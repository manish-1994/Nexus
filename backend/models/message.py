from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
import enum
from sqlalchemy.orm import relationship
from models.base import BaseModel


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Message model."""
    __tablename__ = "messages"

    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    provider = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
