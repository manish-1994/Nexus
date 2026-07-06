"""Database schema migration system.

Idempotent migrations that run on application startup.
Each migration is a callable that receives a SQLAlchemy connection
and applies the necessary schema changes.
"""

from __future__ import annotations

import logging
from typing import Callable, List, Tuple

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

logger = logging.getLogger(__name__)

# Migration registry: list of (version, description, migration_func)
# Versions are integers, monotonically increasing.
MIGRATIONS: List[Tuple[int, str, Callable[[Connection], None]]] = []


def register(version: int, description: str):
    """Decorator to register a migration function."""

    def decorator(func: Callable[[Connection], None]):
        MIGRATIONS.append((version, description, func))
        return func

    return decorator


@register(1, "Add preferred_model_id to agents table")
def migration_001_add_preferred_model_id(conn: Connection) -> None:
    """Add preferred_model_id column to agents.

    Note: SQLite does not support ALTER TABLE ... ADD CONSTRAINT,
    so the foreign key is enforced at the SQLAlchemy ORM level.
    For new databases, Base.metadata.create_all() will create the FK.
    """
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("agents")]

    if "preferred_model_id" not in columns:
        logger.info("Adding preferred_model_id column to agents table")
        conn.execute(text("""
            ALTER TABLE agents ADD COLUMN preferred_model_id INTEGER NULL
        """))
    else:
        logger.info("preferred_model_id column already exists, skipping")


@register(2, "Add presence_penalty, frequency_penalty, is_default to agents table")
def migration_002_add_agent_config_columns(conn: Connection) -> None:
    """Add presence_penalty, frequency_penalty, and is_default columns to agents."""
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("agents")]

    if "presence_penalty" not in columns:
        logger.info("Adding presence_penalty column to agents table")
        conn.execute(text("""
            ALTER TABLE agents ADD COLUMN presence_penalty FLOAT DEFAULT 0.0
        """))
    else:
        logger.info("presence_penalty column already exists, skipping")

    if "frequency_penalty" not in columns:
        logger.info("Adding frequency_penalty column to agents table")
        conn.execute(text("""
            ALTER TABLE agents ADD COLUMN frequency_penalty FLOAT DEFAULT 0.0
        """))
    else:
        logger.info("frequency_penalty column already exists, skipping")

    if "is_default" not in columns:
        logger.info("Adding is_default column to agents table")
        conn.execute(text("""
            ALTER TABLE agents ADD COLUMN is_default BOOLEAN DEFAULT 0
        """))
    else:
        logger.info("is_default column already exists, skipping")


@register(3, "Add execution_logs table for agent runtime")
def migration_003_add_execution_logs(conn: Connection) -> None:
    """Create the execution_logs table for tracking agent execution lifecycle."""
    inspector = inspect(conn)
    table_names = inspector.get_table_names()

    if "execution_logs" in table_names:
        logger.info("execution_logs table already exists, skipping")
        return

    logger.info("Creating execution_logs table")
    conn.execute(text("""
        CREATE TABLE execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id VARCHAR(36) NOT NULL UNIQUE,
            agent_id INTEGER NOT NULL REFERENCES agents(id),
            conversation_id INTEGER NULL REFERENCES conversations(id),
            status VARCHAR(20) NOT NULL DEFAULT 'idle',
            provider_id INTEGER NULL REFERENCES providers(id),
            model VARCHAR(255) NULL,
            input_messages TEXT NULL,
            system_prompt TEXT NULL,
            output_response TEXT NULL,
            streaming_chunks INTEGER DEFAULT 0,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            cost FLOAT DEFAULT 0.0,
            latency_ms INTEGER NULL,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            fallback_provider_id INTEGER NULL REFERENCES providers(id),
            fallback_model VARCHAR(255) NULL,
            tool_calls TEXT NULL,
            error_message TEXT NULL,
            error_code VARCHAR(50) NULL,
            created_at DATETIME NOT NULL DEFAULT (datetime('now')),
            started_at DATETIME NULL,
            completed_at DATETIME NULL,
            updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
        )
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_execution_logs_execution_id
        ON execution_logs (execution_id)
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_execution_logs_status
        ON execution_logs (status)
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_execution_logs_agent_id
        ON execution_logs (agent_id)
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_execution_logs_created_at
        ON execution_logs (created_at)
    """))
    logger.info("execution_logs table created successfully")


@register(4, "Add tool_calls column to execution_logs table")
def migration_004_add_tool_calls(conn: Connection) -> None:
    """Add tool_calls JSON column to execution_logs for tracking tool invocations."""
    inspector = inspect(conn)
    table_names = inspector.get_table_names()

    if "execution_logs" not in table_names:
        logger.info("execution_logs table does not exist yet, skipping")
        return

    columns = [col["name"] for col in inspector.get_columns("execution_logs")]

    if "tool_calls" not in columns:
        logger.info("Adding tool_calls column to execution_logs table")
        conn.execute(text("""
            ALTER TABLE execution_logs ADD COLUMN tool_calls TEXT NULL
        """))
    else:
        logger.info("tool_calls column already exists, skipping")


def get_current_schema_version(conn: Connection) -> int:
    """Get the current schema version from the database.

    Returns 0 if the schema_version table does not exist yet.
    """
    inspector = inspect(conn)
    if "schema_version" not in inspector.get_table_names():
        return 0
    result = conn.execute(text("SELECT version FROM schema_version WHERE id = 1"))
    row = result.fetchone()
    return row[0] if row else 0


def run_migrations(conn: Connection) -> None:
    """Run all pending migrations in order.

    This function is idempotent: running it multiple times is safe
    because each migration checks whether its changes are already applied.
    """
    current_version = get_current_schema_version(conn)
    logger.info("Current schema version: %d", current_version)

    pending = [(v, desc, func) for v, desc, func in MIGRATIONS if v > current_version]

    if not pending:
        logger.info("No pending migrations")
        return

    logger.info("Applying %d migration(s)", len(pending))

    # Ensure schema_version table exists before tracking versions
    inspector = inspect(conn)
    if "schema_version" not in inspector.get_table_names():
        conn.execute(text("""
            CREATE TABLE schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """))
        conn.execute(text("INSERT INTO schema_version (id, version) VALUES (1, 0)"))
        conn.commit()
        logger.info("Created schema_version table")

    for version, description, func in sorted(pending, key=lambda x: x[0]):
        logger.info("Applying migration %d: %s", version, description)
        try:
            func(conn)
            conn.execute(
                text("""
                UPDATE schema_version SET version = :version, applied_at = datetime('now')
                WHERE id = 1
            """),
                {"version": version},
            )
            conn.commit()
            logger.info("Migration %d applied successfully", version)
        except Exception as exc:
            conn.rollback()
            logger.error("Migration %d failed: %s", version, exc)
            raise

    final_version = get_current_schema_version(conn)
    logger.info("Schema updated to version %d", final_version)
