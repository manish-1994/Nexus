import pytest
from services.conversation_service import ConversationService
from models.conversation import Conversation


class TestConversationService:
    """Tests for ConversationService."""

    def test_create_conversation(self, db_session):
        """Test creating a new conversation."""
        service = ConversationService(db_session)
        conversation = service.create({"title": "Test Conversation"})

        assert conversation.id is not None
        assert conversation.title == "Test Conversation"
        assert conversation.created_at is not None
        assert conversation.updated_at is not None

    def test_create_conversation_with_user_id(self, db_session):
        """Test creating a conversation with user_id."""
        service = ConversationService(db_session)
        conversation = service.create({"title": "User Conversation", "user_id": "user123"})

        assert conversation.user_id == "user123"

    def test_get_conversation(self, db_session):
        """Test getting a conversation by ID."""
        service = ConversationService(db_session)
        created = service.create({"title": "Get Test"})

        retrieved = service.get(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Get Test"

    def test_get_conversation_not_found(self, db_session):
        """Test getting a non-existent conversation."""
        service = ConversationService(db_session)
        result = service.get(999)
        assert result is None

    def test_get_all_conversations(self, db_session):
        """Test getting all conversations."""
        service = ConversationService(db_session)
        service.create({"title": "Conv 1"})
        service.create({"title": "Conv 2"})
        service.create({"title": "Conv 3"})

        conversations = service.get_all()
        assert len(conversations) == 3

    def test_get_all_with_pagination(self, db_session):
        """Test pagination for get_all."""
        service = ConversationService(db_session)
        for i in range(5):
            service.create({"title": f"Conv {i}"})

        # Get first 2
        first_page = service.get_all(skip=0, limit=2)
        assert len(first_page) == 2

        # Get next 2
        second_page = service.get_all(skip=2, limit=2)
        assert len(second_page) == 2

    def test_update_conversation(self, db_session):
        """Test updating a conversation."""
        service = ConversationService(db_session)
        created = service.create({"title": "Original Title"})

        updated = service.update(created.id, {"title": "Updated Title"})
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.id == created.id

    def test_update_conversation_not_found(self, db_session):
        """Test updating a non-existent conversation."""
        service = ConversationService(db_session)
        result = service.update(999, {"title": "New Title"})
        assert result is None

    def test_delete_conversation(self, db_session):
        """Test deleting a conversation."""
        service = ConversationService(db_session)
        created = service.create({"title": "To Delete"})

        result = service.delete(created.id)
        assert result is True

        # Verify deleted
        retrieved = service.get(created.id)
        assert retrieved is None

    def test_delete_conversation_not_found(self, db_session):
        """Test deleting a non-existent conversation."""
        service = ConversationService(db_session)
        result = service.delete(999)
        assert result is False
