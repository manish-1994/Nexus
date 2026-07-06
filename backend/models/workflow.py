"""Workflow and Task models for the NEXUS Workflow Execution Engine.

Tracks multi-agent workflows with full lifecycle metadata:
workflow ID, status, execution graph, tasks, results, errors, and metadata.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, 
    Integer, JSON, String, Text, func, Index
)
from sqlalchemy.orm import relationship

from .base import BaseModel


class WorkflowStatus(str, enum.Enum):
    """Workflow lifecycle states."""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"  # Some tasks failed but others completed


class TaskStatus(str, enum.Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"  # Waiting for dependencies
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class Workflow(BaseModel):
    """Persistent record of a multi-agent workflow execution."""
    
    __tablename__ = "workflows"
    
    # Unique workflow identifier (UUID4 string)
    workflow_id = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    
    # User who initiated the workflow
    user_id = Column(String(255), nullable=True, index=True)
    
    # Original user prompt
    prompt = Column(Text, nullable=False)
    
    # Lifecycle state
    status = Column(
        Enum(WorkflowStatus),
        default=WorkflowStatus.CREATED,
        nullable=False,
        index=True,
    )
    
    # Execution graph (DAG) - JSON serialized
    execution_graph = Column(JSON, nullable=True, default=dict)
    
    # Provider context for the workflow
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    model = Column(String(255), nullable=True)
    
    # Aggregated results
    results = Column(JSON, nullable=True, default=dict)
    errors = Column(JSON, nullable=True, default=list)
    
    # Metadata (renamed from metadata to avoid SQLAlchemy reserved name)
    workflow_metadata = Column(JSON, nullable=True, default=dict)
    
    # Token metrics (aggregated across all tasks)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_latency_ms = Column(Integer, nullable=True)
    
    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    provider = relationship("Provider", foreign_keys=[provider_id], lazy="joined")
    tasks = relationship("Task", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return (
            f"<Workflow(id={self.id}, workflow_id='{self.workflow_id}', "
            f"status='{self.status}', task_count={len(self.tasks) if self.tasks else 0})>"
        )


class Task(BaseModel):
    """Persistent record of a single task within a workflow."""
    
    __tablename__ = "tasks"
    
    # Unique task identifier (UUID4 string)
    task_id = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    
    # Parent workflow
    workflow_id = Column(
        Integer, ForeignKey("workflows.id"), nullable=False, index=True
    )
    
    # Agent assigned to this task
    agent = Column(String(100), nullable=False, index=True)
    
    # Task description
    description = Column(Text, nullable=False)
    
    # Dependencies - list of task_ids that must complete first
    dependencies = Column(JSON, nullable=True, default=list)
    
    # Lifecycle state
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    # Progress (0-100)
    progress = Column(Integer, default=0)
    
    # Input/Output
    input = Column(JSON, nullable=True, default=dict)
    output = Column(JSON, nullable=True, default=dict)
    
    # Provider context for this specific task
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    model = Column(String(255), nullable=True)
    
    # Token metrics
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_error = Column(Text, nullable=True)
    
    # Error info
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="tasks")
    provider = relationship("Provider", foreign_keys=[provider_id], lazy="joined")
    
    # Index for efficient dependency queries
    __table_args__ = (
        Index('ix_tasks_workflow_status', 'workflow_id', 'status'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Task(id={self.id}, task_id='{self.task_id}', "
            f"workflow_id={self.workflow_id}, agent='{self.agent}', "
            f"status='{self.status}')>"
        )


class WorkflowEvent(BaseModel):
    """Event log for workflow execution - for streaming and history."""
    
    __tablename__ = "workflow_events"
    
    # Event type
    event_type = Column(String(50), nullable=False, index=True)
    
    # Associated workflow
    workflow_id = Column(
        Integer, ForeignKey("workflows.id"), nullable=False, index=True
    )
    
    # Associated task (optional)
    task_id = Column(
        Integer, ForeignKey("tasks.id"), nullable=True, index=True
    )
    
    # Agent that generated the event
    agent = Column(String(100), nullable=True)
    
    # Event payload
    data = Column(JSON, nullable=True, default=dict)
    
    # Metadata (renamed from metadata to avoid SQLAlchemy reserved name)
    event_metadata = Column(JSON, nullable=True, default=dict)
    
    # Relationships
    workflow = relationship("Workflow", foreign_keys=[workflow_id])
    task = relationship("Task", foreign_keys=[task_id])
    
    def __repr__(self) -> str:
        return f"<WorkflowEvent(id={self.id}, type='{self.event_type}', workflow_id={self.workflow_id})>"