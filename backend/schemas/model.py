from pydantic import BaseModel
from schemas.base import BaseSchema
from typing import Optional


class ModelBase(BaseSchema):
  name: str
  display_name: Optional[str] = None
  max_tokens: Optional[int] = None
  supports_streaming: bool = True
  supports_vision: bool = False
  supports_reasoning: bool = False
  is_deprecated: bool = False
  description: Optional[str] = None


class ModelCreate(ModelBase):
  provider_id: int


class ModelResponse(ModelBase):
  id: int
  provider_id: int
  is_active: bool
  created_at: str
  updated_at: str

  class Config:
    from_attributes = True
