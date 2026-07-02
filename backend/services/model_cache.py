import time
import logging
from typing import List, Dict, Any, Optional
from models.provider import Provider
from providers import ProviderRegistry
from utils.security import decrypt_api_key

logger = logging.getLogger("model_cache")


class ModelCache:
    """Cache model metadata with TTL."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self._cache: Dict[int, Dict[str, Any]] = {}

    def get(self, provider_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get models from cache if valid."""
        entry = self._cache.get(provider_id)
        if not entry:
            return None
        if time.time() - entry["timestamp"] > self.ttl:
            del self._cache[provider_id]
            return None
        return entry["models"]

    def set(self, provider_id: int, models: List[Dict[str, Any]]):
        """Store models in cache."""
        self._cache[provider_id] = {
            "models": models,
            "timestamp": time.time(),
        }

    def invalidate(self, provider_id: int):
        """Invalidate cache for a provider."""
        self._cache.pop(provider_id, None)

    def get_or_fetch(self, provider: Provider) -> List[Dict[str, Any]]:
        """Get models from cache or fetch fresh."""
        cached = self.get(provider.id)
        if cached is not None:
            return cached
        models = self._fetch_models(provider)
        self.set(provider.id, models)
        return models

    def _fetch_models(self, provider: Provider) -> List[Dict[str, Any]]:
        """Fetch models from provider."""
        provider_class = ProviderRegistry.get(provider.type)
        if not provider_class:
            return []
        api_key = decrypt_api_key(provider.api_key) if provider.api_key else None
        instance = provider_class(api_key=api_key, base_url=provider.base_url)
        try:
            import asyncio
            return asyncio.run(instance.list_models())
        except Exception as exc:
            logger.warning("Model fetch failed for provider %s: %s", provider.id, exc)
            return []
