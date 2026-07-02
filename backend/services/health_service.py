from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from config import settings


class HealthService:
    """Service for health checks."""

    def __init__(self, db: Session):
        self.db = db

    def check_health(self) -> Dict[str, Any]:
        """Perform health check."""
        health = {
            "status": "healthy",
            "version": settings.version,
            "database": "disconnected",
            "environment": settings.environment,
        }

        # Check database connection
        try:
            self.db.execute(text("SELECT 1"))
            health["database"] = "connected"
        except Exception as e:
            health["database"] = f"error: {str(e)}"
            health["status"] = "unhealthy"

        return health
