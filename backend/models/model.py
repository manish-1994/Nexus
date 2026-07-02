from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Model(BaseModel):
    """AI Model model."""
    __tablename__ = "models"

    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    max_tokens = Column(Integer, nullable=True)
    supports_streaming = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    provider = relationship("Provider", back_populates="models")
