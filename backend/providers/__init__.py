from typing import Dict, Type, Optional
from .base import BaseProvider, ProviderType, HealthStatus
from .openai_compatible import OpenAICompatibleProvider
from .gemini import GeminiProvider
from .groq import GroqProvider
from .openrouter import OpenRouterProvider
from .ollama import OllamaProvider
from .lmstudio import LMStudioProvider

class ProviderRegistry:
  """Registry for provider implementations."""
  _providers: Dict[ProviderType, Type[BaseProvider]] = {}

  @classmethod
  def register(cls, provider_type: ProviderType, provider_class: Type[BaseProvider]):
    """Register a provider implementation."""
    cls._providers[provider_type] = provider_class

  @classmethod
  def get(cls, provider_type: ProviderType) -> Optional[Type[BaseProvider]]:
    """Get provider implementation."""
    return cls._providers.get(provider_type)

  @classmethod
  def get_all(cls) -> Dict[ProviderType, Type[BaseProvider]]:
    """Get all registered providers."""
    return cls._providers.copy()

def _register_providers():
  """Register all provider implementations."""
  ProviderRegistry.register(ProviderType.OPENAI_COMPATIBLE, OpenAICompatibleProvider)
  ProviderRegistry.register(ProviderType.GEMINI, GeminiProvider)
  ProviderRegistry.register(ProviderType.GROQ, GroqProvider)
  ProviderRegistry.register(ProviderType.OPENROUTER, OpenRouterProvider)
  ProviderRegistry.register(ProviderType.OLLAMA, OllamaProvider)
  ProviderRegistry.register(ProviderType.LMSTUDIO, LMStudioProvider)

# Auto-register providers on import
_register_providers()
