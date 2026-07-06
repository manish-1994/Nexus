from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from database import init_db
from config import settings
from api import api_router
import logging

logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # --- RUNTIME VERIFICATION (diagnostic only) ---
    import sys as _sys
    import inspect as _inspect
    print("=" * 80)
    print("BACKEND STARTUP")
    print("Python executable:", _sys.executable)
    print("Current working directory:", __import__("os").getcwd())
    print("sys.path:")
    for _p in _sys.path:
        print("  ", _p)
    try:
        import services.execution_manager as _em
        import agents.manager as _am
        import api.chat as _chat
        print("Loaded module paths:")
        print("  services.execution_manager ->", _inspect.getfile(_em))
        print("  agents.manager              ->", _inspect.getfile(_am))
        print("  api.chat                    ->", _inspect.getfile(_chat))
        from services.execution_manager import AgentExecutionManager
        from agents.manager import AgentManager
        print("Class file paths:")
        print("  AgentExecutionManager ->", _inspect.getfile(AgentExecutionManager))
        print("  AgentManager          ->", _inspect.getfile(AgentManager))
    except Exception as _e:
        print("STARTUP VERIFICATION FAILED:", _e)
    print("=" * 80)
    # --- END RUNTIME VERIFICATION ---
    # Startup
    init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="NEXUS V3 - Local-first AI Operating System",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to ensure all errors return JSON."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)},
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    logger.warning("ValueError: %s", exc)
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.project_name,
        "version": settings.version,
        "status": "running",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
