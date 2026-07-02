from typing import List, Optional
from sqlalchemy.orm import Session
from models.message import Message, MessageRole
from repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for message data access."""

    def __init__(self, db: Session):
        super().__init__(Message, db)

    def find_by_conversation_id(
        self, conversation_id: int, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        """Find messages by conversation ID."""
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_message(
        self,
        conversation_id: int,
        role: MessageRole,
        content: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tokens_used: Optional[int] = None,
    ) -> Message:
        """Create a new message."""
        return self.create(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "provider": provider,
                "model": model,
                "tokens_used": tokens_used,
            }
        )
