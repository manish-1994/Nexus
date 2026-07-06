"""Shared execution context between Agent Runtime and Tool Runtime."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
import asyncio
import logging


@dataclass
class ExecutionContext:
    """Shared context passed between Agent Runtime and Tool Runtime.

    Contains all information needed for a tool execution:
    - Identity: execution_id, agent_id, conversation_id, workspace_id
    - Control: cancel_event for cooperative cancellation
    - Observability: logger, stream_callback
    - Extensibility: metadata dict for arbitrary data
    """

    execution_id: str
    agent_id: int
    conversation_id: Optional[int] = None
    workspace_id: Optional[int] = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("execution")
    )
    stream_callback: Optional[Callable[[str], Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self.cancel_event.is_set()

    def check_cancellation(self) -> None:
        """Raise CancelledError if cancellation has been requested."""
        if self.is_cancelled():
            raise asyncio.CancelledError()

    def log(self, message: str, level: int = logging.INFO) -> None:
        """Log a message with execution context prefix."""
        self.logger.log(
            level,
            "[exec=%s agent=%d] %s",
            self.execution_id,
            self.agent_id,
            message,
        )