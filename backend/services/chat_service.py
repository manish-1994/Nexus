from typing import List, Optional, Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session
from datetime import datetime
from models.conversation import Conversation
from models.message import Message, MessageRole
from repositories.conversation_repository import ConversationRepository
from repositories.message_repository import MessageRepository
from providers import ProviderRegistry, BaseProvider, HealthStatus
from utils.security import decrypt_api_key
import logging


class ChatService:
    """Service for chat operations."""
    logger = logging.getLogger("chat")

    def __init__(self, db: Session):
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)

    def get_conversations(self, user_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get all conversations."""
        if user_id:
            return self.conversation_repo.find_by_user_id(user_id, skip=skip, limit=limit)
        return self.conversation_repo.find_all(skip=skip, limit=limit)

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """Get a single conversation by ID."""
        return self.conversation_repo.find_by_id(conversation_id)

    def create_conversation(self, title: str = "New Conversation", user_id: Optional[str] = None) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(title=title, user_id=user_id)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def update_conversation(self, conversation_id: int, title: str) -> Optional[Conversation]:
        """Update conversation title."""
        conversation = self.conversation_repo.find_by_id(conversation_id)
        if not conversation:
            return None
        conversation.title = title
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation."""
        return self.conversation_repo.delete(conversation_id)

    def get_messages(self, conversation_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        """Get messages for a conversation."""
        return self.message_repo.find_by_conversation_id(conversation_id, skip=skip, limit=limit)

    def _save_user_message(self, conversation_id: int, content: str, provider: Optional[str] = None, model: Optional[str] = None) -> Message:
        """Save user message to database."""
        return self.message_repo.create_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            provider=provider,
            model=model,
        )

    def _save_assistant_message(self, conversation_id: int, content: str, provider: str, model: str, tokens_used: Optional[int] = None) -> Message:
        """Save assistant message to database."""
        return self.message_repo.create_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            provider=provider,
            model=model,
            tokens_used=tokens_used,
        )

    async def send_message(self, conversation_id: int, content: str, provider_id: int, model: str, stream: bool = True) -> Dict[str, Any]:
        """Send a message and get AI response."""
        # Save user message
        from models.provider import Provider
        provider = self.db.query(Provider).filter(Provider.id == provider_id).first()
        if not provider:
            raise ValueError("Provider not found")
        self._save_user_message(conversation_id, content, provider=provider.type, model=model)
    
        # Update conversation timestamp
        conversation = self.conversation_repo.find_by_id(conversation_id)
        if conversation:
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
    
        # Build messages list
        messages = self._build_messages_for_provider(conversation_id)
    
        if stream:
            # Return streaming config for backend to execute
            return {
                "stream": True,
                "conversation_id": conversation_id,
                "provider": provider.type,
                "model": model,
                "provider_id": provider_id,
                "messages": messages,
            }
        else:
            # Non-streaming via AI Runtime
            from services.ai_runtime import AIRuntime
            runtime = AIRuntime(self.db)
            response = runtime.chat(messages=messages, provider_id=provider_id, model=model)
            assistant_message = self._save_assistant_message(conversation_id, response, provider=provider.type, model=model)
            return {
                "stream": False,
                "conversation_id": conversation_id,
                "message": {
                    "id": assistant_message.id,
                    "role": assistant_message.role,
                    "content": assistant_message.content,
                    "provider": assistant_message.provider,
                    "model": assistant_message.model,
                    "tokens_used": assistant_message.tokens_used,
                    "created_at": assistant_message.created_at.isoformat() if assistant_message.created_at else None,
                },
            }

    async def stream_message(self, conversation_id: int, content: str, provider_id: int, model: str) -> AsyncGenerator[str, None]:
        """Stream AI response."""
        self.logger.info("stream_message started conversation_id=%s provider_id=%s model=%s", conversation_id, provider_id, model)
        # User message already saved by send_message()
        from models.provider import Provider
        provider = self.db.query(Provider).filter(Provider.id == provider_id).first()
        if not provider:
            self.logger.error("stream_message provider not found provider_id=%s", provider_id)
            raise ValueError("Provider not found")

        # Update conversation timestamp
        conversation = self.conversation_repo.find_by_id(conversation_id)
        if conversation:
            conversation.updated_at = datetime.utcnow()
            self.db.commit()

        # Get provider
        provider_class = ProviderRegistry.get(provider.type)
        if not provider_class:
            self.logger.error("stream_message provider class not found type=%s", provider.type)
            raise ValueError(f"Provider type {provider.type} not supported")

        api_key = decrypt_api_key(provider.api_key) if provider.api_key else None
        provider_instance = provider_class(api_key=api_key, base_url=provider.base_url)
        self.logger.info("stream_message provider instance created type=%s", provider.type)

        # Build messages
        messages = self._build_messages_for_provider(conversation_id)
        self.logger.info("stream_message messages built count=%s", len(messages))

        # Stream response
        full_response = ""
        self.logger.info("stream_message starting provider.stream")
        async for chunk in provider_instance.stream(messages=messages, model=model):
            self.logger.info("stream_message chunk received len=%s", len(chunk))
            full_response += chunk
            yield chunk

        self.logger.info("stream_message provider.stream completed")
        # Save complete assistant message
        self._save_assistant_message(conversation_id, full_response, provider=provider.type, model=model)
        self.logger.info("stream_message assistant message saved")

    def _build_messages_for_provider(self, conversation_id: int) -> List[Dict[str, str]]:
        """Build messages list for provider API."""
        messages = self.get_messages(conversation_id)
        formatted = []
        for msg in messages:
            formatted.append({"role": msg.role.value, "content": msg.content})
        return formatted
