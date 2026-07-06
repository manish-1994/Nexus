"""Runtime API routes for the Agent Runtime.

Exposes endpoints for:
- Listing active (non-terminal) executions
- Getting execution details by UUID
- Cancelling active executions
- Querying execution history
"""

import logging
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from models.execution import ExecutionStatus
from schemas.execution import CancelResponse, ExecutionListResponse, ExecutionResponse
from services.execution_manager import AgentExecutionManager
from sqlalchemy.orm import Session

logger = logging.getLogger("runtime_api")

router = APIRouter(prefix="/runtime", tags=["runtime"])


def _get_manager(db: Session = Depends(get_db)) -> AgentExecutionManager:
    """Dependency to get an AgentExecutionManager instance."""
    return AgentExecutionManager(db)


def _execution_to_response(execution) -> ExecutionResponse:
    """Convert an Execution ORM object to an ExecutionResponse schema."""
    return ExecutionResponse(
        id=execution.id,
        execution_id=execution.execution_id,
        agent_id=execution.agent_id,
        agent_name=execution.agent.name if execution.agent else None,
        conversation_id=execution.conversation_id,
        status=execution.status,
        provider_id=execution.provider_id,
        provider_name=execution.provider.name if execution.provider else None,
        model=execution.model,
        system_prompt=execution.system_prompt,
        output_response=execution.output_response,
        streaming_chunks=execution.streaming_chunks or 0,
        input_tokens=execution.input_tokens or 0,
        output_tokens=execution.output_tokens or 0,
        total_tokens=execution.total_tokens or 0,
        cost=execution.cost or 0.0,
        latency_ms=execution.latency_ms,
        retry_count=execution.retry_count or 0,
        max_retries=execution.max_retries or 3,
        fallback_provider_id=execution.fallback_provider_id,
        fallback_model=execution.fallback_model,
        fallback_used=execution.fallback_provider_id is not None,
        error_message=execution.error_message,
        error_code=execution.error_code,
        created_at=execution.created_at,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
    )


@router.get("/executions", response_model=List[ExecutionResponse])
async def list_active_executions(
    manager: AgentExecutionManager = Depends(_get_manager),
):
    """List all currently active (non-terminal) executions."""
    try:
        executions = manager.list_active_executions()
        return [_execution_to_response(e) for e in executions]
    except Exception as exc:
        logger.exception("Failed to list active executions")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    manager: AgentExecutionManager = Depends(_get_manager),
):
    """Get details of a specific execution by its UUID."""
    try:
        execution = manager.get_execution(execution_id)
        if not execution:
            raise HTTPException(
                status_code=404,
                detail=f"Execution '{execution_id}' not found",
            )
        return _execution_to_response(execution)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get execution %s", execution_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/executions/{execution_id}/cancel", response_model=CancelResponse)
async def cancel_execution(
    execution_id: str,
    manager: AgentExecutionManager = Depends(_get_manager),
):
    """Cancel an active execution.

    Can cancel executions in QUEUED, RUNNING, or WAITING_FOR_TOOL states.
    Terminal states (COMPLETED, FAILED, CANCELLED) cannot be cancelled.
    """
    try:
        execution = manager.cancel(execution_id)
        return CancelResponse(
            execution_id=execution.execution_id,
            status=execution.status,
            message=f"Execution '{execution_id}' has been cancelled.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to cancel execution %s", execution_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/executions/history", response_model=ExecutionListResponse)
async def get_execution_history(
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    manager: AgentExecutionManager = Depends(_get_manager),
):
    """Get historical execution records with optional agent filter."""
    try:
        executions = manager.get_execution_history(
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        )
        # Count total for the given filter
        from models.execution import Execution

        query = manager.db.query(Execution)
        if agent_id is not None:
            query = query.filter(Execution.agent_id == agent_id)
        total = query.count()

        return ExecutionListResponse(
            executions=[_execution_to_response(e) for e in executions],
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        logger.exception("Failed to get execution history")
        raise HTTPException(status_code=500, detail=str(exc))
