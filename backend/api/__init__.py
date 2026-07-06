from fastapi import APIRouter

from .agent_routes import router as agents_router
from .ai_runtime import router as ai_runtime_router
from .chat import router as chat_router
from .health import router as health_router
from .mission_control import router as mission_control_router
from .providers import router as providers_router
from .runtime import router as runtime_router
from .tools import router as tools_router
from workflow.api.routes import router as workflow_router
from dev.routes import router as dev_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(chat_router, prefix="", tags=["chat"])
api_router.include_router(providers_router, prefix="", tags=["providers"])
api_router.include_router(ai_runtime_router, prefix="", tags=["ai-runtime"])
api_router.include_router(agents_router, prefix="", tags=["agents"])
api_router.include_router(runtime_router, prefix="", tags=["runtime"])
api_router.include_router(tools_router, prefix="", tags=["tools"])
api_router.include_router(mission_control_router, prefix="/mission-control", tags=["mission-control"])
api_router.include_router(workflow_router, prefix="", tags=["workflows"])
api_router.include_router(dev_router, prefix="/dev", tags=["dev-diagnostics"])

__all__ = ["api_router"]
