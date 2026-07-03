"""Service for agent management operations."""
import logging
import time
from typing import Optional, List, Dict, Any, AsyncGenerator

from sqlalchemy.orm import Session

from models.agent import Agent
from repositories.agent_repository import AgentRepository
from agents.manager import AgentManager
from services.ai_runtime import AIRuntime

logger = logging.getLogger("agent_service")


class AgentService:
    """Service layer for agent CRUD, cloning, and testing."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = AgentRepository(db)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def list_agents(self) -> List[Agent]:
        """List all agents ordered by name."""
        return self.db.query(Agent).order_by(Agent.name).all()

    def get_agent(self, agent_id: int) -> Agent:
        """Get a single agent by ID.

        Raises ValueError if not found.
        """
        agent = self.repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")
        return agent

    def create_agent(self, data: dict) -> Agent:
        """Create a new agent.

        Validates name uniqueness.
        Raises ValueError on validation failure.
        """
        self._validate_name_uniqueness(data.get("name"))

        # If is_default is True, unset any existing default
        if data.get("is_default"):
            self._clear_existing_default()

        return self.repo.create(data)

    def update_agent(self, agent_id: int, data: dict) -> Agent:
        """Update an existing agent.

        Validates name uniqueness if name is being changed.
        Raises ValueError if agent not found or validation fails.
        """
        agent = self.repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")

        # Validate name uniqueness if name is being changed
        if "name" in data and data["name"] != agent.name:
            self._validate_name_uniqueness(data["name"], exclude_id=agent_id)

        # If setting as default, clear existing default
        if data.get("is_default"):
            self._clear_existing_default(exclude_id=agent_id)

        return self.repo.update(agent_id, data)

    def delete_agent(self, agent_id: int) -> bool:
        """Delete an agent.

        Prevents deletion of the default agent.
        Raises ValueError if agent not found or is the default agent.
        """
        agent = self.repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")

        if agent.is_default:
            raise ValueError("Cannot delete the default agent")

        return self.repo.delete(agent_id)

    # ------------------------------------------------------------------
    # Clone
    # ------------------------------------------------------------------

    def clone_agent(self, agent_id: int) -> Agent:
        """Clone an agent with a "(Copy)" suffix.

        Raises ValueError if source agent not found.
        """
        agent = self.repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")

        new_name = f"{agent.name} (Copy)"
        # Ensure unique name
        base_name = new_name
        counter = 1
        while self.repo.find_by_name(new_name):
            new_name = f"{base_name} {counter}"
            counter += 1

        return self.repo.clone(agent_id, new_name)

    # ------------------------------------------------------------------
    # Default agent
    # ------------------------------------------------------------------

    def set_default_agent(self, agent_id: int) -> Agent:
        """Set an agent as the default.

        Raises ValueError if agent not found.
        """
        agent = self.repo.set_default(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")
        return agent

    # ------------------------------------------------------------------
    # Testing
    # ------------------------------------------------------------------

    async def test_agent(
        self,
        agent_id: int,
        message: str,
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Test an agent with a non-streaming request.

        Returns a dict with status, response, latency_ms, provider_id, model.
        Raises ValueError if agent not found or missing provider/model.
        """
        agent = self.repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")

        manager = AgentManager(self.db)
        agent_config = manager.get_agent_config(agent_id)

        eff_provider_id = provider_id or agent_config.get("provider_id")
        eff_model = model or agent_config.get("model")

        if not eff_provider_id:
            raise ValueError(
                "Agent must have a provider configured or a provider_id must be provided."
            )
        if not eff_model:
            raise ValueError(
                "Agent must have a model configured or a model must be provided."
            )

        manager.validate_execution(eff_provider_id, eff_model)

        messages = [{"role": "user", "content": message}]
        messages = manager.build_prompt_for_agent(agent_id, messages)

        runtime = AIRuntime(self.db)

        start_time = time.time()
        response_text = await runtime.chat(
            messages=messages,
            provider_id=eff_provider_id,
            model=eff_model,
        )
        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "status": "success",
            "response": response_text,
            "latency_ms": latency_ms,
            "provider_id": eff_provider_id,
            "model": eff_model,
            "tokens_used": None,
        }

    async def test_agent_stream(
        self,
        agent_id: int,
        message: str,
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Test an agent with a streaming request.

        Yields SSE-formatted chunks.
        Raises ValueError if agent not found or missing provider/model.
        """
        agent = self.repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")

        manager = AgentManager(self.db)
        agent_config = manager.get_agent_config(agent_id)

        eff_provider_id = provider_id or agent_config.get("provider_id")
        eff_model = model or agent_config.get("model")

        if not eff_provider_id:
            raise ValueError(
                "Agent must have a provider configured or a provider_id must be provided."
            )
        if not eff_model:
            raise ValueError(
                "Agent must have a model configured or a model must be provided."
            )

        manager.validate_execution(eff_provider_id, eff_model)

        messages = [{"role": "user", "content": message}]
        messages = manager.build_prompt_for_agent(agent_id, messages)

        runtime = AIRuntime(self.db)

        async for chunk in runtime.stream(
            messages=messages,
            provider_id=eff_provider_id,
            model=eff_model,
        ):
            yield chunk

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_name_uniqueness(
        self, name: Optional[str], exclude_id: Optional[int] = None
    ) -> None:
        """Validate that the agent name is unique.

        Raises ValueError if name is empty or already taken.
        """
        if not name or not name.strip():
            raise ValueError("Agent name cannot be empty")

        existing = self.repo.find_by_name(name.strip())
        if existing and (exclude_id is None or existing.id != exclude_id):
            raise ValueError(f"An agent with the name '{name}' already exists")

    def _clear_existing_default(self, exclude_id: Optional[int] = None) -> None:
        """Unset is_default on all agents except the excluded one."""
        query = self.db.query(Agent).filter(Agent.is_default == True)
        if exclude_id is not None:
            query = query.filter(Agent.id != exclude_id)
        query.update({Agent.is_default: False})
        self.db.commit()
