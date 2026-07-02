from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @field_validator("created_at", "updated_at", mode="before", check_fields=False)
    def convert_datetime_to_str(cls, value):
        """Convert datetime objects to ISO format strings."""
        if isinstance(value, datetime):
            return value.isoformat()
        return value
