"""Repository for agent data access."""
from typing import Optional, List

from sqlalchemy.orm import Session

from models.agent import Agent
from models.base import BaseModel
from repositories.base_repository import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    """Repository for Agent CRUD operations with agent-specific queries."""

    def __init__(self, db: Session):
        super().__init__(Agent, db)

    def find_by_name(self, name: str) -> Optional[Agent]:
        """Find an agent by exact name (case-sensitive)."""
        return self.db.query(Agent).filter(Agent.name == name).first()

    def find_default_agent(self) -> Optional[Agent]:
        """Find the agent marked as default."""
        return self.db.query(Agent).filter(Agent.is_default == True).first()

    def find_enabled(self) -> List[Agent]:
        """Find all enabled agents, ordered by name."""
        return (
            self.db.query(Agent)
            .filter(Agent.enabled == True)
            .order_by(Agent.name)
            .all()
        )

    def clone(self, agent_id: int, new_name: str) -> Optional[Agent]:
        """Clone an agent with a new name.

        Copies all configuration except:
        - id (new auto-generated)
        - is_default (always False for clones)
        - enabled (defaults to True)
        """
        source = self.find_by_id(agent_id)
        if not source:
            return None

        clone_data = {
            "name": new_name,
            "description": source.description,
            "icon": source.icon,
            "color": source.color,
            "category": source.category,
            "provider_id": source.provider_id,
            "preferred_model_id": source.preferred_model_id,
            "temperature": source.temperature,
            "top_p": source.top_p,
            "presence_penalty": source.presence_penalty,
            "frequency_penalty": source.frequency_penalty,
            "max_tokens": source.max_tokens,
            "context_window": source.context_window,
            "streaming": source.streaming,
            "enabled": True,
            "is_default": False,
            "prompt_template": source.prompt_template,
            "capabilities": source.capabilities,
            "tools": source.tools,
            "default_tools": source.default_tools,
            "memory_enabled": source.memory_enabled,
        }

        return self.create(clone_data)

    def set_default(self, agent_id: int) -> Optional[Agent]:
        """Set an agent as the default, unsetting all others.

        Returns the updated agent, or None if not found.
        """
        agent = self.find_by_id(agent_id)
        if not agent:
            return None

        # Unset is_default on all agents
        self.db.query(Agent).filter(Agent.is_default == True).update(
            {Agent.is_default: False}
        )
        # Set is_default on the target agent
        agent.is_default = True
        self.db.commit()
        self.db.refresh(agent)
        return agent
