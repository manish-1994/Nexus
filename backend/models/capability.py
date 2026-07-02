from sqlalchemy import Column, Integer, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Capability(BaseModel):
    """Provider capability cache."""
    __tablename__ = "capabilities"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False, unique=True)
    streaming = Column(Boolean, default=False)
    vision = Column(Boolean, default=False)
    embeddings = Column(Boolean, default=False)
    tools = Column(Boolean, default=False)
    images = Column(Boolean, default=False)
    audio = Column(Boolean, default=False)
    reasoning = Column(Boolean, default=False)
    detected_at = Column(String(50), nullable=True)

    provider = relationship("Provider", back_populates="capabilities_rel")
