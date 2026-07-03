from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.conversation import Conversation
from models.message import Message
from repositories.base_repository import BaseRepository

class ConversationRepository(BaseRepository[Conversation]):
    """Repository for conversation data access."""

    def __init__(self, db: Session):
        super().__init__(Conversation, db)

    def find_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Find conversations by user ID."""
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_title(self, query: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Search conversations by title."""
        return (
            self.db.query(Conversation)
            .filter(Conversation.title.ilike(f"%{query}%"))
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_by_message_content(self, query: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Search conversations by message content."""
        return (
            self.db.query(Conversation)
            .join(Message, Message.conversation_id == Conversation.id)
            .filter(Message.content.ilike(f"%{query}%"))
            .distinct()
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
