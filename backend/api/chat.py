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
    """List all conversations."""
    conversations = service.get_all(skip=skip, limit=limit)
    return conversations


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
    logger.info("POST /chat entered conversation_id=%s provider_id=%s model=%s stream=%s", request.conversation_id, request.provider_id, request.model, request.stream)
    try:
        result = await service.send_message(
            conversation_id=request.conversation_id,
            content=request.content,
            provider_id=request.provider_id,
            model=request.model,
            stream=request.stream,
        )
        logger.info("service.send_message completed stream=%s", bool(result.get("stream")))

        if request.stream and result.get("stream"):
            logger.info("entering streaming response path via AI Runtime")
            runtime = AIRuntime(db)

            async def generate():
                logger.info("generate() started")
                try:
                    async for chunk in runtime.stream(
                        messages=result["messages"],
                        provider_id=result.get("provider_id"),
                        model=result["model"],
                        conversation_id=result["conversation_id"],
                    ):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                except Exception as e:
                    logger.exception("streaming error")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            logger.info("returning StreamingResponse")
            return StreamingResponse(generate(), media_type="text/event-stream")
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
