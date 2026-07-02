from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Dict, Any
from database import get_db
from config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    health = {
        "status": "healthy",
        "version": settings.version,
        "database": "disconnected",
        "environment": settings.environment,
    }

    try:
        db.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    return HealthResponse(**health)
