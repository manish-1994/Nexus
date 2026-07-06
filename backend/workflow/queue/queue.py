"""Workflow Queue - Task queuing with priority and concurrency control.

Manages task queues for workflow execution with:
- Priority-based task ordering
- Concurrency control per workflow and globally
- Task scheduling and dispatch coordination
- Queue persistence for resumability
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import heapq

from sqlalchemy.orm import Session

from models.workflow import Workflow, Task, TaskStatus, WorkflowStatus
from workflow.graph.dependency_graph import DependencyGraph, TaskNode

logger = logging.getLogger(__name__)


class TaskPriority(int, Enum):
    """Task priority levels (lower = higher priority)."""
    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 100
    BACKGROUND = 200


@dataclass(order=True)
class QueuedTask:
    """A task in the execution queue with priority."""
    priority: int
    task_id: str = field(compare=False)
    workflow_id: str = field(compare=False)
    agent_role: str = field(compare=False)
    enqueued_at: float = field(compare=False, default_factory=time.time)
    dependencies: List[str] = field(compare=False, default_factory=list)
    metadata: Dict[str, Any] = field(compare=False, default_factory=dict)


@dataclass
class QueueConfig:
    """Configuration for the workflow queue."""
    max_global_concurrent_tasks: int = 20
    max_workflow_concurrent_tasks: int = 5
    default_priority: TaskPriority = TaskPriority.NORMAL
    enable_priority_boost: bool = True
    priority_boost_interval_seconds: int = 60
    max_queue_size_per_workflow: int = 1000
    task_timeout_seconds: int = 300


class WorkflowQueue:
    """Task queue manager for workflow execution.
    
    Features:
    - Priority-based task ordering (heap queue)
    - Per-workflow and global concurrency limits
    - Dependency-aware task scheduling
    - Task timeout and retry handling
    - Queue persistence for crash recovery
    """
    
    def __init__(
        self,
        db: Session,
        config: Optional[QueueConfig] = None,
    ):
        self.db = db
        self.config = config or QueueConfig()
        
        # Global task queue (priority heap)
        self._global_queue: List[QueuedTask] = []
        self._queue_lock = asyncio.Lock()
        
        # Per-workflow queues
        self._workflow_queues: Dict[str, List[QueuedTask]] = defaultdict(list)
        
        # Concurrency control
        self._global_semaphore = asyncio.Semaphore(self.config.max_global_concurrent_tasks)
        self._workflow_semaphores: Dict[str, asyncio.Semaphore] = {}
        
        # Running tasks tracking
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._running_task_info: Dict[str, Dict[str, Any]] = {}
        
        # Task state tracking
        self._task_states: Dict[str, TaskStatus] = {}
        self._completed_tasks: Set[str] = set()
        self._failed_tasks: Set[str] = {}
        
        # Workflow tracking
        self._active_workflows: Set[str] = set()
        self._workflow_task_counts: Dict[str, int] = defaultdict(int)
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._priority_boost_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logger.info("WorkflowQueue initialized with max_global_concurrent=%d, max_workflow_concurrent=%d",
                   self.config.max_global_concurrent_tasks, self.config.max_workflow_concurrent_tasks)
    
    async def start(self) -> None:
        """Start background queue management tasks."""
        self._shutdown_event.clear()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        if self.config.enable_priority_boost:
            self._priority_boost_task = asyncio.create_task(self._priority_boost_loop())
        logger.info("WorkflowQueue started")
    
    async def stop(self) -> None:
        """Stop the queue and background tasks."""
        self._shutdown_event.set()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._priority_boost_task:
            self._priority_boost_task.cancel()
            try:
                await self._priority_boost_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all running tasks
        for task in self._running_tasks.values():
            task.cancel()
        
        logger.info("WorkflowQueue stopped")
    
    def enqueue_task(
        self,
        task_id: str,
        workflow_id: str,
        agent_role: str,
        priority: Optional[TaskPriority] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a task to the execution queue.
        
        Args:
            task_id: Unique task identifier
            workflow_id: Parent workflow identifier
            agent_role: Agent role to execute this task
            priority: Task priority (default: NORMAL)
            dependencies: List of task_ids this task depends on
            metadata: Additional task metadata
            
        Returns:
            True if enqueued successfully, False if queue full
        """
        # Check workflow queue size limit
        if len(self._workflow_queues[workflow_id]) >= self.config.max_queue_size_per_workflow:
            logger.warning("Workflow %s queue full, rejecting task %s", workflow_id, task_id)
            return False
        
        priority = priority or self.config.default_priority
        
        queued_task = QueuedTask(
            priority=priority.value,
            task_id=task_id,
            workflow_id=workflow_id,
            agent_role=agent_role,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        
        # Add to global queue (heap)
        heapq.heappush(self._global_queue, queued_task)
        
        # Add to workflow queue
        self._workflow_queues[workflow_id].append(queued_task)
        
        # Track workflow
        self._active_workflows.add(workflow_id)
        self._workflow_task_counts[workflow_id] += 1
        
        # Initialize task state
        self._task_states[task_id] = TaskStatus.QUEUED
        
        logger.debug("Enqueued task %s for workflow %s with priority %s", 
                    task_id, workflow_id, priority.name)
        return True
    
    def enqueue_tasks_batch(
        self,
        tasks: List[Dict[str, Any]],
    ) -> int:
        """Enqueue multiple tasks at once.
        
        Args:
            tasks: List of task dictionaries with keys:
                task_id, workflow_id, agent_role, priority, dependencies, metadata
                
        Returns:
            Number of tasks successfully enqueued
        """
        count = 0
        for task_data in tasks:
            if self.enqueue_task(**task_data):
                count += 1
        return count
    
    async def dequeue_task(self, workflow_id: Optional[str] = None) -> Optional[QueuedTask]:
        """Dequeue the next ready task.
        
        Args:
            workflow_id: Optional workflow to dequeue from (None = any workflow)
            
        Returns:
            Next ready QueuedTask or None if no ready tasks
        """
        async with self._queue_lock:
            if workflow_id:
                # Dequeue from specific workflow
                return await self._dequeue_from_workflow(workflow_id)
            else:
                # Dequeue from global queue (highest priority ready task)
                return await self._dequeue_global()
    
    async def _dequeue_global(self) -> Optional[QueuedTask]:
        """Dequeue highest priority ready task from global queue."""
        # Find first task whose dependencies are met
        ready_tasks = []
        remaining = []
        
        while self._global_queue:
            task = heapq.heappop(self._global_queue)
            if self._are_dependencies_met(task):
                ready_tasks.append(task)
                break
            else:
                remaining.append(task)
        
        # Put back non-ready tasks
        for task in remaining:
            heapq.heappush(self._global_queue, task)
        
        if ready_tasks:
            task = ready_tasks[0]
            # Remove from workflow queue
            self._remove_from_workflow_queue(task.workflow_id, task.task_id)
            self._task_states[task.task_id] = TaskStatus.RUNNING
            return task
        
        return None
    
    async def _dequeue_from_workflow(self, workflow_id: str) -> Optional[QueuedTask]:
        """Dequeue next ready task from specific workflow."""
        workflow_queue = self._workflow_queues.get(workflow_id, [])
        
        for i, task in enumerate(workflow_queue):
            if self._are_dependencies_met(task):
                # Remove from workflow queue
                workflow_queue.pop(i)
                # Also remove from global queue (mark as removed)
                self._task_states[task.task_id] = TaskStatus.RUNNING
                return task
        
        return None
    
    def _are_dependencies_met(self, task: QueuedTask) -> bool:
        """Check if all task dependencies are completed."""
        for dep_id in task.dependencies:
            if dep_id not in self._completed_tasks:
                return False
        return True
    
    def _remove_from_workflow_queue(self, workflow_id: str, task_id: str) -> None:
        """Remove a task from workflow queue."""
        queue = self._workflow_queues.get(workflow_id, [])
        for i, task in enumerate(queue):
            if task.task_id == task_id:
                queue.pop(i)
                break
    
    async def acquire_execution_slot(self, workflow_id: str) -> asyncio.Semaphore:
        """Acquire execution slot for a workflow (global + workflow semaphore)."""
        # Get or create workflow semaphore
        if workflow_id not in self._workflow_semaphores:
            self._workflow_semaphores[workflow_id] = asyncio.Semaphore(
                self.config.max_workflow_concurrent_tasks
            )
        
        workflow_sem = self._workflow_semaphores[workflow_id]
        
        # Acquire both semaphores
        await self._global_semaphore.acquire()
        await workflow_sem.acquire()
        
        return workflow_sem
    
    def release_execution_slot(self, workflow_id: str, workflow_sem: asyncio.Semaphore) -> None:
        """Release execution slot."""
        self._global_semaphore.release()
        workflow_sem.release()
    
    def mark_task_started(self, task_id: str, asyncio_task: asyncio.Task) -> None:
        """Mark a task as running."""
        self._running_tasks[task_id] = asyncio_task
        self._running_task_info[task_id] = {
            "started_at": time.time(),
            "workflow_id": self._get_workflow_id_for_task(task_id),
        }
        self._task_states[task_id] = TaskStatus.RUNNING
    
    def mark_task_completed(self, task_id: str, success: bool = True) -> None:
        """Mark a task as completed."""
        self._running_tasks.pop(task_id, None)
        self._running_task_info.pop(task_id, None)
        
        if success:
            self._completed_tasks.add(task_id)
            self._task_states[task_id] = TaskStatus.COMPLETED
        else:
            self._failed_tasks.add(task_id)
            self._task_states[task_id] = TaskStatus.FAILED
        
        # Update workflow task count
        workflow_id = self._get_workflow_id_for_task(task_id)
        if workflow_id:
            self._workflow_task_counts[workflow_id] -= 1
            if self._workflow_task_counts[workflow_id] <= 0:
                self._active_workflows.discard(workflow_id)
                self._workflow_semaphores.pop(workflow_id, None)
    
    def _get_workflow_id_for_task(self, task_id: str) -> Optional[str]:
        """Get workflow ID for a task."""
        for info in self._running_task_info.values():
            if info.get("task_id") == task_id:
                return info.get("workflow_id")
        # Check queued tasks
        for task in self._global_queue:
            if task.task_id == task_id:
                return task.workflow_id
        return None
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get current status of a task."""
        return self._task_states.get(task_id)
    
    def get_workflow_queue_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get queue status for a workflow."""
        queue = self._workflow_queues.get(workflow_id, [])
        running_count = sum(
            1 for info in self._running_task_info.values()
            if info.get("workflow_id") == workflow_id
        )
        
        return {
            "workflow_id": workflow_id,
            "queued_tasks": len(queue),
            "running_tasks": running_count,
            "completed_tasks": sum(
                1 for t in self._completed_tasks 
                if self._get_workflow_id_for_task(t) == workflow_id
            ),
            "failed_tasks": sum(
                1 for t in self._failed_tasks 
                if self._get_workflow_id_for_task(t) == workflow_id
            ),
            "total_tasks": self._workflow_task_counts.get(workflow_id, 0),
        }
    
    def get_global_queue_status(self) -> Dict[str, Any]:
        """Get global queue status."""
        return {
            "global_queued_tasks": len(self._global_queue),
            "global_running_tasks": len(self._running_tasks),
            "global_completed_tasks": len(self._completed_tasks),
            "global_failed_tasks": len(self._failed_tasks),
            "active_workflows": len(self._active_workflows),
            "global_semaphore_available": self._global_semaphore._value,
        }
    
    def requeue_task(self, task_id: str, priority: Optional[TaskPriority] = None) -> bool:
        """Requeue a failed task for retry."""
        # Find task in failed tasks
        if task_id not in self._failed_tasks:
            return False
        
        self._failed_tasks.discard(task_id)
        
        # Get task info from database
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return False
        
        # Requeue with same or new priority
        requeue_priority = priority or TaskPriority.HIGH  # Boost priority for retries
        
        return self.enqueue_task(
            task_id=task.task_id,
            workflow_id=task.workflow.workflow_id if task.workflow else "",
            agent_role=task.agent,
            priority=requeue_priority,
            dependencies=task.dependencies or [],
        )
    
    def cancel_workflow_tasks(self, workflow_id: str) -> int:
        """Cancel all queued and running tasks for a workflow."""
        cancelled = 0
        
        # Cancel queued tasks
        queue = self._workflow_queues.get(workflow_id, [])
        for task in queue:
            self._task_states[task.task_id] = TaskStatus.CANCELLED
            cancelled += 1
        self._workflow_queues[workflow_id] = []
        
        # Cancel running tasks
        for task_id, asyncio_task in list(self._running_tasks.items()):
            info = self._running_task_info.get(task_id, {})
            if info.get("workflow_id") == workflow_id:
                asyncio_task.cancel()
                self._task_states[task_id] = TaskStatus.CANCELLED
                cancelled += 1
        
        self._active_workflows.discard(workflow_id)
        self._workflow_task_counts[workflow_id] = 0
        
        logger.info("Cancelled %d tasks for workflow %s", cancelled, workflow_id)
        return cancelled
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up stale tasks."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                now = time.time()
                stale_tasks = []
                
                for task_id, info in self._running_task_info.items():
                    started_at = info.get("started_at", 0)
                    if now - started_at > self.config.task_timeout_seconds:
                        stale_tasks.append(task_id)
                
                for task_id in stale_tasks:
                    logger.warning("Task %s timed out, marking as failed", task_id)
                    asyncio_task = self._running_tasks.pop(task_id, None)
                    if asyncio_task:
                        asyncio_task.cancel()
                    self.mark_task_completed(task_id, success=False)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in queue cleanup loop: %s", e)
    
    async def _priority_boost_loop(self) -> None:
        """Background task to boost priority of long-waiting tasks."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.priority_boost_interval_seconds)
                
                async with self._queue_lock:
                    now = time.time()
                    boosted = 0
                    
                    # Rebuild global queue with boosted priorities
                    new_queue = []
                    for task in self._global_queue:
                        wait_time = now - task.enqueued_at
                        if wait_time > self.config.priority_boost_interval_seconds * 2:
                            # Boost priority (lower value = higher priority)
                            new_priority = max(TaskPriority.CRITICAL.value, task.priority - 10)
                            if new_priority != task.priority:
                                task.priority = new_priority
                                boosted += 1
                        heapq.heappush(new_queue, task)
                    
                    self._global_queue = new_queue
                    
                    if boosted > 0:
                        logger.debug("Boosted priority for %d tasks", boosted)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in priority boost loop: %s", e)
    
    def persist_queue_state(self) -> Dict[str, Any]:
        """Persist queue state for crash recovery."""
        return {
            "global_queue": [
                {
                    "task_id": t.task_id,
                    "workflow_id": t.workflow_id,
                    "agent_role": t.agent_role,
                    "priority": t.priority,
                    "dependencies": t.dependencies,
                    "metadata": t.metadata,
                    "enqueued_at": t.enqueued_at,
                }
                for t in self._global_queue
            ],
            "workflow_queues": {
                wf_id: [
                    {
                        "task_id": t.task_id,
                        "workflow_id": t.workflow_id,
                        "agent_role": t.agent_role,
                        "priority": t.priority,
                        "dependencies": t.dependencies,
                        "metadata": t.metadata,
                        "enqueued_at": t.enqueued_at,
                    }
                    for t in queue
                ]
                for wf_id, queue in self._workflow_queues.items()
            },
            "task_states": {k: v.value for k, v in self._task_states.items()},
            "completed_tasks": list(self._completed_tasks),
            "failed_tasks": list(self._failed_tasks),
            "active_workflows": list(self._active_workflows),
            "workflow_task_counts": dict(self._workflow_task_counts),
        }
    
    def restore_queue_state(self, state: Dict[str, Any]) -> None:
        """Restore queue state from persistence."""
        # Restore global queue
        self._global_queue = []
        for task_data in state.get("global_queue", []):
            task = QueuedTask(
                priority=task_data["priority"],
                task_id=task_data["task_id"],
                workflow_id=task_data["workflow_id"],
                agent_role=task_data["agent_role"],
                enqueued_at=task_data["enqueued_at"],
                dependencies=task_data["dependencies"],
                metadata=task_data["metadata"],
            )
            heapq.heappush(self._global_queue, task)
        
        # Restore workflow queues
        self._workflow_queues = defaultdict(list)
        for wf_id, queue_data in state.get("workflow_queues", {}).items():
            for task_data in queue_data:
                task = QueuedTask(
                    priority=task_data["priority"],
                    task_id=task_data["task_id"],
                    workflow_id=task_data["workflow_id"],
                    agent_role=task_data["agent_role"],
                    enqueued_at=task_data["enqueued_at"],
                    dependencies=task_data["dependencies"],
                    metadata=task_data["metadata"],
                )
                self._workflow_queues[wf_id].append(task)
        
        # Restore task states
        self._task_states = {
            k: TaskStatus(v) for k, v in state.get("task_states", {}).items()
        }
        self._completed_tasks = set(state.get("completed_tasks", []))
        self._failed_tasks = set(state.get("failed_tasks", []))
        self._active_workflows = set(state.get("active_workflows", []))
        self._workflow_task_counts = defaultdict(int, state.get("workflow_task_counts", {}))
        
        logger.info("Restored queue state: %d global tasks, %d workflows", 
                   len(self._global_queue), len(self._active_workflows))


# Global queue instance
_queue: Optional[WorkflowQueue] = None


def get_queue() -> Optional[WorkflowQueue]:
    """Get the global queue instance."""
    return _queue


def set_queue(queue: WorkflowQueue) -> None:
    """Set the global queue instance."""
    global _queue
    _queue = queue


def create_queue(
    db: Session,
    config: Optional[QueueConfig] = None,
) -> WorkflowQueue:
    """Create the global workflow queue."""
    global _queue
    _queue = WorkflowQueue(db=db, config=config)
    return _queue