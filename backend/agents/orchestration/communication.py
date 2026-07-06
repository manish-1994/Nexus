"""Agent Communication Protocol.

Defines structured message types for inter-agent communication
within the Agent Operating System. Every message between agents
follows a typed envelope pattern for reliable routing and processing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class MessageType(str, Enum):
    """Standard message types in the Agent OS communication protocol."""

    # Orchestration messages
    EXECUTION_REQUEST = "execution_request"       # Orchestrator → Planner
    EXECUTION_PLAN = "execution_plan"             # Planner → Orchestrator
    TASK_ASSIGNMENT = "task_assignment"           # Orchestrator → Specialized Agent
    TASK_RESULT = "task_result"                   # Specialized Agent → Orchestrator
    TASK_FAILED = "task_failed"                   # Specialized Agent → Orchestrator

    # Tool messages
    TOOL_REQUEST = "tool_request"                 # Agent → Tool Agent
    TOOL_RESULT = "tool_result"                   # Tool Agent → Agent
    TOOL_ERROR = "tool_error"                     # Tool Agent → Agent

    # Memory messages
    MEMORY_QUERY = "memory_query"                 # Agent → Memory Agent
    MEMORY_RESULT = "memory_result"               # Memory Agent → Agent
    MEMORY_STORE = "memory_store"                 # Agent → Memory Agent

    # Streaming messages
    STREAMING_CHUNK = "streaming_chunk"           # Agent → Orchestrator (during streaming)
    STREAMING_START = "streaming_start"           # Agent → Orchestrator
    STREAMING_END = "streaming_end"               # Agent → Orchestrator

    # Control messages
    CANCEL_REQUEST = "cancel_request"             # Orchestrator → Agent
    CANCEL_CONFIRM = "cancel_confirm"             # Agent → Orchestrator
    STATUS_UPDATE = "status_update"               # Agent → Orchestrator
    HEALTH_CHECK = "health_check"                 # Orchestrator → Agent
    HEALTH_REPORT = "health_report"               # Agent → Orchestrator

    # Synthesis messages
    SYNTHESIS_REQUEST = "synthesis_request"       # Orchestrator → Synthesizer
    SYNTHESIS_RESULT = "synthesis_result"         # Synthesizer → Orchestrator


@dataclass
class AgentMessage:
    """Structured message envelope for inter-agent communication.

    Every message in the Agent OS carries this envelope, ensuring
    reliable routing, traceability, and typed payload handling.

    Attributes:
        id: Unique message identifier (UUID4)
        type: Message type from MessageType enum
        sender: Agent role/name that sent the message
        receiver: Agent role/name that should receive the message
        correlation_id: Links messages belonging to the same execution
        task_id: Links messages to a specific task within an execution
        payload: The message body (type depends on message_type)
        timestamp: When the message was created (UTC)
        ttl_ms: Time-to-live in milliseconds (0 = no expiry)
        priority: Message priority (1 = highest, 5 = lowest)
        metadata: Arbitrary key-value metadata
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.STATUS_UPDATE
    sender: str = ""
    receiver: str = ""
    correlation_id: Optional[str] = None
    task_id: Optional[str] = None
    payload: Any = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_ms: int = 0
    priority: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "correlation_id": self.correlation_id,
            "task_id": self.task_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "ttl_ms": self.ttl_ms,
            "priority": self.priority,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Deserialize from a dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=MessageType(data["type"]),
            sender=data.get("sender", ""),
            receiver=data.get("receiver", ""),
            correlation_id=data.get("correlation_id"),
            task_id=data.get("task_id"),
            payload=data.get("payload"),
            timestamp=timestamp,
            ttl_ms=data.get("ttl_ms", 0),
            priority=data.get("priority", 3),
            metadata=data.get("metadata", {}),
        )

    def is_expired(self) -> bool:
        """Check if the message has exceeded its TTL."""
        if self.ttl_ms <= 0:
            return False
        elapsed = (datetime.now(timezone.utc) - self.timestamp).total_seconds() * 1000
        return elapsed > self.ttl_ms

    def create_reply(self, reply_type: MessageType, payload: Any = None) -> "AgentMessage":
        """Create a reply message with the same correlation_id."""
        return AgentMessage(
            type=reply_type,
            sender=self.receiver,
            receiver=self.sender,
            correlation_id=self.correlation_id,
            task_id=self.task_id,
            payload=payload,
            priority=self.priority,
        )


# ---------------------------------------------------------------------------
# Payload type helpers for common message patterns
# ---------------------------------------------------------------------------

@dataclass
class ExecutionPlanPayload:
    """Payload for EXECUTION_PLAN messages."""
    intent: str
    tasks: List[Dict[str, Any]]
    execution_strategy: str  # "sequential", "parallel", "mixed"
    estimated_complexity: str  # "low", "medium", "high"
    reasoning: str = ""


@dataclass
class TaskResultPayload:
    """Payload for TASK_RESULT messages."""
    task_id: str
    agent_role: str
    output: Any
    tokens_used: int = 0
    latency_ms: int = 0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class SynthesisPayload:
    """Payload for SYNTHESIS_RESULT messages."""
    final_response: str
    sources: List[str] = field(default_factory=list)
    agents_used: List[str] = field(default_factory=list)
    total_tokens: int = 0
    total_latency_ms: int = 0