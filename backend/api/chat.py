from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.chat import (
    ChatRequest,
    MessageResponse,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
)
from services.chat_service import ChatService
from services.conversation_service import ConversationService
from services.message_service import MessageService
import json
import logging

router = APIRouter()
logger = logging.getLogger("chat")


def sse_error(message: str) -> str:
    """Format an error as a Server-Sent Events data frame."""
    return f"data: {json.dumps({'error': message})}\n\n"


async def stream_generator(
    runtime,
    messages: list,
    provider_id: int,
    model: str,
    conversation_id: int,
):
    """Top-level async generator for SSE streaming.

    Uses the module-level ``json`` import — no closure variable capture.
    """
    logger.info("stream_generator() started")
    logger.info(
        "[DEBUG] About to call runtime.stream messages_count=%d provider_id=%s model=%s",
        len(messages), provider_id, model,
    )
    try:
        async for chunk in runtime.stream(
            messages=messages,
            provider_id=provider_id,
            model=model,
            conversation_id=conversation_id,
        ):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    except Exception as e:
        logger.exception("streaming error")
        yield sse_error(str(e))


def get_conversation_service(db: Session = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    return MessageService(db)


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    return ChatService(db)


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    service: ConversationService = Depends(get_conversation_service),
):
    """List all conversations with metadata."""
    conversations = service.get_all_with_metadata()
    return conversations


@router.get("/conversations/search", response_model=List[ConversationResponse])
async def search_conversations(
    q: str,
    service: ConversationService = Depends(get_conversation_service),
):
    """Search conversations by title and message content."""
    if not q.strip():
        return []
    results = service.search(q.strip())
    return results


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    conversation_in: ConversationCreate,
    service: ConversationService = Depends(get_conversation_service),
):
    """Create a new conversation."""
    conversation = service.create(conversation_in.dict())
    return conversation


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    service: ConversationService = Depends(get_conversation_service),
):
    """Get a specific conversation."""
    conversation = service.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation_in: ConversationUpdate,
    service: ConversationService = Depends(get_conversation_service),
):
    """Update a conversation."""
    conversation = service.update(conversation_id, conversation_in.dict(exclude_unset=True))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int,
    service: ConversationService = Depends(get_conversation_service),
):
    """Delete a conversation."""
    success = service.delete(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return None


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    service: MessageService = Depends(get_message_service),
):
    """Get messages for a conversation."""
    messages = service.find_by_conversation_id(conversation_id, skip=skip, limit=limit)
    return messages


@router.post("/chat")
async def send_message(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
    db: Session = Depends(get_db),
):
    """Send a message and get AI response."""
    from services.ai_runtime import AIRuntime
    from agents.manager import AgentManager
    logger.info("POST /chat entered conversation_id=%s provider_id=%s model=%s stream=%s agent_id=%s", request.conversation_id, request.provider_id, request.model, request.stream, request.agent_id)
    try:
        payload = request.model_dump()
    except Exception as e:
        logger.error("[DEBUG] request.model_dump() FAILED: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Invalid request payload: {str(e)}")
    logger.info("[DEBUG] Full request payload: %s", payload)

    # Log each required field explicitly
    logger.info("[DEBUG] Field check: conversation_id=%s (type=%s)", request.conversation_id, type(request.conversation_id).__name__)
    logger.info("[DEBUG] Field check: content=%s (type=%s, len=%d)", request.content[:50] if request.content else None, type(request.content).__name__, len(request.content or ""))
    logger.info("[DEBUG] Field check: provider_id=%s (type=%s)", request.provider_id, type(request.provider_id).__name__)
    logger.info("[DEBUG] Field check: model=%s (type=%s)", request.model, type(request.model).__name__)
    logger.info("[DEBUG] Field check: stream=%s (type=%s)", request.stream, type(request.stream).__name__)
    logger.info("[DEBUG] Field check: agent_id=%s (type=%s)", request.agent_id, type(request.agent_id).__name__)

    eff_provider_id = request.provider_id
    eff_model = request.model

    manager = None
    agent_config = {}
    if request.agent_id:
        manager = AgentManager(db)
        agent_config = manager.get_agent_config(request.agent_id)
        logger.info("[DEBUG] Agent config resolved: %s", agent_config)
        if eff_provider_id is None and agent_config.get("provider_id"):
            eff_provider_id = agent_config["provider_id"]
        if eff_model is None and agent_config.get("model"):
            eff_model = agent_config["model"]

    logger.info("[DEBUG] Effective provider_id=%s model=%s", eff_provider_id, eff_model)

    if eff_provider_id is None:
        logger.error("[DEBUG] VALIDATION FAILED: Provider ID is required (eff_provider_id is None)")
        raise HTTPException(status_code=400, detail="Provider ID is required")
    if eff_model is None:
        logger.error("[DEBUG] VALIDATION FAILED: Model is required (eff_model is None)")
        raise HTTPException(status_code=400, detail="Model is required")

    if manager:
        try:
            manager.validate_execution(eff_provider_id, eff_model)
            logger.info("[DEBUG] validate_execution passed")
        except ValueError as e:
            logger.error("[DEBUG] validate_execution FAILED: %s", str(e))
            # Detailed diagnostic logging
            from models.provider import Provider
            provider = db.query(Provider).filter(Provider.id == eff_provider_id).first()
            available_models = []
            if provider:
                try:
                    available_models = [m.name for m in provider.models]
                except Exception:
                    available_models = []
            logger.error("[DEBUG] Validation detail: Provider=%s (id=%s) Available models=%s Requested model=%s",
                        provider.name if provider else "NOT_FOUND",
                        eff_provider_id,
                        available_models,
                        eff_model)
            raise HTTPException(status_code=400, detail=str(e))

    try:
        # First save the user message via service (this could be refactored later)
        # But we need ChatService to not execute it if we want custom agent logic.
        # Wait, ChatService.send_message currently handles saving AND executing non-streaming.
        # We can just intercept the messages array in the AIRuntime stream or non-stream?
        # Actually, if we use ChatService.send_message, it returns the messages.
        
        logger.info("[DEBUG] Calling service.send_message conversation_id=%s provider_id=%s model=%s stream=%s", request.conversation_id, eff_provider_id, eff_model, request.stream)
        result = await service.send_message(
            conversation_id=request.conversation_id,
            content=request.content,
            provider_id=eff_provider_id,
            model=eff_model,
            stream=request.stream,
        )
        logger.info("[DEBUG] service.send_message completed result_keys=%s stream=%s", list(result.keys()) if isinstance(result, dict) else type(result).__name__, bool(result.get("stream") if isinstance(result, dict) else None))

        messages = result.get("messages", [])
        logger.info("[DEBUG] Messages from service.send_message count=%d", len(messages))

        if manager and request.agent_id:
            # Apply agent system prompt if any
            logger.info("[DEBUG] Applying agent system prompt agent_id=%s", request.agent_id)
            messages = manager.build_prompt_for_agent(request.agent_id, messages)
            logger.info("[DEBUG] After agent prompt messages count=%d", len(messages))

        if request.stream and result.get("stream"):
            logger.info("entering streaming response path via AI Runtime")
            runtime = AIRuntime(db)
            logger.info("[DEBUG] AIRuntime instantiated")

            logger.info("returning StreamingResponse")
            return StreamingResponse(
                stream_generator(
                    runtime,
                    messages,
                    eff_provider_id,
                    eff_model,
                    request.conversation_id,
                ),
                media_type="text/event-stream",
            )
        else:
            if manager and request.agent_id:
                # Need to run non-streaming ourselves with the agent system prompt
                logger.info("running non-streaming with agent prompt")
                runtime = AIRuntime(db)
                logger.info("[DEBUG] About to call runtime.chat messages_count=%d provider_id=%s model=%s", len(messages), eff_provider_id, eff_model)
                response_text = await runtime.chat(messages=messages, provider_id=eff_provider_id, model=eff_model)
                logger.info("[DEBUG] runtime.chat completed response_length=%d", len(response_text))
                assistant_message = service._save_assistant_message(request.conversation_id, response_text, provider=str(eff_provider_id), model=eff_model)
                return {
                    "stream": False,
                    "conversation_id": request.conversation_id,
                    "message": {
                        "id": assistant_message.id,
                        "role": assistant_message.role,
                        "content": assistant_message.content,
                        "provider": assistant_message.provider,
                        "model": assistant_message.model,
                        "tokens_used": assistant_message.tokens_used,
                        "created_at": assistant_message.created_at.isoformat() if assistant_message.created_at else None,
                    },
                }
            else:
                logger.info("returning non-streaming result")
                return result
            
    except ValueError as e:
        logger.exception("value error in send_message")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("unexpected error in send_message")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


__all__ = ["router"]
