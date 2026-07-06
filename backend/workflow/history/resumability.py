"""Workflow History - Persistence and resumability for workflow execution.

Provides:
- Workflow state persistence for crash recovery
- Checkpoint/resume functionality
- Execution replay capability
- State serialization/deserialization
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship, Session

from models.base import BaseModel
from models.workflow import Workflow, Task, WorkflowStatus, TaskStatus
from workflow.graph.dependency_graph import DependencyGraph
from workflow.queue.queue import WorkflowQueue, QueuedTask, TaskPriority
from workflow.scheduler.scheduler import WorkflowScheduler, WorkflowExecutionContext

logger = logging.getLogger(__name__)


class CheckpointType(str, Enum):
    """Types of checkpoints."""
    PERIODIC = "periodic"      # Regular interval checkpoint
    TASK_COMPLETE = "task_complete"  # After each task completion
    WORKFLOW_COMPLETE = "workflow_complete"  # At workflow end
    MANUAL = "manual"          # User-triggered


@dataclass
class WorkflowCheckpoint:
    """A checkpoint of workflow execution state."""
    workflow_id: str
    checkpoint_type: CheckpointType
    timestamp: datetime
    
    # Workflow state
    workflow_status: WorkflowStatus
    workflow_results: Dict[str, Any]
    workflow_errors: List[Dict[str, Any]]
    workflow_metadata: Dict[str, Any]
    
    # Task states
    task_states: Dict[str, Dict[str, Any]]  # task_id -> {status, output, error, progress, etc.}
    
    # Graph state
    graph_state: Dict[str, Any]  # Serialized DependencyGraph
    
    # Queue state
    queue_state: Dict[str, Any]  # Serialized WorkflowQueue state
    
    # Scheduler context
    scheduler_context: Dict[str, Any]
    
    # Metrics
    completed_tasks: int
    failed_tasks: int
    total_tasks: int
    total_latency_ms: int


class WorkflowCheckpointModel(BaseModel):
    """Persistent storage for workflow checkpoints."""
    
    __tablename__ = "workflow_checkpoints"
    
    # Associated workflow
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)
    
    # Checkpoint info
    checkpoint_type = Column(String(50), nullable=False, index=True)
    checkpoint_number = Column(Integer, default=0)
    
    # Serialized state
    state_data = Column(JSON, nullable=False)
    
    # Metrics
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    total_tasks = Column(Integer, default=0)
    total_latency_ms = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    workflow = relationship("Workflow", foreign_keys=[workflow_id])
    
    # Indexes
    __table_args__ = (
        Index('ix_workflow_checkpoints_workflow_created', 'workflow_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowCheckpoint(id={self.id}, workflow_id={self.workflow_id}, type='{self.checkpoint_type}')>"


class WorkflowResumabilityManager:
    """Manages workflow persistence and resumability."""
    
    def __init__(
        self,
        db: Session,
        scheduler: Optional[WorkflowScheduler] = None,
        queue: Optional[WorkflowQueue] = None,
        checkpoint_interval_tasks: int = 5,
        max_checkpoints_per_workflow: int = 10,
    ):
        self.db = db
        self.scheduler = scheduler
        self.queue = queue
        self.checkpoint_interval_tasks = checkpoint_interval_tasks
        self.max_checkpoints_per_workflow = max_checkpoints_per_workflow
        
        # Track completed tasks since last checkpoint
        self._tasks_since_checkpoint: Dict[str, int] = {}
        
        logger.info("WorkflowResumabilityManager initialized")
    
    async def create_checkpoint(
        self,
        workflow_id: str,
        checkpoint_type: CheckpointType = CheckpointType.PERIODIC,
    ) -> Optional[WorkflowCheckpointModel]:
        """Create a checkpoint of the current workflow state."""
        # Get workflow
        workflow = self.db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        if not workflow:
            logger.warning("Workflow %s not found for checkpoint", workflow_id)
            return None
        
        # Get scheduler context
        scheduler_context = {}
        if self.scheduler:
            context = self.scheduler._active_workflows.get(workflow.id)
            if context:
                scheduler_context = {
                    "completed_task_ids": list(context.completed_task_ids),
                    "failed_task_ids": list(context.failed_task_ids),
                    "running_task_ids": list(context.running_tasks.keys()),
                    "start_time": context.start_time,
                }
        
        # Get queue state
        queue_state = {}
        if self.queue:
            queue_state = self.queue.persist_queue_state()
        
        # Get graph state
        graph_state = {}
        if self.scheduler:
            context = self.scheduler._active_workflows.get(workflow.id)
            if context and context.graph:
                graph_state = context.graph.to_dict()
        
        # Build task states
        task_states = {}
        for task in workflow.tasks:
            task_states[task.task_id] = {
                "status": task.status.value,
                "output": task.output,
                "error": task.error_message,
                "progress": task.progress,
                "retry_count": task.retry_count,
                "latency_ms": task.latency_ms,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }
        
        # Create checkpoint
        checkpoint = WorkflowCheckpoint(
            workflow_id=workflow_id,
            checkpoint_type=checkpoint_type,
            timestamp=datetime.utcnow(),
            workflow_status=workflow.status,
            workflow_results=workflow.results or {},
            workflow_errors=workflow.errors or [],
            workflow_metadata=workflow.workflow_metadata or {},
            task_states=task_states,
            graph_state=graph_state,
            queue_state=queue_state,
            scheduler_context=scheduler_context,
            completed_tasks=sum(1 for t in workflow.tasks if t.status == TaskStatus.COMPLETED),
            failed_tasks=sum(1 for t in workflow.tasks if t.status == TaskStatus.FAILED),
            total_tasks=len(workflow.tasks),
            total_latency_ms=workflow.total_latency_ms or 0,
        )
        
        # Persist
        checkpoint_model = WorkflowCheckpointModel(
            workflow_id=workflow.id,
            checkpoint_type=checkpoint_type.value,
            state_data=self._serialize_checkpoint(checkpoint),
            completed_tasks=checkpoint.completed_tasks,
            failed_tasks=checkpoint.failed_tasks,
            total_tasks=checkpoint.total_tasks,
            total_latency_ms=checkpoint.total_latency_ms,
        )
        
        self.db.add(checkpoint_model)
        self.db.commit()
        
        # Cleanup old checkpoints
        await self._cleanup_old_checkpoints(workflow.id)
        
        logger.info("Created %s checkpoint for workflow %s", checkpoint_type.value, workflow_id)
        return checkpoint_model
    
    def _serialize_checkpoint(self, checkpoint: WorkflowCheckpoint) -> Dict[str, Any]:
        """Serialize checkpoint to JSON-compatible dict."""
        return {
            "workflow_id": checkpoint.workflow_id,
            "checkpoint_type": checkpoint.checkpoint_type.value,
            "timestamp": checkpoint.timestamp.isoformat(),
            "workflow_status": checkpoint.workflow_status.value,
            "workflow_results": checkpoint.workflow_results,
            "workflow_errors": checkpoint.workflow_errors,
            "workflow_metadata": checkpoint.workflow_metadata,
            "task_states": checkpoint.task_states,
            "graph_state": checkpoint.graph_state,
            "queue_state": checkpoint.queue_state,
            "scheduler_context": checkpoint.scheduler_context,
            "completed_tasks": checkpoint.completed_tasks,
            "failed_tasks": checkpoint.failed_tasks,
            "total_tasks": checkpoint.total_tasks,
            "total_latency_ms": checkpoint.total_latency_ms,
        }
    
    def _deserialize_checkpoint(self, data: Dict[str, Any]) -> WorkflowCheckpoint:
        """Deserialize checkpoint from JSON."""
        return WorkflowCheckpoint(
            workflow_id=data["workflow_id"],
            checkpoint_type=CheckpointType(data["checkpoint_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            workflow_status=WorkflowStatus(data["workflow_status"]),
            workflow_results=data["workflow_results"],
            workflow_errors=data["workflow_errors"],
            workflow_metadata=data["workflow_metadata"],
            task_states=data["task_states"],
            graph_state=data["graph_state"],
            queue_state=data["queue_state"],
            scheduler_context=data["scheduler_context"],
            completed_tasks=data["completed_tasks"],
            failed_tasks=data["failed_tasks"],
            total_tasks=data["total_tasks"],
            total_latency_ms=data["total_latency_ms"],
        )
    
    async def _cleanup_old_checkpoints(self, workflow_db_id: int) -> None:
        """Remove old checkpoints beyond max limit."""
        checkpoints = self.db.query(WorkflowCheckpointModel).filter(
            WorkflowCheckpointModel.workflow_id == workflow_db_id
        ).order_by(WorkflowCheckpointModel.created_at.desc()).all()
        
        if len(checkpoints) > self.max_checkpoints_per_workflow:
            for old_checkpoint in checkpoints[self.max_checkpoints_per_workflow:]:
                self.db.delete(old_checkpoint)
            self.db.commit()
    
    async def restore_from_checkpoint(
        self,
        workflow_id: str,
        checkpoint_id: Optional[int] = None,
    ) -> bool:
        """Restore workflow state from a checkpoint."""
        workflow = self.db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        if not workflow:
            return False
        
        # Get checkpoint
        query = self.db.query(WorkflowCheckpointModel).filter(
            WorkflowCheckpointModel.workflow_id == workflow.id
        )
        
        if checkpoint_id:
            checkpoint_model = query.filter(WorkflowCheckpointModel.id == checkpoint_id).first()
        else:
            # Get latest checkpoint
            checkpoint_model = query.order_by(WorkflowCheckpointModel.created_at.desc()).first()
        
        if not checkpoint_model:
            logger.warning("No checkpoint found for workflow %s", workflow_id)
            return False
        
        checkpoint = self._deserialize_checkpoint(checkpoint_model.state_data)
        
        # Restore workflow state
        workflow.status = checkpoint.workflow_status
        workflow.results = checkpoint.workflow_results
        workflow.errors = checkpoint.workflow_errors
        workflow.workflow_metadata = checkpoint.workflow_metadata
        workflow.total_latency_ms = checkpoint.total_latency_ms
        
        # Restore task states
        for task in workflow.tasks:
            task_state = checkpoint.task_states.get(task.task_id)
            if task_state:
                task.status = TaskStatus(task_state["status"])
                task.output = task_state["output"]
                task.error_message = task_state["error"]
                task.progress = task_state["progress"]
                task.retry_count = task_state["retry_count"]
                task.latency_ms = task_state["latency_ms"]
                
                if task_state["started_at"]:
                    task.started_at = datetime.fromisoformat(task_state["started_at"])
                if task_state["completed_at"]:
                    task.completed_at = datetime.fromisoformat(task_state["completed_at"])
        
        # Restore queue state
        if self.queue and checkpoint.queue_state:
            self.queue.restore_queue_state(checkpoint.queue_state)
        
        # Restore scheduler context
        if self.scheduler and checkpoint.scheduler_context:
            context = self.scheduler._active_workflows.get(workflow.id)
            if context:
                context.completed_task_ids = set(checkpoint.scheduler_context.get("completed_task_ids", []))
                context.failed_task_ids = set(checkpoint.scheduler_context.get("failed_task_ids", []))
                # Note: running tasks would need to be re-dispatched
        
        # Restore graph state
        if self.scheduler and checkpoint.graph_state:
            context = self.scheduler._active_workflows.get(workflow.id)
            if context:
                context.graph = DependencyGraph.from_dict(checkpoint.graph_state)
        
        self.db.commit()
        
        logger.info("Restored workflow %s from checkpoint %s", workflow_id, checkpoint_model.id)
        return True
    
    def get_checkpoints(self, workflow_id: str) -> List[WorkflowCheckpointModel]:
        """Get all checkpoints for a workflow."""
        workflow = self.db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        if not workflow:
            return []
        
        return self.db.query(WorkflowCheckpointModel).filter(
            WorkflowCheckpointModel.workflow_id == workflow.id
        ).order_by(WorkflowCheckpointModel.created_at.desc()).all()
    
    async def should_checkpoint(self, workflow_id: str) -> bool:
        """Check if a checkpoint should be created."""
        count = self._tasks_since_checkpoint.get(workflow_id, 0)
        return count >= self.checkpoint_interval_tasks
    
    def increment_task_counter(self, workflow_id: str) -> None:
        """Increment the task completion counter for checkpointing."""
        self._tasks_since_checkpoint[workflow_id] = self._tasks_since_checkpoint.get(workflow_id, 0) + 1
    
    def reset_task_counter(self, workflow_id: str) -> None:
        """Reset the task completion counter after checkpoint."""
        self._tasks_since_checkpoint[workflow_id] = 0


class WorkflowReplayEngine:
    """Replays workflow execution from checkpoints for debugging."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def replay_workflow(
        self,
        workflow_id: str,
        checkpoint_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Generate a replay log of workflow execution."""
        workflow = self.db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        if not workflow:
            return []
        
        # Get checkpoints
        query = self.db.query(WorkflowCheckpointModel).filter(
            WorkflowCheckpointModel.workflow_id == workflow.id
        ).order_by(WorkflowCheckpointModel.created_at)
        
        if checkpoint_id:
            query = query.filter(WorkflowCheckpointModel.id <= checkpoint_id)
        
        checkpoints = query.all()
        
        replay_log = []
        for cp in checkpoints:
            replay_log.append({
                "checkpoint_id": cp.id,
                "checkpoint_type": cp.checkpoint_type,
                "timestamp": cp.created_at.isoformat(),
                "completed_tasks": cp.completed_tasks,
                "failed_tasks": cp.failed_tasks,
                "workflow_status": cp.state_data.get("workflow_status"),
            })
        
        return replay_log
    
    def get_execution_timeline(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get a timeline of task executions."""
        workflow = self.db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        if not workflow:
            return []
        
        timeline = []
        for task in workflow.tasks:
            if task.started_at:
                timeline.append({
                    "task_id": task.task_id,
                    "agent": task.agent,
                    "status": task.status.value,
                    "started_at": task.started_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "latency_ms": task.latency_ms,
                    "retry_count": task.retry_count,
                })
        
        # Sort by start time
        timeline.sort(key=lambda x: x["started_at"] or "")
        return timeline


# Global instances
_resumability_manager: Optional[WorkflowResumabilityManager] = None
_replay_engine: Optional[WorkflowReplayEngine] = None


def get_resumability_manager() -> Optional[WorkflowResumabilityManager]:
    """Get the global resumability manager instance."""
    return _resumability_manager


def set_resumability_manager(manager: WorkflowResumabilityManager) -> None:
    """Set the global resumability manager instance."""
    global _resumability_manager
    _resumability_manager = manager


def create_resumability_manager(
    db: Session,
    scheduler: Optional[WorkflowScheduler] = None,
    queue: Optional[WorkflowQueue] = None,
    checkpoint_interval_tasks: int = 5,
    max_checkpoints_per_workflow: int = 10,
) -> WorkflowResumabilityManager:
    """Create the global resumability manager."""
    global _resumability_manager
    _resumability_manager = WorkflowResumabilityManager(
        db=db,
        scheduler=scheduler,
        queue=queue,
        checkpoint_interval_tasks=checkpoint_interval_tasks,
        max_checkpoints_per_workflow=max_checkpoints_per_workflow,
    )
    return _resumability_manager


def get_replay_engine() -> Optional[WorkflowReplayEngine]:
    """Get the global replay engine instance."""
    return _replay_engine


def set_replay_engine(engine: WorkflowReplayEngine) -> None:
    """Set the global replay engine instance."""
    global _replay_engine
    _replay_engine = engine


def create_replay_engine(db: Session) -> WorkflowReplayEngine:
    """Create the global replay engine."""
    global _replay_engine
    _replay_engine = WorkflowReplayEngine(db=db)
    return _replay_engine