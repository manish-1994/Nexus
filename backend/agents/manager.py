import logging
from sqlalchemy.orm import Session
from models.agent import Agent
from models.model import Model
from agents.registry import AgentRegistry
from agents.default import DefaultAgent
from typing import Dict, Any, List

logger = logging.getLogger("agent_manager")

class AgentManager:
    """Manages agent resolution and execution."""

    def __init__(self, db: Session):
        self.db = db
        self.registry = AgentRegistry()

    def resolve_agent(self, agent_id: int) -> DefaultAgent:
        """Resolve an agent by ID.

        Always creates a fresh DefaultAgent bound to the current request's DB session.
        Never reuses cached instances across requests (prevents detached SQLAlchemy objects).
        """
        logger.info("[DEBUG] resolve_agent called agent_id=%s", agent_id)

        agent_model = self.db.query(Agent).filter(Agent.id == agent_id).first()
        logger.info("[DEBUG] resolve_agent DB lookup agent_id=%s found=%s", agent_id, bool(agent_model))
        if not agent_model:
            raise ValueError(f"Agent with ID {agent_id} not found")

        # Instantiate default agent with the current request's DB session
        agent_instance = DefaultAgent(self.db, agent_model)
        logger.info("[DEBUG] resolve_agent created fresh instance agent_id=%s name=%s", agent_id, agent_model.name)
        return agent_instance

    def build_prompt_for_agent(self, agent_id: int, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply system prompt and prepare messages for execution."""
        logger.info("[DEBUG] build_prompt_for_agent called agent_id=%s input_messages_count=%d", agent_id, len(messages))
        agent = self.resolve_agent(agent_id)
        result = agent.buildPrompt(messages)
        logger.info("[DEBUG] build_prompt_for_agent result messages_count=%d", len(result))
        for i, msg in enumerate(result):
            logger.info("[DEBUG] build_prompt_for_agent msg[%d] role=%s content_preview=%s", i, msg.get("role"), (msg.get("content", "") or "")[:80])
        return result

    def get_agent_config(self, agent_id: int) -> Dict[str, Any]:
        """Get configuration (provider, model, etc.) for the agent."""
        logger.info("[DEBUG] get_agent_config called agent_id=%s", agent_id)
        agent = self.resolve_agent(agent_id)
        preferred_model = None
        if agent.agent_model.preferred_model_id:
            preferred_model = self.db.query(Model).filter(Model.id == agent.agent_model.preferred_model_id).first()
        config = {
            "provider_id": agent.agent_model.provider_id,
            "model": preferred_model.name if preferred_model else None,
            "temperature": agent.agent_model.temperature,
            "max_tokens": agent.agent_model.max_tokens,
            "streaming": agent.agent_model.streaming,
            "top_p": agent.agent_model.top_p,
        }
        logger.info("[DEBUG] get_agent_config returning: %s", config)
        return config

    def validate_execution(self, provider_id: int, model: str):
        """Validate that the provider and model are ready for execution."""
        from models.provider import Provider
        provider = self.db.query(Provider).filter(Provider.id == provider_id).first()
        if not provider:
            raise ValueError(f"Provider with ID {provider_id} does not exist.")
        if not provider.is_active:
            raise ValueError(f"Provider {provider.name} is currently disabled.")

        # Validate against the models table, NOT provider.models JSON
        model_record = self.db.query(Model).filter(
            Model.provider_id == provider_id,
            Model.name == model,
            Model.is_active == True,
        ).first()
        if not model_record:
            raise ValueError(f"Model {model} is not available for provider {provider.name}.")
