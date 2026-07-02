from pydantic import BaseModel
from schemas.base import BaseSchema


class HealthResponse(BaseSchema):
    """Health check response schema."""
    status: str
    version: str
    database: str
    environment: str
