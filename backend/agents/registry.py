from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from agents.base import BaseAgent

class AgentRegistry:
    """Registry for active agents."""
    
    _instance = None
    _agents: Dict[int, BaseAgent] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance._agents = {}
        return cls._instance

    def register(self, agent_id: int, agent_instance: BaseAgent):
        """Register an agent instance."""
        self._agents[agent_id] = agent_instance

    def unregister(self, agent_id: int):
        """Unregister an agent instance."""
        if agent_id in self._agents:
            del self._agents[agent_id]

    def getAgent(self, agent_id: int) -> Optional[BaseAgent]:
        """Get a registered agent instance."""
        return self._agents.get(agent_id)

    def getAll(self) -> List[BaseAgent]:
        """Get all registered agent instances."""
        return list(self._agents.values())

    def getByCapability(self, capability: str) -> List[BaseAgent]:
        """Get agents by capability."""
        return [
            agent for agent in self._agents.values()
            if capability in agent.getCapabilities()
        ]
