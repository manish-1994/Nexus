from fastapi import APIRouter
from .health import router as health_router
from .providers import router as providers_router
from .chat import router as chat_router
from .ai_runtime import router as ai_runtime_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(chat_router, prefix="", tags=["chat"])
api_router.include_router(providers_router, prefix="", tags=["providers"])
api_router.include_router(ai_runtime_router, prefix="", tags=["ai-runtime"])

__all__ = ["api_router"]
