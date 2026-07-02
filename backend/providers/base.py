from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator
from enum import Enum


class ProviderType(str, Enum):
  """Provider type enumeration."""
  OPENROUTER = "openrouter"
  GROQ = "groq"
  OLLAMA = "ollama"
  GEMINI = "gemini"
  LMSTUDIO = "lmstudio"
  OPENAI_COMPATIBLE = "openai_compatible"


class HealthStatus(str, Enum):
    """Provider health status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CHECKING = "checking"


class BaseProvider(ABC):
    """Abstract base provider class."""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> str:
        """Send chat completion request."""
        pass

    @abstractmethod
    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        pass

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Check provider health."""
        pass

    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        pass

    @abstractmethod
    def get_provider_type(self) -> ProviderType:
        """Get provider type."""
        pass
