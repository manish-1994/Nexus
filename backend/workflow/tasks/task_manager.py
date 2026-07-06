"""Workflow Tasks - Task execution logic, input/output handling, and task lifecycle management.

Provides:
- Task input validation and preparation
- Task output processing and normalization
- Task lifecycle state management
- Task retry and failure handling
- Task result aggregation
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from models.workflow import Workflow, Task, TaskStatus, WorkflowStatus
from workflow.graph.dependency_graph import DependencyGraph, TaskNode
from workflow.events.event_bus import (
    EventBus,
    WorkflowEventType,
    get_event_bus,
    emit_task_queued,
    emit_task_started,
    emit_task_completed,
    emit_task_failed,
    emit_task_retrying,
    emit_progress_update,
)
from agents.orchestration.orchestrator import Orchestrator
from agents.orchestration.agent_registry import PluggableAgentRegistry
from services.ai_runtime import AIRuntime

logger = logging.getLogger(__name__)


class TaskInputValidator(ABC):
    """Abstract base for task input validators."""
    
    @abstractmethod
    def validate(self, input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate task input. Returns (is_valid, error_message)."""
        pass


class DefaultTaskInputValidator(TaskInputValidator):
    """Default task input validator."""
    
    def validate(self, input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        if not isinstance(input_data, dict):
            return False, "Input must be a dictionary"
        
        if "description" not in input_data:
            return False, "Missing required field: description"
        
        if not isinstance(input_data.get("description"), str):
            return False, "Description must be a string"
        
        return True, None


class TaskOutputProcessor(ABC):
    """Abstract base for task output processors."""
    
    @abstractmethod
    def process(self, raw_output: Any, task: Task) -> Dict[str, Any]:
        """Process raw agent output into structured format."""
        pass


class DefaultTaskOutputProcessor(TaskOutputProcessor):
    """Default task output processor."""
    
    def process(self, raw_output: Any, task: Task) -> Dict[str, Any]:
        if isinstance(raw_output, dict):
            return raw_output
        elif isinstance(raw_output, str):
            return {"output": raw_output, "text": raw_output}
        else:
            return {"output": str(raw_output), "raw": raw_output}


@dataclass
class TaskExecutionContext:
    """Context for task execution."""
    workflow: Workflow
    task: Task
    node: TaskNode
    dependency_outputs: Dict[str, Any]
    db: Session
    orchestrator: Orchestrator
    ai_runtime: AIRuntime
    agent_registry: PluggableAgentRegistry
    event_bus: EventBus
    cancel_event: Optional[asyncio.Event] = None
    
    # Execution tracking
    start_time: float = field(default_factory=time.time)
    attempt: int = 0
    max_retries: int = 3


class TaskManager:
    """Manages task lifecycle: creation, execution, completion, failure, retry."""
    
    def __init__(
        self,
        db: Session,
        orchestrator: Orchestrator,
        ai_runtime: AIRuntime,
        agent_registry: PluggableAgentRegistry,
        event_bus: Optional[EventBus] = None,
        input_validator: Optional[TaskInputValidator] = None,
        output_processor: Optional[TaskOutputProcessor] = None,
    ):
        self.db = db
        self.orchestrator = orchestrator
        self.ai_runtime = ai_runtime
        self.agent_registry = agent_registry
        self.event_bus = event_bus or get_event_bus()
        self.input_validator = input_validator or DefaultTaskInputValidator()
        self.output_processor = output_processor or DefaultTaskOutputProcessor()
        
        # Task execution tracking
        self._active_executions: Dict[str, TaskExecutionContext] = {}
        self._execution_lock = asyncio.Lock()
        
        logger.info("TaskManager initialized")
    
    async def create_task(
        self,
        workflow: Workflow,
        task_id: str,
        agent_role: str,
        description: str,
        dependencies: Optional[List[str]] = None,
        input_data: Optional[Dict[str, Any]] = None,
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        priority: int = 50,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """Create a new task in the database."""
        task = Task(
            task_id=task_id,
            workflow_id=workflow.id,
            agent=agent_role,
            description=description,
            dependencies=dependencies or [],
            input=input_data or {},
            provider_id=provider_id or workflow.provider_id,
            model=model or workflow.model,
            max_retries=max_retries,
            status=TaskStatus.PENDING,
            progress=0,
            metadata=metadata or {},
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        logger.debug("Created task %s for workflow %s", task_id, workflow.workflow_id)
        return task
    
    async def create_tasks_from_plan(
        self,
        workflow: Workflow,
        execution_plan: Dict[str, Any],
        graph: DependencyGraph,
    ) -> List[Task]:
        """Create all tasks from an execution plan."""
        tasks = []
        
        for task_id, node in graph.nodes.items():
            task = await self.create_task(
                workflow=workflow,
                task_id=node.task_id,
                agent_role=node.agent,
                description=node.description,
                dependencies=node.dependencies,
                input_data=node.input,
                metadata=node.metadata,
            )
            tasks.append(task)
        
        logger.info("Created %d tasks for workflow %s", len(tasks), workflow.workflow_id)
        return tasks
    
    async def execute_task(
        self,
        context: TaskExecutionContext,
    ) -> Dict[str, Any]:
        """Execute a single task with full lifecycle management."""
        task = context.task
        workflow = context.workflow
        node = context.node
        workflow_id = workflow.workflow_id
        task_id = task.task_id
        agent_role = node.agent
        
        # Track active execution
        async with self._execution_lock:
            self._active_executions[task_id] = context
        
        try:
            # Validate input
            is_valid, error = self.input_validator.validate(context.task.input or {})
            if not is_valid:
                raise ValueError(f"Invalid task input: {error}")
            
            # Update task status to RUNNING
            await self._update_task_status(task, TaskStatus.RUNNING, progress=10)
            
            # Emit task started event
            emit_task_started(workflow_id, task_id, agent_role)
            
            # Get agent
            agent = await self._get_agent(agent_role)
            if not agent:
                raise ValueError(f"No agent found for role: {agent_role}")
            
            # Execute with retry logic
            result = await self._execute_with_retry(context, agent)
            
            # Process output
            processed_output = self.output_processor.process(result, task)
            
            # Update task with success
            latency_ms = int((time.time() - context.start_time) * 1000)
            await self._complete_task(
                task, processed_output, latency_ms, 
                tokens_used=result.get("tokens_used", 0),
                cost=result.get("cost", 0.0),
            )
            
            # Emit task completed event
            emit_task_completed(
                workflow_id, task_id, agent_role,
                processed_output, latency_ms
            )
            
            return processed_output
            
        except Exception as e:
            logger.exception("Task %s failed: %s", task_id, e)
            await self._fail_task(task, str(e), context.attempt)
            
            # Emit task failed event
            emit_task_failed(workflow_id, task_id, agent_role, str(e), context.attempt)
            
            raise
            
        finally:
            async with self._execution_lock:
                self._active_executions.pop(task_id, None)
    
    async def _execute_with_retry(
        self,
        context: TaskExecutionContext,
        agent,
    ) -> Dict[str, Any]:
        """Execute task with retry logic."""
        task = context.task
        node = context.node
        workflow_id = context.workflow.workflow_id
        task_id = task.task_id
        agent_role = node.agent
        
        max_retries = task.max_retries or 3
        current_provider_id = task.provider_id or context.workflow.provider_id
        current_model = task.model or context.workflow.model
        last_error: Optional[Exception] = None
        
        for attempt in range(max_retries + 1):
            context.attempt = attempt
            
            # Check cancellation
            if context.cancel_event and context.cancel_event.is_set():
                raise asyncio.CancelledError("Task execution cancelled")
            
            try:
                # Build context from dependencies
                dep_context = self._build_dependency_context(context)
                
                # Invoke agent
                result = await self._invoke_agent(
                    agent, node, dep_context,
                    workflow_id, task_id,
                    current_provider_id, current_model
                )
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    "Task %s attempt %d/%d failed: %s",
                    task_id, attempt + 1, max_retries + 1, e
                )
                
                if attempt < max_retries:
                    # Emit retrying event
                    emit_task_retrying(workflow_id, task_id, agent_role, attempt + 1, str(e))
                    
                    # Update task status
                    await self._update_task_status(
                        task, TaskStatus.RETRYING, 
                        retry_count=attempt + 1,
                        last_error=str(e)
                    )
                    
                    # Exponential backoff
                    delay = min(1000 * (2 ** attempt), 30000) / 1000.0
                    await asyncio.sleep(delay)
                    continue
                else:
                    # All retries exhausted
                    break
        
        # All retries failed
        raise last_error or Exception("Task failed after all retries")
    
    async def _invoke_agent(
        self,
        agent,
        node: TaskNode,
        dependency_outputs: Dict[str, Any],
        workflow_id: str,
        task_id: str,
        provider_id: Optional[int],
        model: Optional[str],
    ) -> Dict[str, Any]:
        """Invoke agent's execute_task method."""
        if hasattr(agent, 'execute_task'):
            return await agent.execute_task(
                task_description=node.description,
                context=dependency_outputs,
                provider_id=provider_id,
                model=model,
                execution_id=workflow_id,
                task_id=task_id,
            )
        else:
            # Fallback to chat
            messages = [
                {"role": "system", "content": f"Task: {node.description}"},
                {"role": "system", "content": f"Context: {dependency_outputs}"},
            ]
            response = await agent.chat(messages)
            return {"output": response}
    
    def _build_dependency_context(self, context: TaskExecutionContext) -> Dict[str, Any]:
        """Build context from dependency task outputs."""
        dep_context = {}
        
        for dep_id in context.node.dependencies:
            if dep_id in context.dependency_outputs:
                dep_context[dep_id] = context.dependency_outputs[dep_id]
            elif dep_id in context.graph.nodes:
                dep_node = context.graph.nodes[dep_id]
                if dep_node.output:
                    dep_context[dep_id] = dep_node.output
        
        return dep_context
    
    async def _get_agent(self, agent_role: str):
        """Get agent instance for a role."""
        try:
            return self.orchestrator._get_agent(agent_role)
        except ValueError:
            factory = self.agent_registry.get_factory(agent_role)
            if factory:
                return factory()
            return None
    
    async def _update_task_status(
        self,
        task: Task,
        status: TaskStatus,
        progress: Optional[int] = None,
        retry_count: Optional[int] = None,
        last_error: Optional[str] = None,
    ) -> None:
        """Update task status in database."""
        task.status = status
        
        if progress is not None:
            task.progress = progress
        
        if retry_count is not None:
            task.retry_count = retry_count
        
        if last_error is not None:
            task.last_error = last_error
        
        if status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.utcnow()
        
        self.db.commit()
    
    async def _complete_task(
        self,
        task: Task,
        output: Dict[str, Any],
        latency_ms: int,
        tokens_used: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Mark task as completed with results."""
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.progress = 100
        task.output = output
        task.latency_ms = latency_ms
        task.total_tokens = tokens_used
        task.input_tokens = input_tokens
        task.output_tokens = output_tokens
        task.cost = cost
        
        self.db.commit()
        
        # Update node in graph
        # Note: graph update happens in scheduler/executor
    
    async def _fail_task(
        self,
        task: Task,
        error: str,
        retry_count: int,
    ) -> None:
        """Mark task as failed."""
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.utcnow()
        task.error_message = error
        task.error_code = "TASK_EXECUTION_FAILED"
        task.retry_count = retry_count
        task.latency_ms = int((time.time() - task.started_at.timestamp()) * 1000) if task.started_at else 0
        
        self.db.commit()
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.db.query(Task).filter(Task.task_id == task_id).first()
    
    def get_workflow_tasks(self, workflow_id: str) -> List[Task]:
        """Get all tasks for a workflow."""
        workflow = self.db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        if not workflow:
            return []
        return self.db.query(Task).filter(Task.workflow_id == workflow.id).all()
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get current status of a task."""
        task = self.get_task(task_id)
        return task.status if task else None
    
    def get_active_executions(self) -> Dict[str, TaskExecutionContext]:
        """Get currently executing tasks."""
        return dict(self._active_executions)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        async with self._execution_lock:
            context = self._active_executions.get(task_id)
            if context and context.cancel_event:
                context.cancel_event.set()
                return True
        return False
    
    async def retry_task(self, task_id: str) -> bool:
        """Retry a failed task."""
        task = self.get_task(task_id)
        if not task or task.status != TaskStatus.FAILED:
            return False
        
        # Reset task for retry
        task.status = TaskStatus.PENDING
        task.retry_count = 0
        task.last_error = None
        task.error_message = None
        task.error_code = None
        task.started_at = None
        task.completed_at = None
        task.progress = 0
        
        self.db.commit()
        return True


class TaskResultAggregator:
    """Aggregates task results into workflow-level results."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def aggregate_workflow_results(self, workflow: Workflow) -> Dict[str, Any]:
        """Aggregate all task results for a workflow."""
        results = {}
        errors = []
        total_tokens = 0
        total_cost = 0.0
        
        for task in workflow.tasks:
            if task.status == TaskStatus.COMPLETED and task.output:
                results[task.task_id] = task.output
                total_tokens += task.total_tokens or 0
                total_cost += task.cost or 0.0
            elif task.status == TaskStatus.FAILED:
                errors.append({
                    "task_id": task.task_id,
                    "agent": task.agent,
                    "error": task.error_message,
                    "error_code": task.error_code,
                })
        
        # Update workflow aggregates
        workflow.results = results
        workflow.errors = errors
        workflow.total_tokens = total_tokens
        workflow.total_cost = total_cost
        
        self.db.commit()
        
        return {
            "results": results,
            "errors": errors,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "completed_tasks": len([t for t in workflow.tasks if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in workflow.tasks if t.status == TaskStatus.FAILED]),
            "total_tasks": len(workflow.tasks),
        }
    
    def merge_results(
        self,
        results: Dict[str, Any],
        strategy: str = "merge",
    ) -> Dict[str, Any]:
        """Merge multiple task results into a single result.
        
        Strategies:
        - merge: Deep merge all results
        - concat: Concatenate text outputs
        - latest: Use latest task result
        - first: Use first task result
        """
        if not results:
            return {}
        
        if strategy == "latest":
            # Return the last result
            last_key = list(results.keys())[-1]
            return results[last_key]
        
        elif strategy == "first":
            first_key = list(results.keys())[0]
            return results[first_key]
        
        elif strategy == "concat":
            # Concatenate text outputs
            texts = []
            for task_id, result in results.items():
                if isinstance(result, dict):
                    if "text" in result:
                        texts.append(result["text"])
                    elif "output" in result:
                        texts.append(str(result["output"]))
                else:
                    texts.append(str(result))
            return {"merged_output": "\n\n".join(texts)}
        
        else:  # merge
            merged = {}
            for task_id, result in results.items():
                if isinstance(result, dict):
                    merged[task_id] = result
                else:
                    merged[task_id] = {"output": result}
            return merged


# Global task manager instance
_task_manager: Optional[TaskManager] = None
_result_aggregator: Optional[TaskResultAggregator] = None


def get_task_manager() -> Optional[TaskManager]:
    """Get the global task manager instance."""
    return _task_manager


def set_task_manager(manager: TaskManager) -> None:
    """Set the global task manager instance."""
    global _task_manager
    _task_manager = manager


def create_task_manager(
    db: Session,
    orchestrator: Orchestrator,
    ai_runtime: AIRuntime,
    agent_registry: PluggableAgentRegistry,
    event_bus: Optional[EventBus] = None,
    input_validator: Optional[TaskInputValidator] = None,
    output_processor: Optional[TaskOutputProcessor] = None,
) -> TaskManager:
    """Create the global task manager."""
    global _task_manager
    _task_manager = TaskManager(
        db=db,
        orchestrator=orchestrator,
        ai_runtime=ai_runtime,
        agent_registry=agent_registry,
        event_bus=event_bus,
        input_validator=input_validator,
        output_processor=output_processor,
    )
    return _task_manager


def get_result_aggregator() -> Optional[TaskResultAggregator]:
    """Get the global result aggregator instance."""
    return _result_aggregator


def set_result_aggregator(aggregator: TaskResultAggregator) -> None:
    """Set the global result aggregator instance."""
    global _result_aggregator
    _result_aggregator = aggregator


def create_result_aggregator(db: Session) -> TaskResultAggregator:
    """Create the global result aggregator."""
    global _result_aggregator
    _result_aggregator = TaskResultAggregator(db=db)
    return _result_aggregator