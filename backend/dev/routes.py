"""Developer Diagnostics API Routes — /api/dev/* endpoints.

All endpoints are developer-only and expose internal backend state.
They do NOT modify any user-facing functionality.

Endpoints:
  GET  /system              — system info (memory, CPU, disk, GC)
  GET  /workflows           — list recent workflows
  GET  /workflows/{id}      — detailed workflow + task graph
  GET  /tasks               — list tasks (filter by workflow_id, status)
  GET  /queue               — queue state
  GET  /events              — last 500 events from both event buses
  GET  /agents              — agent registry state
  GET  /planner             — planner agent config
  GET  /scheduler           — scheduler state
  GET  /executor            — executor state
  GET  /metrics             — aggregated metrics
  GET  /health              — PASS/WARN/FAIL health checks for all subsystems
  GET  /health/{subsystem}  — health check for a single subsystem
  POST /selftest            — run synthetic end-to-end pipeline test
  GET  /snapshot            — full system snapshot
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from database import get_db
from .diagnostics import DiagnosticsCollector
from .health_checks import HealthChecker
from .selftest import SelfTestRunner

logger = logging.getLogger("dev.routes")

router = APIRouter()


# ================================================================
# Helper to build a collector with the DB session
# ================================================================

def _collector(db) -> DiagnosticsCollector:
    return DiagnosticsCollector(db=db)


def _health_checker(db) -> HealthChecker:
    return HealthChecker(db=db)


# ================================================================
# System
# ================================================================

@router.get("/system")
async def get_system_info(db=Depends(get_db)) -> Dict[str, Any]:
    """Get system-level information (memory, CPU, disk, GC)."""
    return _collector(db).collect_system_info()


# ================================================================
# Workflows
# ================================================================

@router.get("/workflows")
async def get_workflows(
    limit: int = Query(50, ge=1, le=500),
    db=Depends(get_db),
) -> Dict[str, Any]:
    """List recent workflows from the database."""
    return _collector(db).collect_workflows(limit=limit)


@router.get("/workflows/{workflow_id}")
async def get_workflow_detail(
    workflow_id: str,
    db=Depends(get_db),
) -> Dict[str, Any]:
    """Get detailed workflow state including task graph and topological order."""
    result = _collector(db).collect_workflow_detail(workflow_id)
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return result


# ================================================================
# Tasks
# ================================================================

@router.get("/tasks")
async def get_tasks(
    workflow_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by task status: pending, running, completed, failed, cancelled"),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_db),
) -> Dict[str, Any]:
    """List tasks from the database, optionally filtered by workflow_id and status."""
    return _collector(db).collect_tasks(workflow_id=workflow_id, status=status, limit=limit)


# ================================================================
# Queue
# ================================================================

@router.get("/queue")
async def get_queue_state(db=Depends(get_db)) -> Dict[str, Any]:
    """Get the workflow queue state."""
    return _collector(db)._collect_queue_state()


# ================================================================
# Events
# ================================================================

@router.get("/events")
async def get_events(
    limit: int = Query(500, ge=1, le=5000),
    db=Depends(get_db),
) -> Dict[str, Any]:
    """Get the last N events from both the workflow event bus and agent OS event bus."""
    return _collector(db).collect_events(limit=limit)


# ================================================================
# Agents
# ================================================================

@router.get("/agents")
async def get_agents(db=Depends(get_db)) -> Dict[str, Any]:
    """Get the agent registry state (builtin + custom agents)."""
    return _collector(db).collect_agent_registry_state()


# ================================================================
# Planner
# ================================================================

@router.get("/planner")
async def get_planner(db=Depends(get_db)) -> Dict[str, Any]:
    """Get the Planner agent configuration."""
    return _collector(db).collect_planner_state()


# ================================================================
# Scheduler
# ================================================================

@router.get("/scheduler")
async def get_scheduler(db=Depends(get_db)) -> Dict[str, Any]:
    """Get the workflow scheduler state."""
    return _collector(db)._collect_scheduler_state()


# ================================================================
# Executor
# ================================================================

@router.get("/executor")
async def get_executor(db=Depends(get_db)) -> Dict[str, Any]:
    """Get the workflow executor state."""
    return _collector(db)._collect_executor_state()


# ================================================================
# Metrics
# ================================================================

@router.get("/metrics")
async def get_metrics(db=Depends(get_db)) -> Dict[str, Any]:
    """Get aggregated metrics across all subsystems."""
    return _collector(db).collect_metrics()


# ================================================================
# Health Checks
# ================================================================

@router.get("/health")
async def get_health(db=Depends(get_db)) -> Dict[str, Any]:
    """Run PASS/WARN/FAIL health checks for all subsystems."""
    return _health_checker(db).run_all()


@router.get("/health/{subsystem}")
async def get_health_subsystem(
    subsystem: str,
    db=Depends(get_db),
) -> Dict[str, Any]:
    """Run a health check for a single subsystem.

    Available subsystems: workflow_engine, planner, scheduler, queue,
    executor, event_bus, database, providers, agent_registry, execution_store
    """
    return _health_checker(db).run_single(subsystem)


# ================================================================
# Self-Test
# ================================================================

@router.post("/selftest")
async def run_selftest(db=Depends(get_db)) -> Dict[str, Any]:
    """Run a synthetic end-to-end test of the workflow pipeline.

    Exercises: Planner config, Graph building, Queue operations,
    Scheduler state, Executor config, Database persistence.
    Does NOT make live LLM calls.
    """
    runner = SelfTestRunner(db=db)
    return await runner.run()


# ================================================================
# Full Snapshot
# ================================================================

@router.get("/snapshot")
async def get_snapshot(db=Depends(get_db)) -> Dict[str, Any]:
    """Get a complete snapshot of all subsystems in a single call."""
    return _collector(db).collect_full_snapshot()
