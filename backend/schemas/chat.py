from pydantic import BaseModel
from schemas.base import BaseSchema
from typing import Optional, List, Dict, Any
from datetime import datetime

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

class ConversationCreate(ConversationBase):
  pass

class ConversationUpdate(BaseSchema):
  title: Optional[str] = None

class ConversationResponse(ConversationBase):
  id: int
  created_at: datetime
  updated_at: datetime
  messages: List[MessageResponse] = []

class ChatRequest(BaseModel):
  conversation_id: int
  content: str
  provider_id: int
  model: str
  stream: bool = True

class ChatResponse(BaseModel):
  conversation_id: int
  message: MessageResponse
  stream_content: Optional[str] = None
