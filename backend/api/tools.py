"""Tool Runtime API — endpoints for tool discovery, execution, and cancellation."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from tools.base import BaseTool
from tools.context import ExecutionContext
from tools.manager import ToolManager
from tools.permissions import PermissionValidator
from tools.registry import ToolRegistry
from tools.schemas import (
    ToolCancelRequest,
    ToolCancelResponse,
    ToolExecuteRequest,
    ToolExecuteResponse,
    ToolMetadataResponse,
    ToolResponse,
)

logger = logging.getLogger("tool_api")

router = APIRouter()

# ---------------------------------------------------------------------------
# Singleton Tool Runtime (initialized at module import)
# ---------------------------------------------------------------------------

_registry = ToolRegistry()
_registry.discover("tools.builtins")

_permission_validator = PermissionValidator()
_tool_manager = ToolManager(
    registry=_registry,
    permission_validator=_permission_validator,
)


def get_tool_manager() -> ToolManager:
    """Dependency injection for ToolManager."""
    return _tool_manager


def get_tool_registry() -> ToolRegistry:
    """Dependency injection for ToolRegistry."""
    return _registry


# ---------------------------------------------------------------------------
# Tool Discovery Endpoints
# ---------------------------------------------------------------------------


@router.get("/tools", response_model=List[ToolResponse])
async def list_tools(
    category: str | None = None,
    registry: ToolRegistry = Depends(get_tool_registry),
):
    """List all available tools, optionally filtered by category.

    Returns metadata for every registered tool including input/output schemas,
    permissions, timeout, and streaming/cancellation support.
    """
    tools = registry.list_tools(category=category)
    return [ToolResponse.from_tool(t) for t in tools]


@router.get("/tools/categories", response_model=List[str])
async def list_tool_categories(
    registry: ToolRegistry = Depends(get_tool_registry),
):
    """List all registered tool categories."""
    return registry.list_categories()


@router.get("/tools/{tool_id}", response_model=ToolResponse)
async def inspect_tool(
    tool_id: str,
    registry: ToolRegistry = Depends(get_tool_registry),
):
    """Inspect a specific tool's metadata, schemas, and capabilities."""
    tool = registry.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return ToolResponse.from_tool(tool)


# ---------------------------------------------------------------------------
# Tool Execution Endpoints
# ---------------------------------------------------------------------------


@router.post("/tools/{tool_id}/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    tool_id: str,
    request: ToolExecuteRequest,
    manager: ToolManager = Depends(get_tool_manager),
    db: Session = Depends(get_db),
):
    """Execute a tool synchronously (non-streaming).

    The tool is resolved from the registry, permissions are validated,
    input is checked against the tool's schema, and execution proceeds
    with retry logic and cancellation support.

    Returns the tool's output or error details.
    """
    # Build execution context from request
    context = ExecutionContext(
        execution_id=request.execution_id,
        agent_id=request.agent_id,
        conversation_id=request.conversation_id,
        workspace_id=request.workspace_id,
    )

    try:
        result = await manager.execute(
            tool_id=tool_id,
            input_data=request.input_data,
            context=context,
        )
        return ToolExecuteResponse(
            execution_id=request.execution_id,
            tool_id=tool_id,
            status="completed",
            output=result,
        )

    except ValueError as exc:
        # Check if it's a "not found" error
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))

    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    except Exception as exc:
        logger.exception("Tool execution failed: tool=%s exec=%s", tool_id, request.execution_id)
        return ToolExecuteResponse(
            execution_id=request.execution_id,
            tool_id=tool_id,
            status="failed",
            error=str(exc),
        )


@router.post("/tools/{tool_id}/execute-stream")
async def execute_tool_stream(
    tool_id: str,
    request: ToolExecuteRequest,
    manager: ToolManager = Depends(get_tool_manager),
    db: Session = Depends(get_db),
):
    """Execute a tool with streaming output (SSE).

    Only tools with supports_streaming=True can use this endpoint.
    Yields JSON-encoded chunks via Server-Sent Events.
    """
    context = ExecutionContext(
        execution_id=request.execution_id,
        agent_id=request.agent_id,
        conversation_id=request.conversation_id,
        workspace_id=request.workspace_id,
    )

    try:
        # Validate tool exists and supports streaming
        tool = _registry.get(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
        if not tool.metadata.supports_streaming:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{tool_id}' does not support streaming",
            )

        async def generate():
            try:
                async for chunk in manager.execute_stream(
                    tool_id=tool_id,
                    input_data=request.input_data,
                    context=context,
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as exc:
                logger.exception("Tool stream failed: tool=%s", tool_id)
                yield f"data: {{\"error\": \"{exc}\"}}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


# ---------------------------------------------------------------------------
# Cancellation Endpoint
# ---------------------------------------------------------------------------


@router.post("/tools/cancel", response_model=ToolCancelResponse)
async def cancel_tool_execution(
    request: ToolCancelRequest,
    manager: ToolManager = Depends(get_tool_manager),
):
    """Cancel an active tool execution.

    Sends a cancellation signal to the running tool. The tool must
    support cancellation (supports_cancellation=True) for this to work.
    """
    cancelled = manager.cancel(request.execution_id)

    if cancelled:
        return ToolCancelResponse(
            execution_id=request.execution_id,
            status="cancelled",
        )

    # Check if execution exists but is not cancellable
    status = manager.get_execution_status(request.execution_id)
    if status:
        return ToolCancelResponse(
            execution_id=request.execution_id,
            status="not_cancellable",
        )

    return ToolCancelResponse(
        execution_id=request.execution_id,
        status="not_found",
    )


# ---------------------------------------------------------------------------
# Active Executions
# ---------------------------------------------------------------------------


@router.get("/tools/executions/active", response_model=List[str])
async def list_active_executions(
    manager: ToolManager = Depends(get_tool_manager),
):
    """List all currently active tool execution IDs."""
    return manager.get_active_executions()