from sqlalchemy import Column, String, Boolean, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel

class Agent(BaseModel):
    """Agent model representing an AI persona."""
    __tablename__ = "agents"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    preferred_model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, nullable=True)
    streaming = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True)
    color = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)
    top_p = Column(Float, default=1.0)
    presence_penalty = Column(Float, default=0.0)
    frequency_penalty = Column(Float, default=0.0)
    context_window = Column(Integer, nullable=True)
    prompt_template = Column(Text, nullable=True)
    capabilities = Column(Text, nullable=True) # JSON string of AgentCapability metadata
    tools = Column(Text, nullable=True) # JSON string
    default_tools = Column(Text, nullable=True) # JSON string placeholder
    memory_enabled = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)

    provider = relationship("Provider")
    preferred_model = relationship("Model")
