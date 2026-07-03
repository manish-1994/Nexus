"""Database schema migration system.

Idempotent migrations that run on application startup.
Each migration is a callable that receives a SQLAlchemy connection
and applies the necessary schema changes.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

logger = logging.getLogger(__name__)

# Migration registry: list of (version, description, migration_func)
# Versions are integers, monotonically increasing.
MIGRATIONS: List[Tuple[int, str, callable]] = []


def register(version: int, description: str):
    """Decorator to register a migration function."""
    def decorator(func: callable):
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
            conn.execute(text("""
                UPDATE schema_version SET version = :version, applied_at = datetime('now')
                WHERE id = 1
            """), {"version": version})
            conn.commit()
            logger.info("Migration %d applied successfully", version)
        except Exception as exc:
            conn.rollback()
            logger.error("Migration %d failed: %s", version, exc)
            raise

    final_version = get_current_schema_version(conn)
    logger.info("Schema updated to version %d", final_version)
