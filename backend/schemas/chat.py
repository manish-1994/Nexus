from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from schemas.base import BaseSchema


class MessageBase(BaseSchema):
    role: str
    content: str
    provider: Optional[str] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None


class MessageCreate(MessageBase):
    conversation_id: int


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime


class ConversationBase(BaseSchema):
    title: str
    user_id: Optional[str] = None
    last_message_preview: Optional[str] = None
    provider_name: Optional[str] = None
    model_name: Optional[str] = None
    message_count: Optional[int] = 0


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseSchema):
    title: Optional[str] = None
    last_message_preview: Optional[str] = None
    provider_name: Optional[str] = None
    model_name: Optional[str] = None


class ConversationResponse(ConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []


class ChatRequest(BaseModel):
    conversation_id: int
    content: str
    provider_id: Optional[int] = None
    model: Optional[str] = None
    stream: bool = True
    agent_id: Optional[int] = None


class ChatResponse(BaseModel):
    conversation_id: int
    message: MessageResponse
    stream_content: Optional[str] = None
    execution_id: Optional[str] = None
