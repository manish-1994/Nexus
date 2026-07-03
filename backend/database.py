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


def run_startup_migrations() -> None:
    """Run schema migrations before any model queries.

    This ensures the database schema is up-to-date with the Python models
    before any queries or seeding occurs.
    """
    from migrations import run_migrations

    with engine.connect() as conn:
        run_migrations(conn)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_agents(db):
    from models import Agent
    import json
    
    default_agents = [
        {
            "name": "Assistant",
            "description": "A helpful general-purpose AI assistant.",
            "icon": "bot",
            "color": "blue",
            "category": "General",
            "top_p": 1.0,
            "prompt_template": "You are a helpful and friendly AI assistant.\n\nContext:\nToday is {{today}}.\nUser: {{user}}",
        },
        {
            "name": "Coding",
            "description": "Expert in software development and programming.",
            "icon": "code",
            "color": "green",
            "category": "Development",
            "top_p": 0.1,
            "prompt_template": "You are an expert programmer. Provide clean, efficient, and well-documented code.\n\nWorkspace Files:\n{{files}}",
        },
        {
            "name": "Research",
            "description": "Thorough researcher that cites sources.",
            "icon": "search",
            "color": "purple",
            "category": "Analysis",
            "top_p": 0.5,
            "prompt_template": "You are a meticulous researcher. Provide detailed, well-structured, and factual answers.\n\nMemory:\n{{memory}}",
        },
        {
            "name": "Writing",
            "description": "Creative writer and copyeditor.",
            "icon": "pen-tool",
            "color": "orange",
            "category": "Content",
            "top_p": 0.9,
            "prompt_template": "You are a skilled writer. Help the user draft, refine, and polish their text.",
        },
        {
            "name": "Planner",
            "description": "Helps organize tasks and project plans.",
            "icon": "list",
            "color": "red",
            "category": "Management",
            "top_p": 0.3,
            "prompt_template": "You are a project planner. Break down complex tasks into actionable steps.\n\nConversation:\n{{conversation}}",
        }
    ]
    
    if db.query(Agent).count() == 0:
        for agent_data in default_agents:
            agent = Agent(
                name=agent_data["name"],
                description=agent_data["description"],
                icon=agent_data["icon"],
                color=agent_data["color"],
                category=agent_data["category"],
                top_p=agent_data["top_p"],
                prompt_template=agent_data["prompt_template"],
                capabilities=json.dumps([]),
                tools=json.dumps([]),
                default_tools=json.dumps([]),
                streaming=True,
                enabled=True,
                memory_enabled=False,
            )
            db.add(agent)
        db.commit()


def init_db():
    """Initialize database tables."""
    # Run migrations FIRST — schema must be current before any queries
    run_startup_migrations()

    # Import all models to ensure they are registered with Base.metadata
    from models import (
        Conversation,
        Message,
        Provider,
        Model,
        Settings,
        Capability,
        Usage,
        Agent,
    )
    Base.metadata.create_all(bind=engine)

    # Seed agents
    db = SessionLocal()
    try:
        seed_agents(db)
    finally:
        db.close()
