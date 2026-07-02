from typing import List, Optional
from sqlalchemy.orm import Session
from models.conversation import Conversation
from repositories.conversation_repository import ConversationRepository


class ConversationService:
    """Service for conversation operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ConversationRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get all conversations."""
        return self.repository.find_all(skip=skip, limit=limit)

    def get(self, conversation_id: int) -> Optional[Conversation]:
        """Get a single conversation by ID."""
        return self.repository.find_by_id(conversation_id)

    def create(self, data: dict) -> Conversation:
        """Create a new conversation."""
        return self.repository.create(data)

    def update(self, conversation_id: int, data: dict) -> Optional[Conversation]:
        """Update a conversation."""
        return self.repository.update(conversation_id, data)

    def delete(self, conversation_id: int) -> bool:
        """Delete a conversation."""
        return self.repository.delete(conversation_id)
