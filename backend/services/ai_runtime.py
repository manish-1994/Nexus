import logging
from typing import Optional, Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session
from models.provider import Provider, ProviderType
from models.message import MessageRole
from providers import ProviderRegistry
from utils.security import decrypt_api_key
from services.capability_manager import CapabilityManager
from services.usage_tracker import UsageTracker
from services.model_cache import ModelCache

logger = logging.getLogger("ai_runtime")


class AIRuntime:
    """Central gateway for all AI operations."""

    def __init__(self, db: Session):
        self.db = db
        self.capability_manager = CapabilityManager(db)
        self.usage_tracker = UsageTracker(db)
        self.model_cache = ModelCache()

    async def chat(self, messages: list, provider_id: Optional[int] = None, model: Optional[str] = None, **kwargs) -> str:
        """Send chat request through runtime."""
        logger.info("[DEBUG] AIRuntime.chat called provider_id=%s model=%s messages_count=%d kwargs=%s", provider_id, model, len(messages), kwargs)
        provider = self._resolve_provider(provider_id, model, kwargs)
        logger.info("[DEBUG] Final Provider: id=%s name=%s type=%s", provider.id, provider.name, provider.type)
        logger.info("[DEBUG] Final Model: %s", model)
        logger.info("[DEBUG] Final Payload: messages_count=%d provider_id=%s model=%s kwargs=%s", len(messages), provider_id, model, kwargs)
        provider_class = ProviderRegistry.get(provider.type)
        if not provider_class:
            raise ValueError(f"Provider type {provider.type} not supported")
        api_key = decrypt_api_key(provider.api_key) if provider.api_key else None
        custom_headers = self._parse_custom_headers(provider.custom_headers)
        instance_kwargs = {"api_key": api_key, "base_url": provider.base_url}
        if provider.type == ProviderType.OPENAI_COMPATIBLE:
            instance_kwargs["provider_type"] = provider.type.value
            instance_kwargs["timeout"] = provider.timeout
            instance_kwargs["custom_headers"] = custom_headers
        instance = provider_class(**instance_kwargs)
        resolved_model = model or provider.default_model
        if not resolved_model:
            raise ValueError("No model specified and provider has no default model")
        try:
            response = await instance.chat(messages=messages, model=resolved_model, **kwargs)
            self.usage_tracker.track_usage(
                provider_id=provider.id,
                model=resolved_model,
                request_type="chat",
            )
            return response
        except Exception as exc:
            logger.exception("Chat request failed: %s", exc)
            raise

    async def stream(self, messages: list, provider_id: Optional[int] = None, model: Optional[str] = None, conversation_id: Optional[int] = None, **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat request through runtime."""
        logger.info("[DEBUG] AIRuntime.stream called provider_id=%s model=%s messages_count=%d conversation_id=%s kwargs=%s", provider_id, model, len(messages), conversation_id, kwargs)
        provider = self._resolve_provider(provider_id, model, kwargs)
        logger.info("[DEBUG] Final Provider: id=%s name=%s type=%s", provider.id, provider.name, provider.type)
        logger.info("[DEBUG] Final Model: %s", model)
        logger.info("[DEBUG] Final Payload: messages_count=%d provider_id=%s model=%s conversation_id=%s kwargs=%s", len(messages), provider_id, model, conversation_id, kwargs)
        provider_class = ProviderRegistry.get(provider.type)
        if not provider_class:
            raise ValueError(f"Provider type {provider.type} not supported")
        api_key = decrypt_api_key(provider.api_key) if provider.api_key else None
        custom_headers = self._parse_custom_headers(provider.custom_headers)
        instance_kwargs = {"api_key": api_key, "base_url": provider.base_url}
        if provider.type == ProviderType.OPENAI_COMPATIBLE:
            instance_kwargs["provider_type"] = provider.type.value
            instance_kwargs["timeout"] = provider.timeout
            instance_kwargs["custom_headers"] = custom_headers
        instance = provider_class(**instance_kwargs)
        resolved_model = model or provider.default_model
        if not resolved_model:
            raise ValueError("No model specified and provider has no default model")
        full_response = ""
        try:
            async for chunk in instance.stream(messages=messages, model=resolved_model, **kwargs):
                full_response += chunk
                yield chunk
            self.usage_tracker.track_usage(
                provider_id=provider.id,
                model=resolved_model,
                request_type="stream",
            )
            if conversation_id:
                from services.chat_service import ChatService
                chat_service = ChatService(self.db)
                chat_service._save_assistant_message(
                    conversation_id=conversation_id,
                    content=full_response,
                    provider=provider.type,
                    model=resolved_model,
                )
                logger.info("stream assistant message saved conversation_id=%s", conversation_id)
        except Exception as exc:
            logger.exception("Stream request failed: %s", exc)
            raise

    def _resolve_provider(self, provider_id: Optional[int], model: Optional[str], kwargs: Dict[str, Any]) -> Provider:
        """Select provider based on requirements."""
        logger.info("[DEBUG] _resolve_provider called provider_id=%s model=%s", provider_id, model)
        if provider_id:
            provider = self.db.query(Provider).filter(Provider.id == provider_id).first()
            logger.info("[DEBUG] _resolve_provider DB lookup provider_id=%s found=%s", provider_id, bool(provider))
            if not provider:
                raise ValueError(f"Provider {provider_id} not found")
            if not provider.is_active:
                raise ValueError(f"Provider {provider_id} is not active")
            logger.info("[DEBUG] _resolve_provider returning provider id=%s type=%s", provider.id, provider.type)
            return provider
        # Fallback to first active provider
        provider = self.db.query(Provider).filter(Provider.is_active == True).order_by(Provider.priority.desc()).first()
        if not provider:
            raise ValueError("No active provider configured")
        return provider

    def _parse_custom_headers(self, custom_headers: Optional[str]) -> Dict[str, str]:
        """Parse custom headers from JSON string."""
        if not custom_headers:
            return {}
        try:
            import json
            return json.loads(custom_headers)
        except Exception:
            return {}
