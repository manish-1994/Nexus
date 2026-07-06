"""Event Bus for the Agent Operating System.

Provides a pub/sub event system that decouples agent execution from
observability, logging, and UI updates. Events are emitted at every
significant lifecycle transition and can be subscribed to by any
number of listeners.

Event types:
    ExecutionStarted, TaskStarted, TaskCompleted, ToolStarted,
    ToolFinished, StreamingStarted, StreamingCompleted,
    ExecutionCompleted, ExecutionFailed, ExecutionCancelled
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set
import uuid

logger = logging.getLogger("event_bus")


class EventType(str, Enum):
    """Canonical event types in the Agent OS."""

    # Execution lifecycle
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_CANCELLED = "execution_cancelled"

    # Task lifecycle
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"

    # Tool lifecycle
    TOOL_STARTED = "tool_started"
    TOOL_FINISHED = "tool_finished"
    TOOL_FAILED = "tool_failed"

    # Streaming lifecycle
    STREAMING_STARTED = "streaming_started"
    STREAMING_CHUNK = "streaming_chunk"
    STREAMING_COMPLETED = "streaming_completed"

    # Agent lifecycle
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"
    AGENT_HEALTH_CHANGED = "agent_health_changed"

    # Planning
    PLANNING_STARTED = "planning_started"
    PLANNING_COMPLETED = "planning_completed"

    # Synthesis
    SYNTHESIS_STARTED = "synthesis_started"
    SYNTHESIS_COMPLETED = "synthesis_completed"

    # Failover
    FAILOVER_TRIGGERED = "failover_triggered"
    RETRY_ATTEMPTED = "retry_attempted"


@dataclass
class ExecutionEvent:
    """An event emitted by the Event Bus.

    Attributes:
        id: Unique event identifier
        type: Event type from EventType enum
        execution_id: The execution this event belongs to
        task_id: The task this event belongs to (if applicable)
        agent_role: The agent role that triggered this event
        timestamp: When the event was created (UTC)
        data: Event-specific payload
        metadata: Arbitrary key-value metadata
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.EXECUTION_STARTED
    execution_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_role: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "agent_role": self.agent_role,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
        }


# Type alias for event handlers
EventHandler = Callable[[ExecutionEvent], Awaitable[None]]


class EventBus:
    """Pub/sub event bus for the Agent Operating System.

    Supports:
    - Multiple subscribers per event type
    - Wildcard subscription ("*" matches all events)
    - Async handler invocation
    - Synchronous fire-and-forget emission
    - Event history buffer for late subscribers
    """

    def __init__(self, history_size: int = 100):
        self._subscribers: Dict[EventType, Set[EventHandler]] = {}
        self._wildcard_subscribers: Set[EventHandler] = set()
        self._history: List[ExecutionEvent] = []
        self._history_size = history_size
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type.

        Args:
            event_type: The event type to listen for
            handler: Async callable that receives ExecutionEvent
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(handler)
        logger.debug("Subscribed handler to event type: %s", event_type.value)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe a handler to ALL event types (wildcard).

        Args:
            handler: Async callable that receives ExecutionEvent
        """
        self._wildcard_subscribers.add(handler)
        logger.debug("Subscribed wildcard handler")

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove a handler from a specific event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(handler)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    def unsubscribe_all(self, handler: EventHandler) -> None:
        """Remove a wildcard handler."""
        self._wildcard_subscribers.discard(handler)

    # ------------------------------------------------------------------
    # Emission
    # ------------------------------------------------------------------

    async def emit(self, event: ExecutionEvent) -> None:
        """Emit an event to all subscribers.

        Handlers are invoked concurrently. Failures in one handler
        do not prevent other handlers from receiving the event.

        Args:
            event: The event to emit
        """
        # Add to history
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._history_size:
                self._history = self._history[-self._history_size:]

        # Collect all handlers that should receive this event
        handlers: List[EventHandler] = list(self._wildcard_subscribers)
        if event.type in self._subscribers:
            handlers.extend(self._subscribers[event.type])

        if not handlers:
            return

        # Fire to all handlers concurrently
        tasks = []
        for handler in handlers:
            tasks.append(self._invoke_handler(handler, event))

        # Wait for all handlers to complete (but don't let one failure block)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.warning(
                    "Event handler failed for event %s: %s",
                    event.type.value,
                    result,
                )

    def emit_sync(self, event: ExecutionEvent) -> None:
        """Schedule an event emission without waiting for handlers.

        Use this when you don't need to wait for handler completion
        (e.g., from within a streaming generator).

        Args:
            event: The event to emit
        """
        asyncio.create_task(self.emit(event))

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        execution_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[ExecutionEvent]:
        """Retrieve recent events, optionally filtered.

        Args:
            event_type: Filter by event type
            execution_id: Filter by execution ID
            limit: Maximum number of events to return

        Returns:
            List of matching events (newest first)
        """
        events = list(reversed(self._history))

        if event_type:
            events = [e for e in events if e.type == event_type]
        if execution_id:
            events = [e for e in events if e.execution_id == execution_id]

        return events[:limit]

    def clear_history(self) -> None:
        """Clear the event history buffer."""
        self._history.clear()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _invoke_handler(self, handler: EventHandler, event: ExecutionEvent) -> None:
        """Invoke a single handler with error isolation."""
        try:
            await handler(event)
        except Exception as exc:
            logger.warning(
                "Event handler %s failed for event %s: %s",
                getattr(handler, "__name__", str(handler)),
                event.type.value,
                exc,
            )

    @property
    def subscriber_count(self) -> int:
        """Total number of subscribers (including wildcards)."""
        count = len(self._wildcard_subscribers)
        for handlers in self._subscribers.values():
            count += len(handlers)
        return count


# ---------------------------------------------------------------------------
# Convenience factory methods for common events
# ---------------------------------------------------------------------------

def make_execution_started_event(
    execution_id: str,
    agent_role: str,
    provider_id: Optional[int] = None,
    model: Optional[str] = None,
    input_message_count: int = 0,
) -> ExecutionEvent:
    """Create an EXECUTION_STARTED event."""
    return ExecutionEvent(
        type=EventType.EXECUTION_STARTED,
        execution_id=execution_id,
        agent_role=agent_role,
        data={
            "provider_id": provider_id,
            "model": model,
            "input_message_count": input_message_count,
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def make_task_started_event(
    execution_id: str,
    task_id: str,
    agent_role: str,
    description: str = "",
) -> ExecutionEvent:
    """Create a TASK_STARTED event."""
    return ExecutionEvent(
        type=EventType.TASK_STARTED,
        execution_id=execution_id,
        task_id=task_id,
        agent_role=agent_role,
        data={
            "description": description,
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def make_task_completed_event(
    execution_id: str,
    task_id: str,
    agent_role: str,
    tokens_used: int = 0,
    latency_ms: int = 0,
    tool_calls: Optional[List[Dict]] = None,
) -> ExecutionEvent:
    """Create a TASK_COMPLETED event."""
    return ExecutionEvent(
        type=EventType.TASK_COMPLETED,
        execution_id=execution_id,
        task_id=task_id,
        agent_role=agent_role,
        data={
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "tool_calls": tool_calls or [],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def make_streaming_chunk_event(
    execution_id: str,
    task_id: str,
    agent_role: str,
    chunk: str,
    chunk_index: int = 0,
) -> ExecutionEvent:
    """Create a STREAMING_CHUNK event."""
    return ExecutionEvent(
        type=EventType.STREAMING_CHUNK,
        execution_id=execution_id,
        task_id=task_id,
        agent_role=agent_role,
        data={
            "chunk": chunk,
            "chunk_index": chunk_index,
        },
    )


def make_execution_completed_event(
    execution_id: str,
    total_tokens: int = 0,
    total_latency_ms: int = 0,
    agents_used: Optional[List[str]] = None,
    retry_count: int = 0,
) -> ExecutionEvent:
    """Create an EXECUTION_COMPLETED event."""
    return ExecutionEvent(
        type=EventType.EXECUTION_COMPLETED,
        execution_id=execution_id,
        data={
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency_ms,
            "agents_used": agents_used or [],
            "retry_count": retry_count,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    )