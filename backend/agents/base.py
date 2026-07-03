from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from models.agent import Agent

class BaseAgent(ABC):
    """Abstract base class for agents."""

    def __init__(self, db: Session, agent_model: Agent):
        self.db = db
        self.agent_model = agent_model
        
    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], provider_id: Optional[int] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """Execute a non-streaming chat request."""
        pass
        
    @abstractmethod
    async def stream(self, messages: List[Dict[str, Any]], provider_id: Optional[int] = None, model: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Execute a streaming chat request."""
        pass

    @abstractmethod
    def buildPrompt(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Construct the prompt messages, injecting system prompts."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate agent configuration."""
        pass

    @abstractmethod
    def getCapabilities(self) -> List[str]:
        """Get agent capabilities."""
        pass
