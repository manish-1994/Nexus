"""Agent management API routes."""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentTestRequest,
    AgentTestResponse,
)
from services.agent_service import AgentService

router = APIRouter()
logger = logging.getLogger("agents")


def _get_service(db: Session = Depends(get_db)) -> AgentService:
    """Dependency for getting AgentService."""
    return AgentService(db)


@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(service: AgentService = Depends(_get_service)):
    """List all agents."""
    return service.list_agents()


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, service: AgentService = Depends(_get_service)):
    """Get a specific agent."""
    try:
        return service.get_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_in: AgentCreate, service: AgentService = Depends(_get_service)
):
    """Create a new agent."""
    try:
        return service.create_agent(agent_in.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to create agent")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_in: AgentUpdate,
    service: AgentService = Depends(_get_service),
):
    """Update an agent."""
    try:
        update_data = agent_in.model_dump(exclude_unset=True)
        return service.update_agent(agent_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to update agent %d", agent_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(agent_id: int, service: AgentService = Depends(_get_service)):
    """Delete an agent."""
    try:
        service.delete_agent(agent_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/clone", response_model=AgentResponse, status_code=201)
async def clone_agent(agent_id: int, service: AgentService = Depends(_get_service)):
    """Clone an agent."""
    try:
        return service.clone_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to clone agent %d", agent_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/agents/{agent_id}/default", response_model=AgentResponse)
async def set_default_agent(
    agent_id: int, service: AgentService = Depends(_get_service)
):
    """Set an agent as the default."""
    try:
        return service.set_default_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/agents/{agent_id}/test", response_model=AgentTestResponse)
async def test_agent(
    agent_id: int,
    request: AgentTestRequest,
    service: AgentService = Depends(_get_service),
):
    """Test agent configuration and execution (non-streaming)."""
    try:
        result = await service.test_agent(
            agent_id=agent_id,
            message=request.message,
            provider_id=request.provider_id,
            model=request.model,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Agent test failed for agent %d", agent_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/test-stream")
async def test_agent_stream(
    agent_id: int,
    request: AgentTestRequest,
    service: AgentService = Depends(_get_service),
):
    """Test agent with live streaming (SSE)."""
    try:
        # Validate agent exists before streaming
        service.get_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    async def stream_generator():
        """SSE stream generator for agent test."""
        try:
            async for chunk in service.test_agent_stream(
                agent_id=agent_id,
                message=request.message,
                provider_id=request.provider_id,
                model=request.model,
            ):
                sse_data = json.dumps({"content": chunk})
                yield f"data: {sse_data}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            logger.exception("Agent stream test failed for agent %d", agent_id)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


__all__ = ["router"]
