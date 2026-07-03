from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy import desc
from models.conversation import Conversation
from models.message import Message, MessageRole
from repositories.conversation_repository import ConversationRepository

class ConversationService:
    """Service for conversation operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ConversationRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get all conversations."""
        return self.repository.find_all(skip=skip, limit=limit)

    def get_all_with_metadata(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get conversations with last message preview and provider/model info.
        
        Returns list of dicts with conversation data plus:
        - last_message_preview: first 100 chars of last message
        - provider_name: provider from last assistant message
        - model_name: model from last assistant message
        """
        conversations = self.repository.find_all(skip=0, limit=100)
        
        result = []
        for conv in conversations:
            # Get the last message for this conversation
            last_message = (
                self.db.query(Message)
                .filter(Message.conversation_id == conv.id)
                .order_by(desc(Message.created_at))
                .first()
            )
            
            # Get provider/model from last assistant message if available
            provider_name = None
            model_name = None
            last_message_preview = None
            
            if last_message:
                # Truncate content for preview
                content = last_message.content or ''
                last_message_preview = content[:100] + ('...' if len(content) > 100 else '')
                
                # For assistant messages, get provider/model from the message
                if last_message.role == MessageRole.ASSISTANT:
                    provider_name = last_message.provider
                    model_name = last_message.model
                else:
                    # If last message is user message, look for previous assistant message
                    prev_assistant = (
                        self.db.query(Message)
                        .filter(
                            Message.conversation_id == conv.id,
                            Message.role == MessageRole.ASSISTANT
                        )
                        .order_by(desc(Message.created_at))
                        .first()
                    )
                    if prev_assistant:
                        provider_name = prev_assistant.provider
                        model_name = prev_assistant.model
            
            # Count messages for this conversation
            message_count = self.db.query(Message).filter(Message.conversation_id == conv.id).count()
        
            result.append({
                'id': conv.id,
                'title': conv.title,
                'user_id': conv.user_id,
                'created_at': conv.created_at,
                'updated_at': conv.updated_at,
                'last_message_preview': last_message_preview,
                'provider_name': provider_name,
                'model_name': model_name,
                'message_count': message_count,
            })
        
        return result

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search conversations by title and message content."""
        # Search by title
        title_matches = self.repository.search_by_title(query, limit=50)
        # Search by message content
        content_matches = self.repository.search_by_message_content(query, limit=50)

        # Combine and deduplicate by conversation ID
        seen = set()
        result = []
        for conv in title_matches + content_matches:
            if conv.id not in seen:
                seen.add(conv.id)
                # Get metadata for this conversation
                last_message = (
                    self.db.query(Message)
                    .filter(Message.conversation_id == conv.id)
                    .order_by(desc(Message.created_at))
                    .first()
                )
                provider_name = None
                model_name = None
                last_message_preview = None
                if last_message:
                    content = last_message.content or ''
                    last_message_preview = content[:100] + ('...' if len(content) > 100 else '')
                    if last_message.role == MessageRole.ASSISTANT:
                        provider_name = last_message.provider
                        model_name = last_message.model
                    else:
                        prev_assistant = (
                            self.db.query(Message)
                            .filter(
                                Message.conversation_id == conv.id,
                                Message.role == MessageRole.ASSISTANT,
                            )
                            .order_by(desc(Message.created_at))
                            .first()
                        )
                        if prev_assistant:
                            provider_name = prev_assistant.provider
                            model_name = prev_assistant.model

                message_count = self.db.query(Message).filter(Message.conversation_id == conv.id).count()

                result.append({
                    'id': conv.id,
                    'title': conv.title,
                    'user_id': conv.user_id,
                    'created_at': conv.created_at,
                    'updated_at': conv.updated_at,
                    'last_message_preview': last_message_preview,
                    'provider_name': provider_name,
                    'model_name': model_name,
                    'message_count': message_count,
                })
        return result

    def get(self, conversation_id: int) -> Optional[Conversation]:
        """Get a single conversation by ID with messages eagerly loaded."""
        return (
            self.db.query(Conversation)
            .options(joinedload(Conversation.messages))
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def create(self, data: dict) -> Conversation:
        """Create a new conversation."""
        clean_data = {k: v for k, v in data.items() if k not in ('message_count', 'last_message_preview', 'provider_name', 'model_name')}
        return self.repository.create(clean_data)

    def update(self, conversation_id: int, data: dict) -> Optional[Conversation]:
        """Update a conversation."""
        clean_data = {k: v for k, v in data.items() if k not in ('message_count', 'last_message_preview', 'provider_name', 'model_name')}
        return self.repository.update(conversation_id, clean_data)

    def delete(self, conversation_id: int) -> bool:
        """Delete a conversation."""
        return self.repository.delete(conversation_id)
