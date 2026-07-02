import pytest
from services.message_service import MessageService
from models.message import Message, MessageRole
from models.conversation import Conversation
from services.conversation_service import ConversationService
from repositories.message_repository import MessageRepository


class TestMessageService:
    """Tests for MessageService."""

    def test_create_message(self, db_session):
        """Test creating a message."""
        # Create conversation first
        conv_service = ConversationService(db_session)
        conversation = conv_service.create({"title": "Test Conv"})

        service = MessageService(db_session)
        message = service.repository.create_message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Hello, world!",
        )

        assert message.id is not None
        assert message.conversation_id == conversation.id
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
        assert message.created_at is not None

    def test_create_message_with_metadata(self, db_session):
        """Test creating a message with provider and model."""
        conv_service = ConversationService(db_session)
        conversation = conv_service.create({"title": "Test Conv"})

        service = MessageService(db_session)
        message = service.repository.create_message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="AI response",
            provider="openrouter",
            model="gpt-4",
            tokens_used=150,
        )

        assert message.provider == "openrouter"
        assert message.model == "gpt-4"
        assert message.tokens_used == 150

    def test_get_message(self, db_session):
        """Test getting a message by ID."""
        conv_service = ConversationService(db_session)
        conversation = conv_service.create({"title": "Test Conv"})

        service = MessageService(db_session)
        created = service.repository.create_message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Test message",
        )

        retrieved = service.get(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.content == "Test message"

    def test_get_message_not_found(self, db_session):
        """Test getting a non-existent message."""
        service = MessageService(db_session)
        result = service.get(999)
        assert result is None

    def test_find_by_conversation_id(self, db_session):
        """Test finding messages by conversation ID."""
        conv_service = ConversationService(db_session)
        conversation = conv_service.create({"title": "Test Conv"})

        service = MessageService(db_session)
        service.repository.create_message(conversation_id=conversation.id, role=MessageRole.USER, content="Msg 1")
        service.repository.create_message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content="Msg 2")
        service.repository.create_message(conversation_id=conversation.id, role=MessageRole.USER, content="Msg 3")

        messages = service.find_by_conversation_id(conversation.id)
        assert len(messages) == 3
        assert all(m.conversation_id == conversation.id for m in messages)

    def test_find_by_conversation_id_with_pagination(self, db_session):
        """Test pagination for find_by_conversation_id."""
        conv_service = ConversationService(db_session)
        conversation = conv_service.create({"title": "Test Conv"})

        service = MessageService(db_session)
        for i in range(5):
            service.repository.create_message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=f"Msg {i}",
            )

        # Get first 2
        first_page = service.find_by_conversation_id(conversation.id, skip=0, limit=2)
        assert len(first_page) == 2

        # Get next 2
        second_page = service.find_by_conversation_id(conversation.id, skip=2, limit=2)
        assert len(second_page) == 2

    def test_get_all_messages(self, db_session):
        """Test getting all messages."""
        conv_service = ConversationService(db_session)
        conversation = conv_service.create({"title": "Test Conv"})

        service = MessageService(db_session)
        service.repository.create_message(conversation_id=conversation.id, role=MessageRole.USER, content="Msg 1")
        service.repository.create_message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content="Msg 2")

        all_messages = service.get_all()
        assert len(all_messages) >= 2
