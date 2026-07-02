from sqlalchemy.orm import Session
from database import get_db, init_db, Base, engine


def test_database_connection():
    """Test database connection."""
    init_db()
    # Verify tables exist
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert len(tables) > 0


def test_get_db_dependency():
    """Test database dependency."""
    db_gen = get_db()
    db = next(db_gen)
    assert isinstance(db, Session)
    db.close()
