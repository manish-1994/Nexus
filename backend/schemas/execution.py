"""Pydantic schemas for execution records."""

from datetime import datetime
from typing import Optional

from models.execution import ExecutionStatus
from pydantic import BaseModel, Field


class ExecutionResponse(BaseModel):
    """Response schema for an execution record."""

    id: int
    execution_id: str
    agent_id: int
    agent_name: Optional[str] = None
    conversation_id: Optional[int] = None
    status: ExecutionStatus
    provider_id: Optional[int] = None
    provider_name: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    output_response: Optional[str] = None
    streaming_chunks: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    fallback_provider_id: Optional[int] = None
    fallback_model: Optional[str] = None
    fallback_used: bool = False
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ExecutionListResponse(BaseModel):
    """Response schema for a list of executions."""

    executions: list[ExecutionResponse]
    total: int
    limit: int
    offset: int


class CancelResponse(BaseModel):
    """Response schema for cancellation."""

    execution_id: str
    status: ExecutionStatus
    message: str
