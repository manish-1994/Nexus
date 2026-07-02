import pytest
from fastapi.testclient import TestClient


class TestChatAPI:
    """Tests for chat API endpoints."""

    def test_list_conversations(self, client):
        """Test listing conversations."""
        response = client.get("/api/v1/conversations")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_conversation(self, client):
        """Test creating a conversation."""
        response = client.post(
            "/api/v1/conversations",
            json={"title": "API Test Conversation"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "API Test Conversation"
        assert "id" in data
        assert "created_at" in data

    def test_get_conversation(self, client):
        """Test getting a specific conversation."""
        create_response = client.post(
            "/api/v1/conversations",
            json={"title": "Get Test"},
        )
        conversation_id = create_response.json()["id"]

        response = client.get(f"/api/v1/conversations/{conversation_id}")
        assert response.status_code == 200
        assert response.json()["id"] == conversation_id

    def test_get_conversation_not_found(self, client):
        """Test getting a non-existent conversation."""
        response = client.get("/api/v1/conversations/999")
        assert response.status_code == 404

    def test_update_conversation(self, client):
        """Test updating a conversation."""
        create_response = client.post(
            "/api/v1/conversations",
            json={"title": "Original"},
        )
        conversation_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/conversations/{conversation_id}",
            json={"title": "Updated"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    def test_update_conversation_not_found(self, client):
        """Test updating a non-existent conversation."""
        response = client.put(
            "/api/v1/conversations/999",
            json={"title": "Updated"},
        )
        assert response.status_code == 404

    def test_delete_conversation(self, client):
        """Test deleting a conversation."""
        create_response = client.post(
            "/api/v1/conversations",
            json={"title": "To Delete"},
        )
        conversation_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/conversations/{conversation_id}")
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/conversations/{conversation_id}")
        assert get_response.status_code == 404

    def test_delete_conversation_not_found(self, client):
        """Test deleting a non-existent conversation."""
        response = client.delete("/api/v1/conversations/999")
        assert response.status_code == 404

    def test_get_messages(self, client):
        """Test getting messages for a conversation."""
        create_response = client.post(
            "/api/v1/conversations",
            json={"title": "Messages Test"},
        )
        conversation_id = create_response.json()["id"]

        response = client.get(f"/api/v1/conversations/{conversation_id}/messages")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_messages_not_found(self, client):
        """Test getting messages for a non-existent conversation."""
        response = client.get("/api/v1/conversations/999/messages")
        # Returns empty list for non-existent conversation
        assert response.status_code == 200
        assert response.json() == []

    def test_send_message_streaming(self, client):
        """Test sending a message with streaming."""
        create_response = client.post(
            "/api/v1/conversations",
            json={"title": "Stream Test"},
        )
        conversation_id = create_response.json()["id"]

        response = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conversation_id,
                "content": "Hello",
                "provider_id": 1,
                "model": "gpt-4",
                "stream": True,
            },
        )
        assert response.status_code in [400, 422, 500]

    def test_send_message_non_streaming(self, client):
        """Test sending a message without streaming."""
        create_response = client.post(
            "/api/v1/conversations",
            json={"title": "Non-Stream Test"},
        )
        conversation_id = create_response.json()["id"]

        response = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": conversation_id,
                "content": "Hello",
                "provider_id": 1,
                "model": "gpt-4",
                "stream": False,
            },
        )
        assert response.status_code in [400, 422, 500]

    def test_send_message_missing_fields(self, client):
        """Test sending a message with missing required fields."""
        response = client.post(
            "/api/v1/chat",
            json={"content": "Hello"},
        )
        assert response.status_code == 422

    def test_send_message_invalid_conversation(self, client):
        """Test sending a message to a non-existent conversation."""
        response = client.post(
            "/api/v1/chat",
            json={
                "conversation_id": 999,
                "content": "Hello",
                "provider_id": 1,
                "model": "gpt-4",
                "stream": True,
            },
        )
        assert response.status_code in [400, 404, 422, 500]
