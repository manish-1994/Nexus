import uuid
from datetime import datetime


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat() if dt else None
