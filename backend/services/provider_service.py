from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from models.provider import Provider, ProviderType, ProviderStatus
from models.model import Model
from repositories.provider_repository import ProviderRepository
from utils.security import encrypt_api_key, decrypt_api_key
from providers import ProviderRegistry, BaseProvider, HealthStatus


class ProviderService:
    """Service for provider management."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProviderRepository(db)

    def get_all_providers(self) -> List[Provider]:
        """Get all providers."""
        return self.repository.find_all()

    def get_provider_by_id(self, provider_id: int) -> Optional[Provider]:
        """Get provider by ID."""
        return self.repository.find_by_id(provider_id)

    def create_provider(self, data: dict) -> Provider:
        """Create new provider."""
        if data.get("api_key"):
            data["api_key"] = encrypt_api_key(data["api_key"])
        return self.repository.create(data)

    def update_provider(self, provider_id: int, data: dict) -> Optional[Provider]:
        """Update provider."""
        if data.get("api_key"):
            data["api_key"] = encrypt_api_key(data["api_key"])
        return self.repository.update(provider_id, data)

    def delete_provider(self, provider_id: int) -> bool:
        """Delete provider."""
        return self.repository.delete(provider_id)

    async def test_connection(self, provider_id: int) -> Dict[str, Any]:
        """Test provider connection."""
        provider = self.repository.find_by_id(provider_id)
        if not provider:
            raise ValueError("Provider not found")

        provider_class = ProviderRegistry.get(provider.type)
        if not provider_class:
            raise ValueError(f"Provider type {provider.type} not supported")

        api_key = decrypt_api_key(provider.api_key) if provider.api_key else None
        provider_instance = provider_class(api_key=api_key, base_url=provider.base_url)

        status = await provider_instance.health_check()

        provider.health_status = status
        provider.last_checked = datetime.utcnow().isoformat()
        self.db.commit()

        return {
            "status": status,
            "provider": provider.name,
            "message": "Connection successful" if status == HealthStatus.ACTIVE else "Connection failed",
        }

    async def discover_models(self, provider_id: int) -> List[Dict[str, Any]]:
        """Discover models from provider."""
        provider = self.repository.find_by_id(provider_id)
        if not provider:
            raise ValueError("Provider not found")

        provider_class = ProviderRegistry.get(provider.type)
        if not provider_class:
            raise ValueError(f"Provider type {provider.type} not supported")

        api_key = decrypt_api_key(provider.api_key) if provider.api_key else None
        provider_instance = provider_class(api_key=api_key, base_url=provider.base_url)

        models_data = await provider_instance.list_models()

        saved_models = []
        for model_data in models_data:
            model = Model(
                provider_id=provider.id,
                name=model_data["name"],
                display_name=model_data.get("display_name"),
                max_tokens=model_data.get("max_tokens"),
                supports_streaming=model_data.get("supports_streaming", True),
                is_active=True,
                description=model_data.get("description"),
            )
            self.db.add(model)
            saved_models.append(model)

        self.db.commit()
        return [
            {
                "id": m.id,
                "name": m.name,
                "display_name": m.display_name,
                "provider_id": m.provider_id,
                "max_tokens": m.max_tokens,
                "supports_streaming": m.supports_streaming,
                "is_active": m.is_active,
                "description": m.description,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in saved_models
        ]

    def get_models_by_provider(self, provider_id: int) -> List[Model]:
        """Get all models for a provider."""
        return self.db.query(Model).filter(Model.provider_id == provider_id).all()

    def delete_model(self, model_id: int) -> bool:
        """Delete a model."""
        model = self.db.query(Model).filter(Model.id == model_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False
