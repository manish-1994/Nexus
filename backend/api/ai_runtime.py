from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.ai_runtime import AIRequest, AIResponse, CapabilityResponse
from services.ai_runtime import AIRuntime
from services.provider_service import ProviderService
from database import get_db
import logging

router = APIRouter()
logger = logging.getLogger("ai_runtime_api")


def get_ai_runtime(db: Session = Depends(get_db)) -> AIRuntime:
    return AIRuntime(db)


@router.post("/ai/chat", response_model=AIResponse)
async def ai_chat(request: AIRequest, runtime: AIRuntime = Depends(get_ai_runtime)):
    """Unified chat endpoint for all modules."""
    try:
        content = await runtime.chat(
            messages=request.messages,
            provider_id=request.provider_id,
            model=request.model,
            **(request.requirements or {}),
        )
        return AIResponse(
            content=content,
            model=request.model or "unknown",
            provider="runtime",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("AI chat failed")
        raise HTTPException(status_code=500, detail="AI request failed")


@router.post("/ai/stream")
async def ai_stream(request: AIRequest, runtime: AIRuntime = Depends(get_ai_runtime)):
    """Unified streaming endpoint for all modules."""
    from fastapi.responses import StreamingResponse
    try:
        async def generate():
            async for chunk in runtime.stream(
                messages=request.messages,
                provider_id=request.provider_id,
                model=request.model,
                **(request.requirements or {}),
            ):
                yield f"data: {chunk}\n\n"
        return StreamingResponse(generate(), media_type="text/event-stream")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("AI stream failed")
        raise HTTPException(status_code=500, detail="AI stream failed")


@router.get("/ai/providers/{provider_id}/capabilities", response_model=CapabilityResponse)
async def get_capabilities(provider_id: int, runtime: AIRuntime = Depends(get_ai_runtime)):
    """Get detected capabilities for a provider."""
    from models.provider import Provider
    provider = runtime.db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    capabilities = runtime.capability_manager.detect_capabilities(provider)
    runtime.capability_manager.save_capabilities(provider_id, capabilities)
    return CapabilityResponse(
        provider_id=provider_id,
        capabilities=capabilities,
        detected_at=provider.updated_at.isoformat() if provider.updated_at else "",
        models_count=len(provider.models),
    )
