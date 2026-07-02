import logging
from typing import Dict, Any, List
from models.provider import Provider
from providers import ProviderRegistry

logger = logging.getLogger("capability_manager")


class CapabilityManager:
    """Detect and manage provider capabilities."""

    CAPABILITY_KEYS = [
        "streaming",
        "vision",
        "embeddings",
        "tools",
        "images",
        "audio",
        "reasoning",
    ]

    def __init__(self, db):
        self.db = db

    def detect_capabilities(self, provider: Provider) -> Dict[str, bool]:
        """Auto-detect provider capabilities."""
        capabilities = {key: False for key in self.CAPABILITY_KEYS}

        provider_class = ProviderRegistry.get(provider.type)
        if not provider_class:
            return capabilities

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we can't run sync
                # Return basic capabilities based on provider type
                return self._default_capabilities(provider)
        except RuntimeError:
            pass

        try:
            instance = self._create_instance(provider)
            models = self._run_sync(instance.list_models())
            capabilities["streaming"] = any(m.get("supports_streaming") for m in models)
            capabilities["vision"] = any(
                "vision" in m.get("name", "").lower() or "multimodal" in m.get("name", "").lower()
                for m in models
            )
            capabilities["tools"] = any(
                m.get("supports_tools") or m.get("supports_function_calling")
                for m in models
            )
        except Exception as exc:
            logger.warning("Capability detection failed: %s", exc)

        return capabilities

    def _default_capabilities(self, provider: Provider) -> Dict[str, bool]:
        """Return default capabilities based on provider type."""
        capabilities = {key: False for key in self.CAPABILITY_KEYS}
        capabilities["streaming"] = True
        if provider.type.value == "gemini":
            capabilities["vision"] = True
            capabilities["tools"] = True
        return capabilities

    def _create_instance(self, provider: Provider):
        """Create provider instance."""
        from utils.security import decrypt_api_key
        api_key = decrypt_api_key(provider.api_key) if provider.api_key else None
        provider_class = ProviderRegistry.get(provider.type)
        if not provider_class:
            raise ValueError(f"Provider type {provider.type} not supported")
        return provider_class(api_key=api_key, base_url=provider.base_url)

    def _run_sync(self, coro):
        """Run async coroutine synchronously."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't run in running loop, return defaults
                return []
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    def save_capabilities(self, provider_id: int, capabilities: Dict[str, bool]):
        """Save capabilities to database."""
        from models.capability import Capability
        from datetime import datetime

        existing = self.db.query(Capability).filter(Capability.provider_id == provider_id).first()
        if existing:
            for key, value in capabilities.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.detected_at = datetime.utcnow().isoformat()
        else:
            cap = Capability(provider_id=provider_id, **capabilities)
            cap.detected_at = datetime.utcnow().isoformat()
            self.db.add(cap)
        self.db.commit()

    def get_capabilities(self, provider_id: int) -> Dict[str, bool]:
        """Get capabilities from database."""
        from models.capability import Capability
        cap = self.db.query(Capability).filter(Capability.provider_id == provider_id).first()
        if not cap:
            return {key: False for key in self.CAPABILITY_KEYS}
        return {key: getattr(cap, key, False) for key in self.CAPABILITY_KEYS}
