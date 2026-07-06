"""Execution model for the Agent Runtime.

Tracks every agent execution with full lifecycle metadata:
execution ID, status state machine, provider context, token usage,
retry/fallback info, timestamps, and error details.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from .base import BaseModel


class ExecutionStatus(str, enum.Enum):
    """Execution lifecycle states."""

    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_TOOL = "waiting_for_tool"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Execution(BaseModel):
    """Persistent record of an agent execution run."""

    __tablename__ = "execution_logs"

    # Unique execution identifier (UUID4 string)
    execution_id = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )

    # Agent that was executed
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # Optional conversation context
    conversation_id = Column(
        Integer, ForeignKey("conversations.id"), nullable=True, index=True
    )

    # Lifecycle state
    status = Column(
        Enum(ExecutionStatus),
        default=ExecutionStatus.IDLE,
        nullable=False,
        index=True,
    )

    # Provider context
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    model = Column(String(255), nullable=True)

    # Input / Output
    input_messages = Column(Text, nullable=True)  # JSON-serialized message list
    system_prompt = Column(Text, nullable=True)  # The assembled system prompt
    output_response = Column(Text, nullable=True)  # Final response text
    streaming_chunks = Column(Integer, default=0)  # Number of stream chunks received

    # Token metrics
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)

    # Timing
    latency_ms = Column(Integer, nullable=True)  # Total execution duration in ms

    # Retry / Fallback
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    fallback_provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    fallback_model = Column(String(255), nullable=True)

    # Tool calls made during this execution (JSON array)
    tool_calls = Column(JSON, nullable=True, default=list)

    # Error info (populated on failure)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    # Lifecycle timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    agent = relationship("Agent", foreign_keys=[agent_id], lazy="joined")
    provider = relationship("Provider", foreign_keys=[provider_id], lazy="joined")
    fallback_provider = relationship(
        "Provider", foreign_keys=[fallback_provider_id], lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<Execution(id={self.id}, execution_id='{self.execution_id}', "
            f"status='{self.status}', agent_id={self.agent_id})>"
        )
