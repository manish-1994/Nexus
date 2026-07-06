"""Pydantic schemas for tool API responses and requests."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolMetadataResponse(BaseModel):
    """Schema for tool metadata returned by the API."""

    id: str
    name: str
    description: str
    version: str
    category: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    timeout: float
    supports_streaming: bool
    supports_cancellation: bool
    permissions: List[str]


class ToolResponse(BaseModel):
    """Schema for a tool listing response."""

    metadata: ToolMetadataResponse

    @classmethod
    def from_tool(cls, tool: "BaseTool") -> "ToolResponse":
        """Create a ToolResponse from a BaseTool instance."""
        meta = tool.metadata
        return cls(
            metadata=ToolMetadataResponse(
                id=meta.id,
                name=meta.name,
                description=meta.description,
                version=meta.version,
                category=meta.category,
                input_schema=meta.input_schema,
                output_schema=meta.output_schema,
                timeout=meta.timeout,
                supports_streaming=meta.supports_streaming,
                supports_cancellation=meta.supports_cancellation,
                permissions=meta.permissions or [],
            )
        )


class ToolExecuteRequest(BaseModel):
    """Schema for tool execution request."""

    execution_id: str = Field(..., description="Unique execution identifier")
    agent_id: int = Field(..., description="Agent initiating the tool call")
    conversation_id: Optional[int] = Field(
        default=None, description="Optional conversation context"
    )
    workspace_id: Optional[int] = Field(
        default=None, description="Optional workspace context"
    )
    input_data: Dict[str, Any] = Field(
        ..., description="Tool input matching the tool's input_schema"
    )


class ToolExecuteResponse(BaseModel):
    """Schema for tool execution response."""

    execution_id: str
    tool_id: str
    status: str  # "completed" | "failed" | "cancelled"
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class ToolCancelRequest(BaseModel):
    """Schema for tool cancellation request."""

    execution_id: str = Field(..., description="Execution ID to cancel")


class ToolCancelResponse(BaseModel):
    """Schema for tool cancellation response."""

    execution_id: str
    status: str  # "cancelled" | "not_found" | "not_cancellable"


# Forward reference for type hints
from .base import BaseTool