from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = "bot"
    color: Optional[str] = None
    category: Optional[str] = None
    provider_id: Optional[int] = None
    preferred_model_id: Optional[int] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    context_window: Optional[int] = Field(default=None, ge=1)
    streaming: bool = True
    enabled: bool = True
    is_default: bool = False
    prompt_template: Optional[str] = None
    capabilities: Optional[str] = "[]"
    tools: Optional[str] = "[]"
    default_tools: Optional[str] = "[]"
    memory_enabled: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Agent name cannot be empty")
        return v.strip()


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    provider_id: Optional[int] = None
    preferred_model_id: Optional[int] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    context_window: Optional[int] = Field(default=None, ge=1)
    streaming: Optional[bool] = None
    enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    prompt_template: Optional[str] = None
    capabilities: Optional[str] = None
    tools: Optional[str] = None
    default_tools: Optional[str] = None
    memory_enabled: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Agent name cannot be empty")
            return v.strip()
        return v


class AgentResponse(AgentBase):
    id: int

    class Config:
        from_attributes = True


class AgentTestRequest(BaseModel):
    message: str = "Hello, this is a test."
    provider_id: Optional[int] = None
    model: Optional[str] = None


class AgentTestResponse(BaseModel):
    status: str
    response: Optional[str] = None
    latency_ms: Optional[int] = None
    provider_id: Optional[int] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None
