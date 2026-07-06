"""Workflow Executor - Parallel task execution and agent dispatch.

Handles the actual execution of tasks by dispatching to appropriate agents,
managing parallel execution, collecting outputs, and handling errors.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session

from models.workflow import Workflow, Task, TaskStatus
from workflow.graph.dependency_graph import DependencyGraph, TaskNode
from workflow.events.event_bus import (
    EventBus,
    WorkflowEventType,
    WorkflowEvent,
    get_event_bus,
    emit_task_started,
    emit_task_completed,
    emit_task_failed,
    emit_task_retrying,
)
from agents.orchestration.orchestrator import Orchestrator
from agents.orchestration.agent_registry import PluggableAgentRegistry
from services.ai_runtime import AIRuntime
from services.execution_manager import AgentExecutionManager

logger = logging.getLogger(__name__)


class ExecutionStrategy(str, Enum):
    """Task execution strategy."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    MIXED = "mixed"  # Parallel groups with sequential group ordering


@dataclass
class TaskExecutionResult:
    """Result of a task execution."""
    task_id: str
    agent_role: str
    success: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    retry_count: int = 0
    provider_used: Optional[int] = None
    model_used: Optional[str] = None
    fallback_used: bool = False
    structured_output: Optional[Dict[str, Any]] = None


@dataclass
class ExecutorConfig:
    """Configuration for the workflow executor."""
    max_parallel_tasks: int = 5
    default_max_retries: int = 3
    base_retry_delay_ms: int = 1000
    max_retry_delay_ms: int = 30000
    retry_exponential_base: float = 2.0
    task_timeout_seconds: int = 300
    enable_fallback: bool = True


class WorkflowExecutor:
    """Executes workflow tasks by dispatching to agents.
    
    Supports:
    - Parallel execution of independent tasks
    - Sequential execution for dependent tasks
    - Retry logic with exponential backoff
    - Provider/model fallback on failure
    - Real-time event emission
    """
    
    def __init__(
        self,
        db: Session,
        orchestrator: Orchestrator,
        ai_runtime: AIRuntime,
        execution_manager: AgentExecutionManager,
        agent_registry: PluggableAgentRegistry,
        event_bus: Optional[EventBus] = None,
        config: Optional[ExecutorConfig] = None,
    ):
        self.db = db
        self.orchestrator = orchestrator
        self.ai_runtime = ai_runtime
        self.execution_manager = execution_manager
        self.agent_registry = agent_registry
        self.event_bus = event_bus or get_event_bus()
        self.config = config or ExecutorConfig()
        
        # Semaphore for limiting parallel execution
        self._parallel_semaphore = asyncio.Semaphore(self.config.max_parallel_tasks)
        
        logger.info("WorkflowExecutor initialized with max_parallel_tasks=%d", 
                   self.config.max_parallel_tasks)
    
    async def execute_task(
        self,
        workflow: Workflow,
        task: Task,
        node: TaskNode,
        dependency_outputs: Dict[str, Any],
        cancel_event: Optional[asyncio.Event] = None,
    ) -> TaskExecutionResult:
        """Execute a single task with retry and fallback logic.
        
        Args:
            workflow: Parent workflow
            task: Task database record
            node: Task node from dependency graph
            dependency_outputs: Outputs from completed dependency tasks
            cancel_event: Optional cancellation event
            
        Returns:
            TaskExecutionResult with execution outcome
        """
        task_id = task.task_id
        workflow_id = workflow.workflow_id
        agent_role = node.agent
        
        # Update task status to RUNNING
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.progress = 10
        self.db.commit()
        
        # Emit task started event
        emit_task_started(workflow_id, task_id, agent_role)
        
        start_time = time.time()
        retry_count = task.retry_count or 0
        max_retries = task.max_retries or self.config.default_max_retries
        
        # Get agent for this task
        agent = await self._get_agent(agent_role)
        if not agent:
            error_msg = f"No agent found for role: {agent_role}"
            return await self._handle_task_failure(
                workflow, task, node, agent_role, error_msg, 
                retry_count, start_time
            )
        
        # Prepare task input
        task_input = {
            "description": node.description,
            "context": dependency_outputs,
            "parameters": node.metadata.get("parameters", {}),
        }
        task.input = task_input
        self.db.commit()
        
        # Track provider/model for fallback
        current_provider_id = task.provider_id or workflow.provider_id
        current_model = task.model or workflow.model
        last_error: Optional[Exception] = None
        
        while retry_count <= max_retries:
            # Check for cancellation
            if cancel_event and cancel_event.is_set():
                return await self._handle_task_failure(
                    workflow, task, node, agent_role, "Execution cancelled",
                    retry_count, start_time
                )
            
            try:
                # Execute task via agent
                result = await self._invoke_agent(
                    agent, node, dependency_outputs, 
                    workflow_id, task_id, current_provider_id, current_model
                )
                
                # Success!
                latency_ms = int((time.time() - start_time) * 1000)
                
                return TaskExecutionResult(
                    task_id=task_id,
                    agent_role=agent_role,
                    success=True,
                    output=result.get("output", {}),
                    tokens_used=result.get("tokens_used", 0),
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    cost=result.get("cost", 0.0),
                    latency_ms=latency_ms,
                    retry_count=retry_count,
                    provider_used=current_provider_id,
                    model_used=current_model,
                    structured_output=result if isinstance(result, dict) else None,
                )
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                logger.warning(
                    "Task %s attempt %d/%d failed: %s",
                    task_id, retry_count, max_retries + 1, e
                )
                
                if retry_count <= max_retries:
                    # Emit retrying event
                    emit_task_retrying(workflow_id, task_id, agent_role, retry_count, str(e))
                    
                    # Exponential backoff
                    delay = min(
                        self.config.base_retry_delay_ms * (self.config.retry_exponential_base ** (retry_count - 1)),
                        self.config.max_retry_delay_ms
                    )
                    await asyncio.sleep(delay / 1000.0)
                    
                    # Update task status
                    task.status = TaskStatus.RETRYING
                    task.retry_count = retry_count
                    task.last_error = str(e)
                    self.db.commit()
                    continue
                else:
                    # All retries exhausted - try fallback if enabled
                    if self.config.enable_fallback:
                        fallback_result = await self._try_fallback(
                            workflow, task, node, agent_role, dependency_outputs,
                            workflow_id, task_id, current_provider_id, current_model,
                            last_error, retry_count, start_time
                        )
                        if fallback_result:
                            return fallback_result
                    
                    # Complete failure
                    return await self._handle_task_failure(
                        workflow, task, node, agent_role, str(last_error),
                        retry_count, start_time
                    )
        
        # Should not reach here
        return await self._handle_task_failure(
            workflow, task, node, agent_role, str(last_error) if last_error else "Unknown error",
            retry_count, start_time
        )
    
    async def execute_parallel_group(
        self,
        workflow: Workflow,
        task_nodes: List[TaskNode],
        dependency_outputs: Dict[str, Any],
        cancel_event: Optional[asyncio.Event] = None,
    ) -> List[TaskExecutionResult]:
        """Execute a group of tasks in parallel.
        
        Args:
            workflow: Parent workflow
            task_nodes: List of task nodes to execute in parallel
            dependency_outputs: Outputs from completed dependency tasks
            cancel_event: Optional cancellation event
            
        Returns:
            List of TaskExecutionResult for each task
        """
        # Create tasks for parallel execution
        async def execute_with_semaphore(node: TaskNode) -> TaskExecutionResult:
            async with self._parallel_semaphore:
                task = self.db.query(Task).filter(Task.task_id == node.task_id).first()
                if not task:
                    return TaskExecutionResult(
                        task_id=node.task_id,
                        agent_role=node.agent,
                        success=False,
                        error=f"Task {node.task_id} not found in database",
                    )
                return await self.execute_task(
                    workflow, task, node, dependency_outputs, cancel_event
                )
        
        # Execute all tasks in parallel
        tasks = [execute_with_semaphore(node) for node in task_nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.exception("Parallel task %s raised exception", task_nodes[i].task_id)
                processed_results.append(TaskExecutionResult(
                    task_id=task_nodes[i].task_id,
                    agent_role=task_nodes[i].agent,
                    success=False,
                    error=str(result),
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def execute_workflow_tasks(
        self,
        workflow: Workflow,
        graph: DependencyGraph,
        execution_strategy: ExecutionStrategy = ExecutionStrategy.MIXED,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> Dict[str, TaskExecutionResult]:
        """Execute all tasks in a workflow according to the execution strategy.
        
        Args:
            workflow: Workflow to execute
            graph: Dependency graph with task nodes
            execution_strategy: How to execute tasks (sequential, parallel, mixed)
            cancel_event: Optional cancellation event
            
        Returns:
            Dictionary mapping task_id to TaskExecutionResult
        """
        results: Dict[str, TaskExecutionResult] = {}
        completed_task_ids: Set[str] = set()
        
        if execution_strategy == ExecutionStrategy.SEQUENTIAL:
            # Execute in topological order, one at a time
            topo_order = graph.topological_order()
            for task_id in topo_order:
                if cancel_event and cancel_event.is_set():
                    break
                
                node = graph.nodes[task_id]
                task = self.db.query(Task).filter(Task.task_id == task_id).first()
                if not task:
                    continue
                
                # Build dependency outputs
                dep_outputs = self._build_dependency_outputs(graph, node, results)
                
                result = await self.execute_task(
                    workflow, task, node, dep_outputs, cancel_event
                )
                results[task_id] = result
                
                if result.success:
                    completed_task_ids.add(task_id)
                    node.output = result.output or {}
                    graph.update_node_status(task_id, "completed")
                else:
                    graph.update_node_status(task_id, "failed", error=result.error)
        
        elif execution_strategy == ExecutionStrategy.PARALLEL:
            # Execute all independent tasks in parallel (respecting dependencies)
            # This is complex - we use mixed strategy instead
            return await self.execute_workflow_tasks(
                workflow, graph, ExecutionStrategy.MIXED, cancel_event
            )
        
        else:  # MIXED - parallel groups with sequential group ordering
            parallel_groups = graph.get_parallel_groups()
            
            for group in parallel_groups:
                if cancel_event and cancel_event.is_set():
                    break
                
                # Get nodes for this group
                group_nodes = [graph.nodes[tid] for tid in group if tid in graph.nodes]
                
                # Build dependency outputs from all completed tasks so far
                dep_outputs = {}
                for completed_id in completed_task_ids:
                    completed_node = graph.nodes.get(completed_id)
                    if completed_node and completed_node.output:
                        dep_outputs[completed_id] = completed_node.output
                
                # Execute group in parallel
                group_results = await self.execute_parallel_group(
                    workflow, group_nodes, dep_outputs, cancel_event
                )
                
                # Process results
                for result in group_results:
                    results[result.task_id] = result
                    node = graph.nodes.get(result.task_id)
                    if result.success:
                        completed_task_ids.add(result.task_id)
                        if node:
                            node.output = result.output or {}
                            graph.update_node_status(result.task_id, "completed")
                    else:
                        if node:
                            graph.update_node_status(result.task_id, "failed", error=result.error)
        
        return results
    
    async def _get_agent(self, agent_role: str):
        """Get agent instance for a role."""
        try:
            return self.orchestrator._get_agent(agent_role)
        except ValueError:
            # Try custom agent registry
            factory = self.agent_registry.get_factory(agent_role)
            if factory:
                return factory()
            return None
    
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
    
    async def _try_fallback(
        self,
        workflow: Workflow,
        task: Task,
        node: TaskNode,
        agent_role: str,
        dependency_outputs: Dict[str, Any],
        workflow_id: str,
        task_id: str,
        current_provider_id: Optional[int],
        current_model: Optional[str],
        last_error: Exception,
        retry_count: int,
        start_time: float,
    ) -> Optional[TaskExecutionResult]:
        """Try fallback provider/model on failure."""
        # This would integrate with FallbackPolicy from orchestrator
        # For now, return None to indicate no fallback available
        logger.info("Fallback not implemented for task %s", task_id)
        return None
    
    async def _handle_task_failure(
        self,
        workflow: Workflow,
        task: Task,
        node: TaskNode,
        agent_role: str,
        error: str,
        retry_count: int,
        start_time: float,
    ) -> TaskExecutionResult:
        """Handle task failure - update database and emit events."""
        latency_ms = int((time.time() - start_time) * 1000)
        
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.utcnow()
        task.error_message = error
        task.error_code = "TASK_EXECUTION_FAILED"
        task.latency_ms = latency_ms
        task.retry_count = retry_count
        self.db.commit()
        
        # Emit task failed event
        emit_task_failed(workflow.workflow_id, task.task_id, agent_role, error, retry_count)
        
        return TaskExecutionResult(
            task_id=task.task_id,
            agent_role=agent_role,
            success=False,
            error=error,
            latency_ms=latency_ms,
            retry_count=retry_count,
        )
    
    def _build_dependency_outputs(
        self,
        graph: DependencyGraph,
        node: TaskNode,
        results: Dict[str, TaskExecutionResult],
    ) -> Dict[str, Any]:
        """Build dependency outputs from completed task results."""
        dep_outputs = {}
        
        for dep_id in node.dependencies:
            if dep_id in results and results[dep_id].success:
                dep_outputs[dep_id] = results[dep_id].output
            elif dep_id in graph.nodes:
                dep_node = graph.nodes[dep_id]
                if dep_node.output:
                    dep_outputs[dep_id] = dep_node.output
        
        return dep_outputs


# Global executor instance
_executor: Optional[WorkflowExecutor] = None


def get_executor() -> Optional[WorkflowExecutor]:
    """Get the global executor instance."""
    return _executor


def set_executor(executor: WorkflowExecutor) -> None:
    """Set the global executor instance."""
    global _executor
    _executor = executor


def create_executor(
    db: Session,
    orchestrator: Orchestrator,
    ai_runtime: AIRuntime,
    execution_manager: AgentExecutionManager,
    agent_registry: PluggableAgentRegistry,
    event_bus: Optional[EventBus] = None,
    config: Optional[ExecutorConfig] = None,
) -> WorkflowExecutor:
    """Create the global workflow executor."""
    global _executor
    _executor = WorkflowExecutor(
        db=db,
        orchestrator=orchestrator,
        ai_runtime=ai_runtime,
        execution_manager=execution_manager,
        agent_registry=agent_registry,
        event_bus=event_bus,
        config=config,
    )
    return _executor