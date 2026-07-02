from typing import List, Optional
from sqlalchemy.orm import Session
from models.message import Message
from repositories.message_repository import MessageRepository


class MessageService:
    """Service for message operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = MessageRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Message]:
        """Get all messages."""
        return self.repository.find_all(skip=skip, limit=limit)

    def get(self, message_id: int) -> Optional[Message]:
        """Get a single message by ID."""
        return self.repository.find_by_id(message_id)

    def find_by_conversation_id(self, conversation_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        """Find messages by conversation ID."""
        return self.repository.find_by_conversation_id(conversation_id, skip=skip, limit=limit)
