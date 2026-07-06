"""Event system for workflow execution.

Provides event emission, subscription, and streaming for real-time progress updates.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class WorkflowEventType(str, Enum):
    """Workflow event types for streaming and logging."""
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_CANCELLED = "workflow.cancelled"
    TASK_QUEUED = "task.queued"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_RETRYING = "task.retrying"
    TASK_CANCELLED = "task.cancelled"
    PROGRESS_UPDATE = "progress.update"


@dataclass
class WorkflowEvent:
    """Event emitted during workflow execution."""
    event_type: WorkflowEventType
    workflow_id: str
    task_id: Optional[str] = None
    agent: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "agent": self.agent,
            "data": self.data,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    def to_sse(self) -> str:
        """Format as Server-Sent Event."""
        return f"data: {json.dumps(self.to_dict())}\n\n"


class EventBus:
    """Event bus for workflow execution events.
    
    Supports:
    - Sync and async event emission
    - Event subscription by type
    - Wildcard subscriptions
    - Event history for replay
    """
    
    def __init__(self, history_size: int = 1000):
        self._subscribers: Dict[WorkflowEventType, List[Callable]] = {}
        self._wildcard_subscribers: List[Callable] = []
        self._history: List[WorkflowEvent] = []
        self._history_size = history_size
        self._lock = asyncio.Lock()
    
    def subscribe(self, event_type: WorkflowEventType, handler: Callable) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def subscribe_all(self, handler: Callable) -> None:
        """Subscribe to all events (wildcard)."""
        self._wildcard_subscribers.append(handler)
    
    def unsubscribe(self, event_type: WorkflowEventType, handler: Callable) -> bool:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                return True
            except ValueError:
                return False
        return False
    
    def unsubscribe_all(self, handler: Callable) -> bool:
        """Unsubscribe from wildcard."""
        try:
            self._wildcard_subscribers.remove(handler)
            return True
        except ValueError:
            return False
    
    async def emit(self, event: WorkflowEvent) -> None:
        """Emit an event to all subscribers (async)."""
        # Add to history
        self._history.append(event)
        if len(self._history) > self._history_size:
            self._history = self._history[-self._history_size:]
        
        # Call specific subscribers
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type}: {e}")
        
        # Call wildcard subscribers
        for handler in self._wildcard_subscribers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in wildcard event handler: {e}")
    
    def emit_sync(self, event: WorkflowEvent) -> None:
        """Emit an event synchronously (for non-async contexts)."""
        # Add to history
        self._history.append(event)
        if len(self._history) > self._history_size:
            self._history = self._history[-self._history_size:]
        
        # Call specific subscribers
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if not asyncio.iscoroutinefunction(handler):
                    handler(event)
            except Exception as e:
                logger.error(f"Error in sync event handler for {event.event_type}: {e}")
        
        # Call wildcard subscribers
        for handler in self._wildcard_subscribers:
            try:
                if not asyncio.iscoroutinefunction(handler):
                    handler(event)
            except Exception as e:
                logger.error(f"Error in sync wildcard event handler: {e}")
    
    def get_history(
        self,
        event_type: Optional[WorkflowEventType] = None,
        workflow_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WorkflowEvent]:
        """Get event history with optional filters."""
        events = self._history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if workflow_id:
            events = [e for e in events if e.workflow_id == workflow_id]
        
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def set_event_bus(event_bus: EventBus) -> None:
    """Set the global event bus (for testing)."""
    global _event_bus
    _event_bus = event_bus


# Convenience functions for common events
def emit_workflow_created(workflow_id: str, prompt: str, task_count: int) -> None:
    """Emit workflow created event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.WORKFLOW_CREATED,
        workflow_id=workflow_id,
        data={"prompt": prompt, "task_count": task_count},
    )
    get_event_bus().emit_sync(event)


def emit_workflow_started(workflow_id: str) -> None:
    """Emit workflow started event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.WORKFLOW_STARTED,
        workflow_id=workflow_id,
    )
    get_event_bus().emit_sync(event)


def emit_workflow_completed(workflow_id: str, results: Dict[str, Any], duration_ms: int) -> None:
    """Emit workflow completed event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.WORKFLOW_COMPLETED,
        workflow_id=workflow_id,
        data={"results": results, "duration_ms": duration_ms},
    )
    get_event_bus().emit_sync(event)


def emit_workflow_failed(workflow_id: str, error: str, partial_results: Dict[str, Any] = None) -> None:
    """Emit workflow failed event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.WORKFLOW_FAILED,
        workflow_id=workflow_id,
        data={"error": error, "partial_results": partial_results or {}},
    )
    get_event_bus().emit_sync(event)


def emit_task_queued(workflow_id: str, task_id: str, agent: str) -> None:
    """Emit task queued event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.TASK_QUEUED,
        workflow_id=workflow_id,
        task_id=task_id,
        agent=agent,
    )
    get_event_bus().emit_sync(event)


def emit_task_started(workflow_id: str, task_id: str, agent: str) -> None:
    """Emit task started event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.TASK_STARTED,
        workflow_id=workflow_id,
        task_id=task_id,
        agent=agent,
    )
    get_event_bus().emit_sync(event)


def emit_task_completed(workflow_id: str, task_id: str, agent: str, output: Dict[str, Any], duration_ms: int) -> None:
    """Emit task completed event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.TASK_COMPLETED,
        workflow_id=workflow_id,
        task_id=task_id,
        agent=agent,
        data={"output": output, "duration_ms": duration_ms},
    )
    get_event_bus().emit_sync(event)


def emit_task_failed(workflow_id: str, task_id: str, agent: str, error: str, retry_count: int) -> None:
    """Emit task failed event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.TASK_FAILED,
        workflow_id=workflow_id,
        task_id=task_id,
        agent=agent,
        data={"error": error, "retry_count": retry_count},
    )
    get_event_bus().emit_sync(event)


def emit_task_retrying(workflow_id: str, task_id: str, agent: str, retry_count: int, error: str) -> None:
    """Emit task retrying event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.TASK_RETRYING,
        workflow_id=workflow_id,
        task_id=task_id,
        agent=agent,
        data={"retry_count": retry_count, "error": error},
    )
    get_event_bus().emit_sync(event)


def emit_progress_update(workflow_id: str, progress: int, current_task: Optional[str] = None, message: str = "") -> None:
    """Emit progress update event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.PROGRESS_UPDATE,
        workflow_id=workflow_id,
        task_id=current_task,
        data={"progress": progress, "message": message},
    )
    get_event_bus().emit_sync(event)