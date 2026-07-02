from sqlalchemy import Column, Integer, String, Text
from models.base import BaseModel


class Settings(BaseModel):
    """Application settings model."""
    __tablename__ = "settings"

    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
