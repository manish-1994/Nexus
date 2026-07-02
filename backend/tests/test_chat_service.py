import pytest
from services.chat_service import ChatService
from models.message import MessageRole
from services.conversation_service import ConversationService
from services.message_service import MessageService


class TestChatService:
    """Tests for ChatService."""

    def test_build_messages_for_provider(self, db_session):
        """Test building messages list for provider API."""
        conv_service = ConversationService(db_session)
        conversation = conv_service.create({"title": "Test Conv"})

        msg_service = MessageService(db_session)
        msg_service.repository.create_message(conversation_id=conversation.id, role=MessageRole.USER, content="User msg")
        msg_service.repository.create_message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content="AI msg")

        service = ChatService(db_session)
        messages = service._build_messages_for_provider(conversation.id)

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "User msg"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "AI msg"

    def test_save_user_message(self, db_session):
        """Test saving a user message."""
        conv_service = ConversationService(db_session)
        conversation = conv_service.create({"title": "Test Conv"})

        service = ChatService(db_session)
        message = service._save_user_message(
            conversation_id=conversation.id,
            content="User message",
            provider="openrouter",
            model="gpt-4",
        )

        assert message.role == MessageRole.USER
        assert message.content == "User message"
        assert message.provider == "openrouter"
        assert message.model == "gpt-4"

    def test_save_assistant_message(self, db_session):
        """Test saving an assistant message."""
        conv_service = ConversationService(db_session)
        conversation = conv_service.create({"title": "Test Conv"})

        service = ChatService(db_session)
        message = service._save_assistant_message(
            conversation_id=conversation.id,
            content="AI response",
            provider="openrouter",
            model="gpt-4",
            tokens_used=100,
        )

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "AI response"
        assert message.tokens_used == 100

    def test_get_conversations(self, db_session):
        """Test getting conversations through ChatService."""
        conv_service = ConversationService(db_session)
        conv_service.create({"title": "Conv 1"})
        conv_service.create({"title": "Conv 2"})

        service = ChatService(db_session)
        conversations = service.get_conversations()

        assert len(conversations) >= 2

    def test_get_conversation(self, db_session):
        """Test getting a single conversation through ChatService."""
        conv_service = ConversationService(db_session)
        created = conv_service.create({"title": "Get Test"})

        service = ChatService(db_session)
        conversation = service.get_conversation(created.id)

        assert conversation is not None
        assert conversation.id == created.id
        assert conversation.title == "Get Test"

    def test_get_messages(self, db_session):
        """Test getting messages through ChatService."""
        conv_service = ConversationService(db_session)
        conversation = conv_service.create({"title": "Test Conv"})

        msg_service = MessageService(db_session)
        msg_service.repository.create_message(conversation_id=conversation.id, role=MessageRole.USER, content="Msg 1")
        msg_service.repository.create_message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content="Msg 2")

        service = ChatService(db_session)
        messages = service.get_messages(conversation.id)

        assert len(messages) == 2
        assert all(m.conversation_id == conversation.id for m in messages)
