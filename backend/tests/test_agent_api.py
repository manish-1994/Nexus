"""Tests for agent API endpoints."""
import pytest
from unittest.mock import AsyncMock, patch


class TestAgentAPI:
    """Tests for agent management API endpoints."""

    # ------------------------------------------------------------------
    # List / Get
    # ------------------------------------------------------------------

    def test_list_agents(self, client):
        """Test listing agents."""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_agent(self, client):
        """Test getting a specific agent."""
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Test Agent", "description": "A test agent"},
        )
        agent_id = create_response.json()["id"]

        response = client.get(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 200
        assert response.json()["id"] == agent_id
        assert response.json()["name"] == "Test Agent"

    def test_get_agent_not_found(self, client):
        """Test getting a non-existent agent."""
        response = client.get("/api/v1/agents/999")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def test_create_agent(self, client):
        """Test creating an agent."""
        response = client.post(
            "/api/v1/agents",
            json={
                "name": "New Agent",
                "description": "A brand new agent",
                "temperature": 0.5,
                "top_p": 0.9,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Agent"
        assert data["temperature"] == 0.5
        assert data["top_p"] == 0.9
        assert "id" in data

    def test_create_agent_empty_name(self, client):
        """Test that empty name is rejected."""
        response = client.post(
            "/api/v1/agents",
            json={"name": "", "description": "Bad agent"},
        )
        assert response.status_code == 422

    def test_create_agent_duplicate_name(self, client):
        """Test that duplicate names are rejected."""
        client.post("/api/v1/agents", json={"name": "Unique Agent"})
        response = client.post(
            "/api/v1/agents",
            json={"name": "Unique Agent"},
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_agent_temperature_out_of_range(self, client):
        """Test that temperature > 2 is rejected."""
        response = client.post(
            "/api/v1/agents",
            json={"name": "Hot Agent", "temperature": 3.0},
        )
        assert response.status_code == 422

    def test_create_agent_top_p_out_of_range(self, client):
        """Test that top_p > 1 is rejected."""
        response = client.post(
            "/api/v1/agents",
            json={"name": "TopP Agent", "top_p": 1.5},
        )
        assert response.status_code == 422

    def test_create_agent_with_new_fields(self, client):
        """Test creating an agent with presence_penalty and frequency_penalty."""
        response = client.post(
            "/api/v1/agents",
            json={
                "name": "Penalty Agent",
                "presence_penalty": 0.5,
                "frequency_penalty": -0.5,
                "is_default": False,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["presence_penalty"] == 0.5
        assert data["frequency_penalty"] == -0.5
        assert data["is_default"] is False

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def test_update_agent(self, client):
        """Test updating an agent."""
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Original Name"},
        )
        agent_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/agents/{agent_id}",
            json={"name": "Updated Name", "temperature": 1.2},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        assert response.json()["temperature"] == 1.2

    def test_update_agent_not_found(self, client):
        """Test updating a non-existent agent."""
        response = client.patch("/api/v1/agents/999", json={"name": "Nope"})
        assert response.status_code == 404

    def test_update_agent_partial(self, client):
        """Test partial update only changes specified fields."""
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Partial Agent", "temperature": 0.7, "top_p": 1.0},
        )
        agent_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/agents/{agent_id}",
            json={"temperature": 0.3},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["temperature"] == 0.3
        assert data["top_p"] == 1.0  # unchanged

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def test_delete_agent(self, client):
        """Test deleting an agent."""
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Delete Me"},
        )
        agent_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/agents/{agent_id}")
        assert get_response.status_code == 404

    def test_delete_agent_not_found(self, client):
        """Test deleting a non-existent agent."""
        response = client.delete("/api/v1/agents/999")
        assert response.status_code == 400

    def test_delete_default_agent_fails(self, client):
        """Test that the default agent cannot be deleted."""
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Default Agent", "is_default": True},
        )
        agent_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 400
        assert "default" in response.json()["detail"].lower()

    # ------------------------------------------------------------------
    # Clone
    # ------------------------------------------------------------------

    def test_clone_agent(self, client):
        """Test cloning an agent."""
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Clone Source", "description": "Original", "temperature": 0.8},
        )
        agent_id = create_response.json()["id"]

        response = client.post(f"/api/v1/agents/{agent_id}/clone")
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Clone Source (Copy)"
        assert data["description"] == "Original"
        assert data["temperature"] == 0.8
        assert data["id"] != agent_id
        assert data["is_default"] is False

    def test_clone_agent_not_found(self, client):
        """Test cloning a non-existent agent."""
        response = client.post("/api/v1/agents/999/clone")
        assert response.status_code == 404

    def test_clone_agent_unique_name(self, client):
        """Test that cloning produces a unique name."""
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Unique Clone Source"},
        )
        agent_id = create_response.json()["id"]

        # Clone once
        clone1 = client.post(f"/api/v1/agents/{agent_id}/clone")
        assert clone1.status_code == 201
        assert clone1.json()["name"] == "Unique Clone Source (Copy)"

        # Clone again - should get a different name
        clone2 = client.post(f"/api/v1/agents/{agent_id}/clone")
        assert clone2.status_code == 201
        assert clone2.json()["name"] != clone1.json()["name"]

    # ------------------------------------------------------------------
    # Set Default
    # ------------------------------------------------------------------

    def test_set_default_agent(self, client):
        """Test setting an agent as default."""
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Future Default"},
        )
        agent_id = create_response.json()["id"]

        response = client.patch(f"/api/v1/agents/{agent_id}/default")
        assert response.status_code == 200
        assert response.json()["is_default"] is True

    def test_set_default_unsets_previous(self, client):
        """Test that setting a new default unsets the previous one."""
        create1 = client.post("/api/v1/agents", json={"name": "First Default", "is_default": True})
        first_id = create1.json()["id"]

        create2 = client.post("/api/v1/agents", json={"name": "Second Agent"})
        second_id = create2.json()["id"]

        # Set second as default
        response = client.patch(f"/api/v1/agents/{second_id}/default")
        assert response.status_code == 200
        assert response.json()["is_default"] is True

        # Verify first is no longer default
        first_response = client.get(f"/api/v1/agents/{first_id}")
        assert first_response.json()["is_default"] is False

    def test_set_default_agent_not_found(self, client):
        """Test setting a non-existent agent as default."""
        response = client.patch("/api/v1/agents/999/default")
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # Test (non-streaming, mocked)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_test_agent_mocked(self, client):
        """Test the agent test endpoint with mocked AIRuntime."""
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Testable Agent", "provider_id": 1},
        )
        agent_id = create_response.json()["id"]

        with patch(
            "services.agent_service.AIRuntime.chat",
            new_callable=AsyncMock,
            return_value="Mocked response",
        ):
            with patch(
                "agents.manager.AgentManager.validate_execution",
                return_value=None,
            ):
                with patch(
                    "agents.manager.AgentManager.build_prompt_for_agent",
                    return_value=[{"role": "user", "content": "Hello"}],
                ):
                    with patch(
                        "agents.manager.AgentManager.get_agent_config",
                        return_value={"provider_id": 1, "model": "test-model"},
                    ):
                        response = client.post(
                            f"/api/v1/agents/{agent_id}/test",
                            json={"message": "Hello", "provider_id": 1, "model": "test-model"},
                        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["response"] == "Mocked response"
        assert "latency_ms" in data
        assert data["provider_id"] == 1
        assert data["model"] == "test-model"

    def test_test_agent_not_found(self, client):
        """Test testing a non-existent agent."""
        response = client.post(
            "/api/v1/agents/999/test",
            json={"message": "Hello"},
        )
        assert response.status_code == 400
