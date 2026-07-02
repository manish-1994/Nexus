from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # Project
    project_name: str = "NEXUS V3"
    version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite:///./data/nexus.db"

    # Security
    secret_key: str = "change-me-in-production"
    api_key_encryption_key: str = "change-me-in-production"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
