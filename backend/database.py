from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from config import settings

# Ensure data directory exists
data_dir = Path("./data")
data_dir.mkdir(exist_ok=True)

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.environment == "development",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import all models to ensure they are registered with Base.metadata
    from models import (
        Conversation,
        Message,
        Provider,
        Model,
        Settings,
        Capability,
        Usage,
    )
    Base.metadata.create_all(bind=engine)
