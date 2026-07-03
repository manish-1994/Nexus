from pydantic import BaseModel
from typing import Dict, Any, Optional

class AgentCapability(BaseModel):
    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}
