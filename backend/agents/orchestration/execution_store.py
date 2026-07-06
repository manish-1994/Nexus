"""Live Execution Store — in-memory tracking of all active executions.

Provides real-time visibility into the Agent OS state:
- Which agent is currently executing
- Completed tasks, running tasks, pending tasks
- Execution time, provider, model, token usage
- Per-execution event history

This is the source of truth for the frontend LiveStatusPanel,
TokenStreamHUD, ResponseTimeline, and AIActivityLog components.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import threading

from .agent_config import AgentRole, ExecutionStatus
from .event_bus import EventBus, ExecutionEvent, EventType


class ExecutionState(str, Enum):
    """High-level execution state for UI display."""

    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    RESEARCHING = "researching"
    CALLING_PROVIDER = "calling_provider"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ActiveExecution:
    """Live tracking record for a single execution.

    Updated in real-time as the execution progresses through
    planning, task execution, and synthesis phases.
    """

    execution_id: str
    conversation_id: Optional[int] = None
    state: ExecutionState = ExecutionState.IDLE
    current_agent: Optional[str] = None
    current_task_id: Optional[str] = None

    # Task tracking
    completed_tasks: List[str] = field(default_factory=list)
    running_tasks: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)

    # Metrics
    provider_id: Optional[int] = None
    provider_name: Optional[str] = None
    model: Optional[str] = None
    total_tokens: int = 0
    tokens_per_second: float = 0.0
    elapsed_ms: int = 0
    estimated_cost: float = 0.0
    retry_count: int = 0

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Activity log
    events: List[Dict[str, Any]] = field(default_factory=list)

    # Error
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "conversation_id": self.conversation_id,
            "state": self.state.value,
            "current_agent": self.current_agent,
            "current_task_id": self.current_task_id,
            "completed_tasks": self.completed_tasks,
            "running_tasks": self.running_tasks,
            "pending_tasks": self.pending_tasks,
            "failed_tasks": self.failed_tasks,
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "model": self.model,
            "total_tokens": self.total_tokens,
            "tokens_per_second": self.tokens_per_second,
            "elapsed_ms": self.elapsed_ms,
            "estimated_cost": self.estimated_cost,
            "retry_count": self.retry_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "events": self.events,
            "error_message": self.error_message,
        }


class LiveExecutionStore:
    """Thread-safe in-memory store for all active executions.

    Subscribes to the EventBus to automatically update execution
    state as events are emitted. Provides query methods for the
    frontend to poll current status.
    """

    def __init__(self, event_bus: "EventBus" = None):
        self._executions: Dict[str, ActiveExecution] = {}
        self._lock = threading.Lock()
        
        # Use shared EventBus singleton if not provided
        from .event_bus import get_event_bus
        self._event_bus = event_bus or get_event_bus()

        # Subscribe to event bus
        self._event_bus.subscribe_all(self._on_event)

    # ------------------------------------------------------------------
    # Execution lifecycle
    # ------------------------------------------------------------------

    def create_execution(
        self,
        execution_id: str,
        conversation_id: Optional[int] = None,
        provider_id: Optional[int] = None,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> ActiveExecution:
        """Register a new execution in the store."""
        execution = ActiveExecution(
            execution_id=execution_id,
            conversation_id=conversation_id,
            provider_id=provider_id,
            provider_name=provider_name,
            model=model,
            state=ExecutionState.IDLE,
            started_at=datetime.now(timezone.utc),
        )
        with self._lock:
            self._executions[execution_id] = execution
        return execution

    def update_state(self, execution_id: str, state: ExecutionState) -> None:
        """Update the high-level state of an execution."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_:
                exec_.state = state
                exec_.events.append({
                    "type": "state_change",
                    "state": state.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    def set_current_agent(self, execution_id: str, agent_role: str, task_id: Optional[str] = None) -> None:
        """Set the currently executing agent."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_:
                exec_.current_agent = agent_role
                exec_.current_task_id = task_id

    def add_task(self, execution_id: str, task_id: str) -> None:
        """Add a task to the pending list."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_ and task_id not in exec_.pending_tasks:
                exec_.pending_tasks.append(task_id)

    def start_task(self, execution_id: str, task_id: str) -> None:
        """Move a task from pending to running."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_:
                if task_id in exec_.pending_tasks:
                    exec_.pending_tasks.remove(task_id)
                if task_id not in exec_.running_tasks:
                    exec_.running_tasks.append(task_id)

    def complete_task(
        self,
        execution_id: str,
        task_id: str,
        tokens: int = 0,
        latency_ms: int = 0,
    ) -> None:
        """Move a task from running to completed."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_:
                if task_id in exec_.running_tasks:
                    exec_.running_tasks.remove(task_id)
                if task_id not in exec_.completed_tasks:
                    exec_.completed_tasks.append(task_id)
                exec_.total_tokens += tokens
                self._recompute_metrics(exec_)

    def fail_task(self, execution_id: str, task_id: str, error: str = "") -> None:
        """Mark a task as failed."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_:
                if task_id in exec_.running_tasks:
                    exec_.running_tasks.remove(task_id)
                if task_id in exec_.pending_tasks:
                    exec_.pending_tasks.remove(task_id)
                if task_id not in exec_.failed_tasks:
                    exec_.failed_tasks.append(task_id)
                if error:
                    exec_.error_message = error

    def complete_execution(
        self,
        execution_id: str,
        total_tokens: int = 0,
        total_latency_ms: int = 0,
    ) -> None:
        """Mark an execution as completed."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_:
                exec_.state = ExecutionState.COMPLETED
                exec_.completed_at = datetime.now(timezone.utc)
                exec_.total_tokens = total_tokens or exec_.total_tokens
                exec_.elapsed_ms = total_latency_ms or exec_.elapsed_ms
                exec_.current_agent = None
                exec_.current_task_id = None

    def fail_execution(self, execution_id: str, error: str = "") -> None:
        """Mark an execution as failed."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_:
                exec_.state = ExecutionState.FAILED
                exec_.completed_at = datetime.now(timezone.utc)
                exec_.error_message = error or exec_.error_message
                exec_.current_agent = None
                exec_.current_task_id = None

    def cancel_execution(self, execution_id: str) -> None:
        """Mark an execution as cancelled."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_:
                exec_.state = ExecutionState.CANCELLED
                exec_.completed_at = datetime.now(timezone.utc)
                exec_.current_agent = None
                exec_.current_task_id = None

    def record_retry(self, execution_id: str) -> None:
        """Increment the retry counter."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_:
                exec_.retry_count += 1

    def record_tokens(self, execution_id: str, tokens: int) -> None:
        """Add tokens to the running total."""
        with self._lock:
            exec_ = self._executions.get(execution_id)
            if exec_:
                exec_.total_tokens += tokens
                self._recompute_metrics(exec_)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_execution(self, execution_id: str) -> Optional[ActiveExecution]:
        """Get an execution by ID."""
        with self._lock:
            return self._executions.get(execution_id)

    def get_execution_dict(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get an execution as a dictionary (for API responses)."""
        exec_ = self.get_execution(execution_id)
        return exec_.to_dict() if exec_ else None

    def get_all_active(self) -> List[Dict[str, Any]]:
        """Get all active (non-terminal) executions."""
        terminal = {ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED}
        with self._lock:
            return [
                e.to_dict()
                for e in self._executions.values()
                if e.state not in terminal
            ]

    def get_by_conversation(self, conversation_id: int) -> Optional[ActiveExecution]:
        """Get the active execution for a conversation."""
        with self._lock:
            for exec_ in self._executions.values():
                if exec_.conversation_id == conversation_id:
                    if exec_.state not in {
                        ExecutionState.COMPLETED,
                        ExecutionState.FAILED,
                        ExecutionState.CANCELLED,
                    }:
                        return exec_
        return None

    def cleanup_completed(self, max_age_ms: int = 300_000) -> int:
        """Remove completed executions older than max_age_ms.

        Args:
            max_age_ms: Maximum age in milliseconds (default: 5 minutes)

        Returns:
            Number of executions removed
        """
        now = datetime.now(timezone.utc)
        removed = 0
        with self._lock:
            to_remove = []
            for exec_id, exec_ in self._executions.items():
                if exec_.state in {
                    ExecutionState.COMPLETED,
                    ExecutionState.FAILED,
                    ExecutionState.CANCELLED,
                }:
                    if exec_.completed_at:
                        age = (now - exec_.completed_at).total_seconds() * 1000
                        if age > max_age_ms:
                            to_remove.append(exec_id)
            for exec_id in to_remove:
                del self._executions[exec_id]
                removed += 1
        return removed

    @property
    def active_count(self) -> int:
        """Number of currently active executions."""
        terminal = {ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED}
        with self._lock:
            return sum(1 for e in self._executions.values() if e.state not in terminal)

    # ------------------------------------------------------------------
    # Event bus integration
    # ------------------------------------------------------------------

    async def _on_event(self, event: ExecutionEvent) -> None:
        """Handle events from the EventBus to update execution state."""
        exec_id = event.execution_id
        if not exec_id:
            return

        event_type = event.type

        if event_type == EventType.EXECUTION_STARTED:
            self.update_state(exec_id, ExecutionState.THINKING)

        elif event_type == EventType.PLANNING_STARTED:
            self.update_state(exec_id, ExecutionState.PLANNING)

        elif event_type == EventType.PLANNING_COMPLETED:
            # Add all planned tasks
            tasks = event.data.get("tasks", [])
            for task in tasks:
                self.add_task(exec_id, task.get("id", ""))

        elif event_type == EventType.TASK_STARTED:
            task_id = event.task_id
            agent_role = event.agent_role
            if task_id:
                self.start_task(exec_id, task_id)
            if agent_role:
                self.set_current_agent(exec_id, agent_role, task_id)
                # Map agent role to execution state
                role_state_map = {
                    "research": ExecutionState.RESEARCHING,
                    "coder": ExecutionState.CALLING_PROVIDER,
                    "analyst": ExecutionState.CALLING_PROVIDER,
                    "memory": ExecutionState.THINKING,
                    "tool": ExecutionState.CALLING_PROVIDER,
                }
                state = role_state_map.get(agent_role, ExecutionState.CALLING_PROVIDER)
                self.update_state(exec_id, state)

        elif event_type == EventType.TASK_COMPLETED:
            task_id = event.task_id
            tokens = event.data.get("tokens_used", 0)
            latency = event.data.get("latency_ms", 0)
            if task_id:
                self.complete_task(exec_id, task_id, tokens, latency)

        elif event_type == EventType.TASK_FAILED:
            task_id = event.task_id
            error = event.data.get("error", "")
            if task_id:
                self.fail_task(exec_id, task_id, error)

        elif event_type == EventType.STREAMING_STARTED:
            self.update_state(exec_id, ExecutionState.STREAMING)

        elif event_type == EventType.STREAMING_CHUNK:
            chunk = event.data.get("chunk", "")
            # Estimate tokens (rough: ~4 chars per token)
            estimated_tokens = max(1, len(chunk) // 4)
            self.record_tokens(exec_id, estimated_tokens)

        elif event_type == EventType.STREAMING_COMPLETED:
            pass  # State will be updated by execution_completed

        elif event_type == EventType.EXECUTION_COMPLETED:
            total_tokens = event.data.get("total_tokens", 0)
            total_latency = event.data.get("total_latency_ms", 0)
            self.complete_execution(exec_id, total_tokens, total_latency)

        elif event_type == EventType.EXECUTION_FAILED:
            error = event.data.get("error", "")
            self.fail_execution(exec_id, error)

        elif event_type == EventType.EXECUTION_CANCELLED:
            self.cancel_execution(exec_id)

        elif event_type == EventType.RETRY_ATTEMPTED:
            self.record_retry(exec_id)

        elif event_type == EventType.FAILOVER_TRIGGERED:
            new_provider = event.data.get("fallback_provider")
            new_model = event.data.get("fallback_model")
            with self._lock:
                exec_ = self._executions.get(exec_id)
                if exec_:
                    if new_provider:
                        exec_.provider_name = str(new_provider)
                    if new_model:
                        exec_.model = str(new_model)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _recompute_metrics(self, exec_: ActiveExecution) -> None:
        """Recompute derived metrics (tokens/sec, cost, elapsed)."""
        if exec_.started_at:
            now = datetime.now(timezone.utc)
            elapsed_sec = (now - exec_.started_at).total_seconds()
            exec_.elapsed_ms = int(elapsed_sec * 1000)
            if elapsed_sec > 0 and exec_.total_tokens > 0:
                exec_.tokens_per_second = exec_.total_tokens / elapsed_sec

        # Rough cost estimation ($0.002 per 1K tokens as baseline)
        exec_.estimated_cost = (exec_.total_tokens / 1000) * 0.002


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_execution_store: Optional[LiveExecutionStore] = None


def get_execution_store() -> LiveExecutionStore:
    """Get or create the singleton LiveExecutionStore with attached EventBus."""
    global _execution_store
    if _execution_store is None:
        from .event_bus import get_event_bus
        event_bus = get_event_bus()
        _execution_store = LiveExecutionStore(event_bus=event_bus)
    return _execution_store


def set_execution_store(store: LiveExecutionStore) -> None:
    """Set the singleton LiveExecutionStore (for testing)."""
    global _execution_store
    _execution_store = store