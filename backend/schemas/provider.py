from pydantic import BaseModel, ConfigDict, field_serializer, field_validator
from datetime import datetime
from schemas.base import BaseSchema
from typing import Optional, List, Dict, Any

class ProviderBase(BaseSchema):
    name: str
    type: str
    base_url: Optional[str] = None
    is_active: bool = True
    default_model: Optional[str] = None
    timeout: int = 60
    priority: int = 0
    max_retries: int = 3
    organization_id: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Provider name cannot be empty')
        if len(v) > 255:
            raise ValueError('Provider name must be 255 characters or less')
        return v

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.strip():
            return None
        return v

class ProviderCreate(ProviderBase):
    api_key: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None

class ProviderUpdate(BaseSchema):
    name: Optional[str] = None
    type: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None
    default_model: Optional[str] = None
    timeout: Optional[int] = None
    priority: Optional[int] = None
    max_retries: Optional[int] = None
    organization_id: Optional[str] = None
    api_key: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None

class ProviderResponse(ProviderBase):
    id: int
    health_status: str
    last_checked: Optional[str] = None
    error_message: Optional[str] = None
    capabilities: Optional[Dict[str, bool]] = None
    created_at: datetime
    updated_at: datetime
    models: List["ModelResponse"] = []

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime fields to ISO format strings."""
        return value.isoformat() if value else ""

class ModelBase(BaseSchema):
    name: str
    display_name: Optional[str] = None
    max_tokens: Optional[int] = None
    supports_streaming: bool = True
    description: Optional[str] = None

class ModelCreate(ModelBase):
    provider_id: int

class ModelResponse(ModelBase):
    id: int
    provider_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime fields to ISO format strings."""
        return value.isoformat() if value else ""
