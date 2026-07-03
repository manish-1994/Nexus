from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Conversation(BaseModel):
    """Conversation model."""
    __tablename__ = "conversations"

    title = Column(String(255), nullable=False, default="New Conversation")
    user_id = Column(String(255), nullable=True, index=True)
    last_message_preview = Column(String(200), nullable=True)
    provider_name = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_conversation_updated_at', 'updated_at'),
    )
