from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from models.provider import Provider, ProviderType, ProviderStatus
from models.model import Model
from repositories.provider_repository import ProviderRepository
from services.provider_validation_service import ProviderValidationService
from utils.security import encrypt_api_key, decrypt_api_key
from providers import ProviderRegistry, BaseProvider, HealthStatus


class ProviderService:
    """Service for provider management."""

    def __init__(self, db: Session):
      self.db = db
      self.repository = ProviderRepository(db)
      self.validator = ProviderValidationService(db)

    def get_all_providers(self) -> List[Provider]:
        """Get all providers."""
        return self.repository.find_all()

    def get_provider_by_id(self, provider_id: int) -> Optional[Provider]:
        """Get provider by ID."""
        return self.repository.find_by_id(provider_id)

    def create_provider(self, data: dict) -> Provider:
      """Create new provider."""
      self.validator.validate_provider(
        name=data.get("name", ""),
        provider_type=data.get("type", ""),
        base_url=data.get("base_url"),
        api_key=data.get("api_key"),
      )
      if data.get("api_key"):
        data["api_key"] = encrypt_api_key(data["api_key"])
      return self.repository.create(data)

    def update_provider(self, provider_id: int, data: dict) -> Optional[Provider]:
      """Update provider."""
      provider = self.repository.find_by_id(provider_id)
      if not provider:
        raise ValueError("Provider not found")
  
      self.validator.validate_provider(
        name=data.get("name", provider.name),
        provider_type=data.get("type", provider.type),
        base_url=data.get("base_url", provider.base_url),
        api_key=data.get("api_key"),
        exclude_id=provider_id,
      )
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
          model_name = model_data["name"]
          existing_model = self.db.query(Model).filter(
            Model.provider_id == provider.id,
            Model.name == model_name,
          ).first()
      
          model_data_dict = {
            "provider_id": provider.id,
            "name": model_name,
            "display_name": model_data.get("display_name"),
            "max_tokens": model_data.get("max_tokens"),
            "supports_streaming": model_data.get("supports_streaming", True),
            "supports_vision": model_data.get("supports_vision", False),
            "supports_reasoning": model_data.get("supports_reasoning", False),
            "is_deprecated": model_data.get("is_deprecated", False),
            "is_active": True,
            "description": model_data.get("description"),
          }
      
          if existing_model:
            for key, value in model_data_dict.items():
              setattr(existing_model, key, value)
            saved_models.append(existing_model)
          else:
            model = Model(**model_data_dict)
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
  
    def validate_provider_config(self, name: str, provider_type: str, base_url: Optional[str] = None, api_key: Optional[str] = None, exclude_id: Optional[int] = None) -> Dict[str, Any]:
      """Validate provider configuration without creating/updating."""
      try:
        self.validator.validate_provider(
          name=name,
          provider_type=provider_type,
          base_url=base_url,
          api_key=api_key,
          exclude_id=exclude_id,
        )
        return {"valid": True, "errors": []}
      except ValueError as exc:
        return {"valid": False, "errors": [str(exc)]}
