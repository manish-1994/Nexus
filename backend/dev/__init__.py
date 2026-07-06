"""Developer Diagnostics & Validation Layer for NEXUS.

This is a developer-only diagnostics namespace (/api/dev) that exposes
the internal state of all backend subsystems for debugging and validation.

NOT a user-facing feature. Does NOT modify Mission Control or any UI.

Modules:
- diagnostics: Core collector that inspects all subsystem states
- health_checks: PASS/WARN/FAIL validators for each subsystem
- selftest: Backend self-test runner
- routes: FastAPI router with all /api/dev/* endpoints
"""

from .routes import router

__all__ = ["router"]
