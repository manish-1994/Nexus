from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Usage(BaseModel):
    """AI usage tracking."""
    __tablename__ = "usages"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    model = Column(String(255), nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    request_type = Column(String(50), nullable=False)
    created_at = Column(String(50), nullable=True)

    provider = relationship("Provider", back_populates="usages")
