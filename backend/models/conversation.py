from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Conversation(BaseModel):
    """Conversation model."""
    __tablename__ = "conversations"

    title = Column(String(255), nullable=False, default="New Conversation")
    user_id = Column(String(255), nullable=True, index=True)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
