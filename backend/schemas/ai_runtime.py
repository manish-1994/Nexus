from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AIRequest(BaseModel):
    provider_id: Optional[int] = None
    model: Optional[str] = None
    messages: List[Dict[str, Any]]
    stream: bool = False
    requirements: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AIResponse(BaseModel):
    content: str
    model: str
    provider: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost: Optional[float] = None
    finish_reason: Optional[str] = None


class CapabilityResponse(BaseModel):
    provider_id: int
    capabilities: Dict[str, bool]
    detected_at: str
    models_count: int
