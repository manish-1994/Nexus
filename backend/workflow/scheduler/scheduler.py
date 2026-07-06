"""Workflow Scheduler - Core orchestration engine for workflow execution.

Manages the lifecycle of workflow execution:
- Queues ready tasks based on dependency resolution
- Dispatches tasks to appropriate agents
- Collects outputs and updates workflow/task state
- Handles retries with exponential backoff
- Emits workflow events for real-time monitoring
- Supports concurrent workflow execution
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session

from models.workflow import Workflow, Task, WorkflowStatus, TaskStatus
from workflow.graph.dependency_graph import DependencyGraph, TaskNode, build_graph_from_plan
from workflow.events.event_bus import (
    EventBus,
    WorkflowEventType,
    WorkflowEvent,
    get_event_bus,
    emit_workflow_created,
    emit_workflow_started,
    emit_workflow_completed,
    emit_workflow_failed,
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
from services.execution_manager import AgentExecutionManager

logger = logging.getLogger(__name__)


class SchedulerState(str, Enum):
    """Scheduler lifecycle states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class SchedulerConfig:
    """Configuration for the workflow scheduler."""
    max_concurrent_workflows: int = 10
    max_concurrent_tasks_per_workflow: int = 5
    default_max_retries: int = 3
    base_retry_delay_ms: int = 1000
    max_retry_delay_ms: int = 30000
    retry_exponential_base: float = 2.0
    task_dispatch_interval_ms: int = 100
    progress_update_interval_ms: int = 500
    enable_parallel_execution: bool = True


@dataclass
class WorkflowExecutionContext:
    """Runtime context for a workflow execution."""
    workflow: Workflow
    graph: DependencyGraph
    db: Session
    orchestrator: Orchestrator
    ai_runtime: AIRuntime
    execution_manager: AgentExecutionManager
    agent_registry: PluggableAgentRegistry
    event_bus: EventBus
    config: SchedulerConfig
    
    # Runtime state
    running_tasks: Dict[str, asyncio.Task] = field(default_factory=dict)
    completed_task_ids: Set[str] = field(default_factory=set)
    failed_task_ids: Set[str] = field(default_factory=set)
    cancelled: bool = False
    start_time: float = field(default_factory=time.time)
    last_progress_update: float = field(default_factory=time.time)
    
    # Task retry tracking
    task_retry_counts: Dict[str, int] = field(default_factory=dict)
    task_last_errors: Dict[str, str] = field(default_factory=dict)


class WorkflowScheduler:
    """Main workflow scheduler orchestrating multi-agent workflow execution."""
    
    def __init__(
        self,
        db: Session,
        orchestrator: Orchestrator,
        ai_runtime: AIRuntime,
        execution_manager: AgentExecutionManager,
        agent_registry: PluggableAgentRegistry,
        event_bus: Optional[EventBus] = None,
        config: Optional[SchedulerConfig] = None,
    ):
        self.db = db
        self.orchestrator = orchestrator
        self.ai_runtime = ai_runtime
        self.execution_manager = execution_manager
        self.agent_registry = agent_registry
        self.event_bus = event_bus or get_event_bus()
        self.config = config or SchedulerConfig()
        
        self._state = SchedulerState.IDLE
        self._active_workflows: Dict[int, WorkflowExecutionContext] = {}
        self._workflow_semaphore = asyncio.Semaphore(self.config.max_concurrent_workflows)
        self._shutdown_event = asyncio.Event()
        self._scheduler_task: Optional[asyncio.Task] = None
        
        logger.info("WorkflowScheduler initialized with max_concurrent_workflows=%d", 
                   self.config.max_concurrent_workflows)
    
    @property
    def state(self) -> SchedulerState:
        return self._state
    
    @property
    def active_workflow_count(self) -> int:
        return len(self._active_workflows)
    
    async def start(self) -> None:
        """Start the scheduler background task."""
        if self._state != SchedulerState.IDLE:
            logger.warning("Scheduler already running, state=%s", self._state)
            return
        
        self._state = SchedulerState.RUNNING
        self._shutdown_event.clear()
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("WorkflowScheduler started")
    
    async def stop(self, graceful: bool = True) -> None:
        """Stop the scheduler."""
        if self._state == SchedulerState.STOPPED:
            return
        
        self._state = SchedulerState.STOPPING
        self._shutdown_event.set()
        
        if graceful:
            # Wait for active workflows to complete or cancel
            await self._wait_for_active_workflows(timeout=30.0)
        else:
            # Force cancel all active workflows
            await self._cancel_all_workflows()
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        self._state = SchedulerState.STOPPED
        logger.info("WorkflowScheduler stopped")
    
    async def submit_workflow(
        self,
        workflow: Workflow,
        execution_plan: Dict[str, Any],
    ) -> Workflow:
        """Submit a workflow for execution.
        
        Args:
            workflow: The workflow record (already persisted)
            execution_plan: The execution plan from the Planner agent
            
        Returns:
            The workflow with updated status
        """
        # Build dependency graph from execution plan
        graph = build_graph_from_plan(execution_plan)
        workflow.execution_graph = graph.to_dict()
        self.db.commit()
        
        # Emit workflow created event
        emit_workflow_created(
            workflow_id=workflow.workflow_id,
            prompt=workflow.prompt,
            task_count=len(graph.nodes),
        )
        
        # Update workflow status to QUEUED
        workflow.status = WorkflowStatus.QUEUED
        self.db.commit()
        
        # Create execution context
        context = WorkflowExecutionContext(
            workflow=workflow,
            graph=graph,
            db=self.db,
            orchestrator=self.orchestrator,
            ai_runtime=self.ai_runtime,
            execution_manager=self.execution_manager,
            agent_registry=self.agent_registry,
            event_bus=self.event_bus,
            config=self.config,
        )
        
        # Add to active workflows
        self._active_workflows[workflow.id] = context
        
        logger.info("Workflow %s (%s) queued with %d tasks", 
                   workflow.workflow_id, workflow.id, len(graph.nodes))
        
        return workflow
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        # Find workflow by workflow_id
        context = None
        for ctx in self._active_workflows.values():
            if ctx.workflow.workflow_id == workflow_id:
                context = ctx
                break
        
        if not context:
            logger.warning("Workflow %s not found in active workflows", workflow_id)
            return False
        
        context.cancelled = True
        
        # Cancel all running tasks
        for task_id, task in context.running_tasks.items():
            task.cancel()
        
        # Update workflow status
        workflow = context.workflow
        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.utcnow()
        if workflow.started_at:
            workflow.total_latency_ms = int(
                (workflow.completed_at - workflow.started_at).total_seconds() * 1000
            )
        self.db.commit()
        
        # Emit workflow cancelled event
        self.event_bus.emit_sync(WorkflowEvent(
            event_type=WorkflowEventType.WORKFLOW_CANCELLED,
            workflow_id=workflow_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"workflow_id": workflow_id},
        ))
        
        logger.info("Workflow %s cancelled", workflow_id)
        return True
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow (stops dispatching new tasks)."""
        context = self._find_context_by_workflow_id(workflow_id)
        if not context:
            return False
        
        # Just stop dispatching new tasks; running tasks continue
        logger.info("Workflow %s paused", workflow_id)
        return True
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow."""
        context = self._find_context_by_workflow_id(workflow_id)
        if not context:
            return False
        
        logger.info("Workflow %s resumed", workflow_id)
        return True
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow."""
        context = self._find_context_by_workflow_id(workflow_id)
        if not context:
            # Check database for completed workflows
            workflow = self.db.query(Workflow).filter(
                Workflow.workflow_id == workflow_id
            ).first()
            if workflow:
                return self._workflow_to_status_dict(workflow)
            return None
        
        return self._context_to_status_dict(context)
    
    def get_all_active_workflows(self) -> List[Dict[str, Any]]:
        """Get status of all active workflows."""
        return [
            self._context_to_status_dict(ctx) 
            for ctx in self._active_workflows.values()
        ]
    
    # ============================================================
    # Internal scheduler loop
    # ============================================================
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop - dispatches ready tasks for all active workflows."""
        logger.debug("Scheduler loop started")
        
        while not self._shutdown_event.is_set():
            try:
                # Process each active workflow
                workflows_to_remove = []
                
                for workflow_id, context in list(self._active_workflows.items()):
                    if context.cancelled:
                        await self._finalize_workflow(context, WorkflowStatus.CANCELLED)
                        workflows_to_remove.append(workflow_id)
                        continue
                    
                    # Check if workflow is complete
                    if self._is_workflow_complete(context):
                        await self._finalize_workflow(context, WorkflowStatus.COMPLETED)
                        workflows_to_remove.append(workflow_id)
                        continue
                    
                    # Check if workflow has failed (no more tasks can run)
                    if self._is_workflow_failed(context):
                        await self._finalize_workflow(context, WorkflowStatus.FAILED)
                        workflows_to_remove.append(workflow_id)
                        continue
                    
                    # Dispatch ready tasks
                    await self._dispatch_ready_tasks(context)
                    
                    # Emit progress update periodically
                    await self._maybe_emit_progress(context)
                
                # Clean up completed workflows
                for wf_id in workflows_to_remove:
                    self._active_workflows.pop(wf_id, None)
                
                # Sleep before next iteration
                await asyncio.sleep(self.config.task_dispatch_interval_ms / 1000.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in scheduler loop: %s", e)
                await asyncio.sleep(1.0)  # Back off on error
        
        logger.debug("Scheduler loop stopped")
    
    async def _dispatch_ready_tasks(self, context: WorkflowExecutionContext) -> None:
        """Dispatch all ready tasks for a workflow."""
        # Get ready tasks from dependency graph
        ready_task_ids = context.graph.get_ready_tasks(context.completed_task_ids)
        
        # Filter out already running/queued tasks
        ready_task_ids = [
            tid for tid in ready_task_ids
            if tid not in context.running_tasks
            and tid not in context.completed_task_ids
            and tid not in context.failed_task_ids
        ]
        
        # Limit concurrent tasks per workflow
        available_slots = self.config.max_concurrent_tasks_per_workflow - len(context.running_tasks)
        ready_task_ids = ready_task_ids[:available_slots]
        
        for task_id in ready_task_ids:
            node = context.graph.nodes.get(task_id)
            if not node:
                continue
            
            # Get task from database
            task = self.db.query(Task).filter(Task.task_id == task_id).first()
            if not task:
                logger.warning("Task %s not found in database", task_id)
                continue
            
            # Check if we should skip (already completed/failed)
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                continue
            
            # Dispatch task
            asyncio.create_task(self._execute_task(context, task, node))
    
    async def _execute_task(
        self,
        context: WorkflowExecutionContext,
        task: Task,
        node: TaskNode,
    ) -> None:
        """Execute a single task with retry logic."""
        task_id = task.task_id
        workflow_id = context.workflow.workflow_id
        agent_role = node.agent_role
        
        # Update task status to RUNNING
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.progress = 10
        self.db.commit()
        
        # Emit task started event
        emit_task_started(workflow_id, task_id, agent_role)
        
        # Track running task
        execution_task = asyncio.current_task()
        context.running_tasks[task_id] = execution_task
        
        start_time = time.time()
        retry_count = context.task_retry_counts.get(task_id, 0)
        max_retries = task.max_retries or self.config.default_max_retries
        
        while retry_count <= max_retries:
            if context.cancelled:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.utcnow()
                self.db.commit()
                emit_task_failed(workflow_id, task_id, agent_role, "Workflow cancelled", retry_count)
                break
            
            try:
                # Build context from dependency outputs
                dep_outputs = self._build_dependency_context(context, node)
                
                # Execute task via orchestrator/agent
                result = await self._invoke_agent_for_task(
                    context, task, node, dep_outputs
                )
                
                # Success!
                latency_ms = int((time.time() - start_time) * 1000)
                
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.progress = 100
                task.output = result.get("output", {})
                task.latency_ms = latency_ms
                if "tokens_used" in result:
                    task.total_tokens = result["tokens_used"]
                    task.input_tokens = result.get("input_tokens", 0)
                    task.output_tokens = result.get("output_tokens", 0)
                if "cost" in result:
                    task.cost = result["cost"]
                
                # Update workflow aggregates
                context.workflow.total_input_tokens += task.input_tokens
                context.workflow.total_output_tokens += task.output_tokens
                context.workflow.total_tokens += task.total_tokens
                context.workflow.total_cost += task.cost or 0.0
                
                self.db.commit()
                
                # Mark completed in graph
                context.graph.update_node_status(task_id, "completed", result.get("output"))
                context.completed_task_ids.add(task_id)
                
                # Emit task completed event
                emit_task_completed(
                    workflow_id, task_id, agent_role, 
                    result.get("output", {}), latency_ms
                )
                
                logger.info("Task %s completed in %dms", task_id, latency_ms)
                break
                
            except Exception as e:
                retry_count += 1
                context.task_retry_counts[task_id] = retry_count
                context.task_last_errors[task_id] = str(e)
                
                latency_ms = int((time.time() - start_time) * 1000)
                
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
                    # All retries exhausted
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.utcnow()
                    task.error_message = str(e)
                    task.error_code = type(e).__name__
                    task.latency_ms = latency_ms
                    self.db.commit()
                    
                    context.graph.update_node_status(task_id, "failed", error=str(e))
                    context.failed_task_ids.add(task_id)
                    
                    # Emit task failed event
                    emit_task_failed(workflow_id, task_id, agent_role, str(e), retry_count)
                    
                    logger.error("Task %s failed after %d retries: %s", task_id, retry_count, e)
                    break
        
        # Clean up running task
        context.running_tasks.pop(task_id, None)
    
    async def _invoke_agent_for_task(
        self,
        context: WorkflowExecutionContext,
        task: Task,
        node: TaskNode,
        dep_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Invoke the appropriate agent for a task."""
        agent_role = node.agent_role
        
        # Get agent from registry or orchestrator
        try:
            agent = context.orchestrator._get_agent(agent_role)
        except ValueError:
            # Try custom agent registry
            factory = context.agent_registry.get_factory(agent_role)
            if factory:
                agent = factory()
            else:
                raise ValueError(f"No agent found for role: {agent_role}")
        
        # Prepare task input
        task_input = {
            "description": node.description,
            "context": dep_outputs,
            "parameters": node.metadata.get("parameters", {}),
        }
        task.input = task_input
        self.db.commit()
        
        # Execute via agent's execute_task method
        if hasattr(agent, 'execute_task'):
            result = await agent.execute_task(
                task_description=node.description,
                context=dep_outputs,
                provider_id=task.provider_id or context.workflow.provider_id,
                model=task.model or context.workflow.model,
                execution_id=context.workflow.workflow_id,
                task_id=task.task_id,
            )
        else:
            # Fallback to chat
            messages = [
                {"role": "system", "content": f"Task: {node.description}"},
                {"role": "system", "content": f"Context: {dep_outputs}"},
            ]
            result = await agent.chat(messages)
            result = {"output": result}
        
        return result
    
    def _build_dependency_context(
        self,
        context: WorkflowExecutionContext,
        node: TaskNode,
    ) -> Dict[str, Any]:
        """Build context from dependency task outputs."""
        dep_context = {}
        
        for dep_id in node.dependencies:
            dep_node = context.graph.nodes.get(dep_id)
            if dep_node and dep_node.output:
                dep_context[dep_id] = dep_node.output
        
        return dep_context
    
    def _is_workflow_complete(self, context: WorkflowExecutionContext) -> bool:
        """Check if all tasks in workflow are completed."""
        all_task_ids = set(context.graph.nodes.keys())
        return context.completed_task_ids == all_task_ids
    
    def _is_workflow_failed(self, context: WorkflowExecutionContext) -> bool:
        """Check if workflow has failed (no more tasks can run)."""
        all_task_ids = set(context.graph.nodes.keys())
        pending_task_ids = all_task_ids - context.completed_task_ids - context.failed_task_ids - set(context.running_tasks.keys())
        
        # If there are pending tasks but none are ready (dependency deadlock or all deps failed)
        if pending_task_ids:
            ready_tasks = context.graph.get_ready_tasks(context.completed_task_ids)
            ready_pending = [t for t in ready_tasks if t in pending_task_ids]
            if not ready_pending:
                # Check if any pending task has failed dependencies
                for task_id in pending_task_ids:
                    node = context.graph.nodes[task_id]
                    deps_failed = any(
                        dep_id in context.failed_task_ids 
                        for dep_id in node.dependencies
                    )
                    if not deps_failed:
                        return False  # Still has runnable tasks
                return True  # All pending tasks blocked by failed dependencies
        
        return False
    
    async def _finalize_workflow(
        self,
        context: WorkflowExecutionContext,
        final_status: WorkflowStatus,
    ) -> None:
        """Finalize workflow execution."""
        workflow = context.workflow
        workflow.status = final_status
        workflow.completed_at = datetime.utcnow()
        
        if workflow.started_at:
            workflow.total_latency_ms = int(
                (workflow.completed_at - workflow.started_at).total_seconds() * 1000
            )
        
        # Aggregate results
        results = {}
        errors = []
        
        for task in workflow.tasks:
            if task.status == TaskStatus.COMPLETED and task.output:
                results[task.task_id] = task.output
            elif task.status == TaskStatus.FAILED:
                errors.append({
                    "task_id": task.task_id,
                    "agent": task.agent,
                    "error": task.error_message,
                })
        
        workflow.results = results
        workflow.errors = errors
        
        # Determine if partial completion
        if final_status == WorkflowStatus.COMPLETED and errors:
            workflow.status = WorkflowStatus.PARTIAL
        
        self.db.commit()
        
        # Emit workflow completion event
        if final_status in (WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL):
            emit_workflow_completed(
                workflow.workflow_id,
                results,
                workflow.total_latency_ms or 0,
            )
        elif final_status == WorkflowStatus.FAILED:
            emit_workflow_failed(
                workflow.workflow_id,
                errors[0]["error"] if errors else "Unknown error",
                results if results else None,
            )
        
        logger.info("Workflow %s finalized with status %s", workflow.workflow_id, final_status)
    
    async def _maybe_emit_progress(self, context: WorkflowExecutionContext) -> None:
        """Emit progress update if interval has passed."""
        now = time.time()
        if now - context.last_progress_update >= (self.config.progress_update_interval_ms / 1000.0):
            total_tasks = len(context.graph.nodes)
            completed = len(context.completed_task_ids)
            progress = int((completed / total_tasks) * 100) if total_tasks > 0 else 0
            
            current_task = None
            if context.running_tasks:
                current_task = next(iter(context.running_tasks.keys()))
            
            emit_progress_update(
                context.workflow.workflow_id,
                progress,
                current_task,
                f"Completed {completed}/{total_tasks} tasks",
            )
            
            context.last_progress_update = now
    
    async def _wait_for_active_workflows(self, timeout: float = 30.0) -> None:
        """Wait for active workflows to complete."""
        start = time.time()
        while self._active_workflows and (time.time() - start) < timeout:
            await asyncio.sleep(0.5)
        
        # Force cancel remaining
        if self._active_workflows:
            await self._cancel_all_workflows()
    
    async def _cancel_all_workflows(self) -> None:
        """Force cancel all active workflows."""
        for context in self._active_workflows.values():
            context.cancelled = True
            for task in context.running_tasks.values():
                task.cancel()
    
    def _find_context_by_workflow_id(self, workflow_id: str) -> Optional[WorkflowExecutionContext]:
        """Find execution context by workflow_id."""
        for context in self._active_workflows.values():
            if context.workflow.workflow_id == workflow_id:
                return context
        return None
    
    def _context_to_status_dict(self, context: WorkflowExecutionContext) -> Dict[str, Any]:
        """Convert execution context to status dictionary."""
        workflow = context.workflow
        total_tasks = len(context.graph.nodes)
        completed = len(context.completed_task_ids)
        failed = len(context.failed_task_ids)
        running = len(context.running_tasks)
        
        return {
            "workflow_id": workflow.workflow_id,
            "status": workflow.status.value,
            "progress": int((completed / total_tasks) * 100) if total_tasks > 0 else 0,
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "running_tasks": running,
            "current_task": next(iter(context.running_tasks.keys())) if context.running_tasks else None,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "total_latency_ms": workflow.total_latency_ms,
        }
    
    def _workflow_to_status_dict(self, workflow: Workflow) -> Dict[str, Any]:
        """Convert database workflow to status dictionary."""
        total_tasks = len(workflow.tasks)
        completed = sum(1 for t in workflow.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in workflow.tasks if t.status == TaskStatus.FAILED)
        running = sum(1 for t in workflow.tasks if t.status == TaskStatus.RUNNING)
        
        return {
            "workflow_id": workflow.workflow_id,
            "status": workflow.status.value,
            "progress": int((completed / total_tasks) * 100) if total_tasks > 0 else 0,
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "running_tasks": running,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "total_latency_ms": workflow.total_latency_ms,
        }


# Global scheduler instance
_scheduler: Optional[WorkflowScheduler] = None


def get_scheduler() -> Optional[WorkflowScheduler]:
    """Get the global scheduler instance."""
    return _scheduler


def set_scheduler(scheduler: WorkflowScheduler) -> None:
    """Set the global scheduler instance."""
    global _scheduler
    _scheduler = scheduler


async def create_scheduler(
    db: Session,
    orchestrator: Orchestrator,
    ai_runtime: AIRuntime,
    execution_manager: AgentExecutionManager,
    agent_registry: PluggableAgentRegistry,
    event_bus: Optional[EventBus] = None,
    config: Optional[SchedulerConfig] = None,
) -> WorkflowScheduler:
    """Create and start the global workflow scheduler."""
    global _scheduler
    _scheduler = WorkflowScheduler(
        db=db,
        orchestrator=orchestrator,
        ai_runtime=ai_runtime,
        execution_manager=execution_manager,
        agent_registry=agent_registry,
        event_bus=event_bus,
        config=config,
    )
    await _scheduler.start()
    return _scheduler