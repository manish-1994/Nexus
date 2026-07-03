from sqlalchemy import Column, Integer, String, Boolean, Enum, Text
import enum
from sqlalchemy.orm import relationship
from models.base import BaseModel


class ProviderType(str, enum.Enum):
    OPENAI_COMPATIBLE = "openai_compatible"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    NVIDIA_NIM = "nvidia_nim"
    AZURE_OPENAI = "azure_openai"
    MISTRAL = "mistral"
    TOGETHER_AI = "together_ai"
    DEEPSEEK = "deepseek"
    COHERE = "cohere"
    XAI = "xai"
    PERPLEXITY = "perplexity"
    CUSTOM = "custom"


class ProviderStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CHECKING = "checking"


class Provider(BaseModel):
    """Provider model."""
    __tablename__ = "providers"

    name = Column(String(255), nullable=False)
    type = Column(Enum(ProviderType), nullable=False)
    api_key = Column(Text, nullable=True)
    base_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    health_status = Column(Enum(ProviderStatus), default=ProviderStatus.CHECKING, nullable=False)
    last_checked = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    default_model = Column(String(255), nullable=True)
    timeout = Column(Integer, default=60)
    priority = Column(Integer, default=0)
    custom_headers = Column(Text, nullable=True)
    max_retries = Column(Integer, default=3)
    organization_id = Column(String(255), nullable=True)
    capabilities = Column(Text, nullable=True)

    # Relationships
    models = relationship("Model", back_populates="provider", cascade="all, delete-orphan")
    capabilities_rel = relationship("Capability", back_populates="provider", cascade="all, delete-orphan")
    usages = relationship("Usage", back_populates="provider", cascade="all, delete-orphan")
