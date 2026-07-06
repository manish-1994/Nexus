"""Health Check Validators — PASS / WARN / FAIL for each backend subsystem.

Each health check inspects a subsystem and returns a structured result:
- status: "PASS" | "WARN" | "FAIL"
- message: human-readable explanation
- details: optional dict with supporting data
- checks: optional list of sub-checks (for composite checks)

The HealthChecker aggregates all subsystem checks into a single report.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .diagnostics import DiagnosticsCollector

logger = logging.getLogger("dev.health_checks")

# Health status constants
PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


def _result(status: str, message: str, **extra) -> Dict[str, Any]:
    """Build a standardized health check result dict."""
    r = {"status": status, "message": message}
    r.update(extra)
    return r


class HealthChecker:
    """Runs PASS/WARN/FAIL health checks against all backend subsystems."""

    def __init__(self, db=None):
        self.collector = DiagnosticsCollector(db=db)
        self.db = db

    # ================================================================
    # Individual subsystem checks
    # ================================================================

    def check_workflow_engine(self) -> Dict[str, Any]:
        """Check the overall Workflow Engine (scheduler + executor + queue)."""
        state = self.collector.collect_workflow_engine_state()
        checks: List[Dict[str, Any]] = []

        # Scheduler
        sched = state.get("scheduler", {})
        if sched.get("status") == "initialized":
            checks.append(_result(PASS, "Scheduler initialized",
                                  active_workflows=sched.get("active_workflow_count", 0)))
        elif sched.get("status") == "not_initialized":
            checks.append(_result(WARN, "Scheduler not initialized (call /api/workflows/initialize)"))
        else:
            checks.append(_result(FAIL, f"Scheduler error: {sched.get('error', 'unknown')}"))

        # Executor
        exe = state.get("executor", {})
        if exe.get("status") == "initialized":
            checks.append(_result(PASS, "Executor initialized",
                                  max_parallel=exe.get("config", {}).get("max_parallel_tasks")))
        elif exe.get("status") == "not_initialized":
            checks.append(_result(WARN, "Executor not initialized"))
        else:
            checks.append(_result(FAIL, f"Executor error: {exe.get('error', 'unknown')}"))

        # Queue
        q = state.get("queue", {})
        if q.get("status") == "initialized":
            queued = q.get("queued_task_count", 0)
            running = q.get("running_task_count", 0)
            status = PASS if running == 0 else PASS
            checks.append(_result(status, f"Queue initialized (queued={queued}, running={running})"))
        elif q.get("status") == "not_initialized":
            checks.append(_result(WARN, "Queue not initialized"))
        else:
            checks.append(_result(FAIL, f"Queue error: {q.get('error', 'unknown')}"))

        # Event bus
        eb = state.get("event_bus", {})
        if eb.get("status") == "initialized":
            checks.append(_result(PASS, "Event bus initialized",
                                  history=eb.get("history_size", 0)))
        else:
            checks.append(_result(FAIL, f"Event bus error: {eb.get('error', 'unknown')}"))

        # History / resumability
        hist = state.get("history", {})
        if hist.get("status") == "initialized":
            checks.append(_result(PASS, "Resumability manager initialized"))
        elif hist.get("status") == "not_initialized":
            checks.append(_result(WARN, "Resumability manager not initialized"))
        else:
            checks.append(_result(FAIL, f"Resumability error: {hist.get('error', 'unknown')}"))

        # Task manager
        tm = state.get("task_manager", {})
        if tm.get("status") == "initialized":
            checks.append(_result(PASS, "Task manager initialized",
                                  active=tm.get("active_executions", 0)))
        elif tm.get("status") == "not_initialized":
            checks.append(_result(WARN, "Task manager not initialized"))
        else:
            checks.append(_result(FAIL, f"Task manager error: {tm.get('error', 'unknown')}"))

        return self._aggregate("workflow_engine", checks)

    def check_planner(self) -> Dict[str, Any]:
        """Check the Planner agent configuration."""
        state = self.collector.collect_planner_state()

        if state.get("status") == "configured":
            checks = [_result(PASS, "Planner agent configured",
                              role=state.get("role"),
                              capabilities=state.get("capabilities"))]
            if not state.get("system_prompt_length"):
                checks.append(_result(WARN, "Planner has no system prompt"))
            return self._aggregate("planner", checks)
        elif state.get("status") == "not_configured":
            return _result(FAIL, "Planner agent not configured in DEFAULT_AGENTS",
                           checks=[_result(FAIL, "No 'planner' entry in DEFAULT_AGENTS")])
        else:
            return _result(FAIL, f"Planner check error: {state.get('error', 'unknown')}",
                           checks=[_result(FAIL, state.get("error", "unknown"))])

    def check_scheduler(self) -> Dict[str, Any]:
        """Check the Workflow Scheduler specifically."""
        state = self.collector._collect_scheduler_state()
        checks: List[Dict[str, Any]] = []

        if state.get("status") == "initialized":
            checks.append(_result(PASS, "Scheduler initialized"))
            active = state.get("active_workflow_count", 0)
            if active > 0:
                checks.append(_result(PASS, f"{active} active workflow(s)"))
            max_wf = state.get("config", {}).get("max_concurrent_workflows", 0)
            if active >= max_wf and max_wf > 0:
                checks.append(_result(WARN, "At max concurrent workflow capacity"))
        elif state.get("status") == "not_initialized":
            checks.append(_result(WARN, "Scheduler not initialized"))
        else:
            checks.append(_result(FAIL, f"Scheduler error: {state.get('error')}"))

        return self._aggregate("scheduler", checks)

    def check_queue(self) -> Dict[str, Any]:
        """Check the Workflow Queue."""
        state = self.collector._collect_queue_state()
        checks: List[Dict[str, Any]] = []

        if state.get("status") == "initialized":
            checks.append(_result(PASS, "Queue initialized"))
            failed = state.get("failed_task_count", 0)
            if failed > 0:
                checks.append(_result(WARN, f"{failed} failed task(s) in queue tracking"))
            queued = state.get("queued_task_count", 0)
            running = state.get("running_task_count", 0)
            checks.append(_result(PASS, f"Queue: {queued} queued, {running} running"))
        elif state.get("status") == "not_initialized":
            checks.append(_result(WARN, "Queue not initialized"))
        else:
            checks.append(_result(FAIL, f"Queue error: {state.get('error')}"))

        return self._aggregate("queue", checks)

    def check_executor(self) -> Dict[str, Any]:
        """Check the Workflow Executor."""
        state = self.collector._collect_executor_state()
        checks: List[Dict[str, Any]] = []

        if state.get("status") == "initialized":
            checks.append(_result(PASS, "Executor initialized"))
            sem = state.get("semaphore_available")
            max_par = state.get("config", {}).get("max_parallel_tasks")
            if sem is not None and max_par:
                if sem == 0:
                    checks.append(_result(WARN, "All parallel execution slots in use"))
                else:
                    checks.append(_result(PASS, f"{sem}/{max_par} parallel slots available"))
        elif state.get("status") == "not_initialized":
            checks.append(_result(WARN, "Executor not initialized"))
        else:
            checks.append(_result(FAIL, f"Executor error: {state.get('error')}"))

        return self._aggregate("executor", checks)

    def check_event_bus(self) -> Dict[str, Any]:
        """Check the Workflow Event Bus."""
        state = self.collector._collect_event_bus_state()
        checks: List[Dict[str, Any]] = []

        if state.get("status") == "initialized":
            checks.append(_result(PASS, "Event bus initialized"))
            hist = state.get("history_size", 0)
            limit = state.get("history_limit", 0)
            if limit > 0 and hist >= limit * 0.9:
                checks.append(_result(WARN, f"Event history near capacity ({hist}/{limit})"))
            else:
                checks.append(_result(PASS, f"Event history: {hist}/{limit}"))
            subs = state.get("subscriber_count", {})
            total_subs = subs.get("specific", 0) + subs.get("wildcard", 0)
            if total_subs == 0:
                checks.append(_result(WARN, "No event subscribers registered"))
            else:
                checks.append(_result(PASS, f"{total_subs} subscriber(s) registered"))
        else:
            checks.append(_result(FAIL, f"Event bus error: {state.get('error')}"))

        return self._aggregate("event_bus", checks)

    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and required tables."""
        state = self.collector.collect_database_state()
        checks: List[Dict[str, Any]] = []

        if state.get("status") == "connected":
            checks.append(_result(PASS, "Database connected",
                                  dialect=state.get("dialect")))
            tables = state.get("tables", [])
            required = ["workflows", "tasks", "workflow_events", "providers", "agents"]
            missing = [t for t in required if t not in tables]
            if missing:
                checks.append(_result(FAIL, f"Missing required tables: {missing}"))
            else:
                checks.append(_result(PASS, f"All required tables present ({len(required)} tables)"))

            row_counts = state.get("row_counts", {})
            for tname in required:
                if tname in row_counts and row_counts[tname] == "table_not_found":
                    checks.append(_result(FAIL, f"Table '{tname}' not found"))
        else:
            checks.append(_result(FAIL, f"Database error: {state.get('error', 'unknown')}"))

        return self._aggregate("database", checks)

    def check_providers(self) -> Dict[str, Any]:
        """Check the Provider Registry."""
        state = self.collector.collect_provider_state()
        checks: List[Dict[str, Any]] = []

        if state.get("status") == "initialized":
            count = state.get("registered_provider_count", 0)
            if count == 0:
                checks.append(_result(FAIL, "No providers registered"))
            else:
                checks.append(_result(PASS, f"{count} provider type(s) registered",
                                      types=state.get("provider_types", [])))
        else:
            checks.append(_result(FAIL, f"Provider registry error: {state.get('error')}"))

        # Also check DB-configured providers if we have a session
        if self.db:
            try:
                from models.provider import Provider
                db_providers = self.db.query(Provider).filter(Provider.is_active == True).count()
                if db_providers == 0:
                    checks.append(_result(WARN, "No active providers configured in database"))
                else:
                    checks.append(_result(PASS, f"{db_providers} active provider(s) in database"))
            except Exception as e:
                checks.append(_result(WARN, f"Could not query DB providers: {e}"))

        return self._aggregate("providers", checks)

    def check_agent_registry(self) -> Dict[str, Any]:
        """Check the Agent Registry."""
        state = self.collector.collect_agent_registry_state()
        checks: List[Dict[str, Any]] = []

        if state.get("status") == "initialized":
            builtin = state.get("builtin_count", 0)
            custom = state.get("custom_count", 0)
            if builtin == 0:
                checks.append(_result(FAIL, "No builtin agents configured"))
            else:
                checks.append(_result(PASS, f"{builtin} builtin agent(s) configured"))
            if custom > 0:
                checks.append(_result(PASS, f"{custom} custom agent(s) registered"))
            # Verify planner exists
            builtin_agents = state.get("builtin_agents", {})
            if "planner" not in builtin_agents:
                checks.append(_result(WARN, "Planner agent not found in registry"))
            else:
                checks.append(_result(PASS, "Planner agent present"))
        else:
            checks.append(_result(FAIL, f"Agent registry error: {state.get('error')}"))

        return self._aggregate("agent_registry", checks)

    def check_execution_store(self) -> Dict[str, Any]:
        """Check the live Execution Store."""
        state = self.collector.collect_execution_store_state()
        checks: List[Dict[str, Any]] = []

        if state.get("status") == "initialized":
            checks.append(_result(PASS, "Execution store initialized"))
            active = state.get("active_count", 0)
            if active > 0:
                checks.append(_result(PASS, f"{active} active execution(s)"))
            if not state.get("event_bus_attached"):
                checks.append(_result(WARN, "Execution store event bus not attached"))
            else:
                checks.append(_result(PASS, "Execution store event bus attached"))
        else:
            checks.append(_result(FAIL, f"Execution store error: {state.get('error')}"))

        return self._aggregate("execution_store", checks)

    # ================================================================
    # Aggregation
    # ================================================================

    def _aggregate(self, name: str, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate sub-checks into a single status."""
        statuses = [c.get("status") for c in checks]
        if FAIL in statuses:
            overall = FAIL
        elif WARN in statuses:
            overall = WARN
        elif statuses:
            overall = PASS
        else:
            overall = FAIL

        messages = [c.get("message", "") for c in checks if c.get("status") != PASS]
        summary = "; ".join(messages) if messages else "All checks passed"

        return {
            "name": name,
            "status": overall,
            "message": summary,
            "checks": checks,
        }

    def run_all(self) -> Dict[str, Any]:
        """Run all health checks and return a complete report."""
        timestamp = datetime.now(timezone.utc).isoformat()

        results = {
            "workflow_engine": self.check_workflow_engine(),
            "planner": self.check_planner(),
            "scheduler": self.check_scheduler(),
            "queue": self.check_queue(),
            "executor": self.check_executor(),
            "event_bus": self.check_event_bus(),
            "database": self.check_database(),
            "providers": self.check_providers(),
            "agent_registry": self.check_agent_registry(),
            "execution_store": self.check_execution_store(),
        }

        # Overall status
        all_statuses = [r.get("status") for r in results.values()]
        if FAIL in all_statuses:
            overall = FAIL
        elif WARN in all_statuses:
            overall = WARN
        else:
            overall = PASS

        summary = {
            "PASS": sum(1 for s in all_statuses if s == PASS),
            "WARN": sum(1 for s in all_statuses if s == WARN),
            "FAIL": sum(1 for s in all_statuses if s == FAIL),
        }

        return {
            "timestamp": timestamp,
            "overall_status": overall,
            "summary": summary,
            "checks": results,
        }

    def run_single(self, subsystem: str) -> Dict[str, Any]:
        """Run a single subsystem health check by name."""
        check_map = {
            "workflow_engine": self.check_workflow_engine,
            "planner": self.check_planner,
            "scheduler": self.check_scheduler,
            "queue": self.check_queue,
            "executor": self.check_executor,
            "event_bus": self.check_event_bus,
            "database": self.check_database,
            "providers": self.check_providers,
            "agent_registry": self.check_agent_registry,
            "execution_store": self.check_execution_store,
        }

        checker = check_map.get(subsystem)
        if not checker:
            return {
                "name": subsystem,
                "status": FAIL,
                "message": f"Unknown subsystem: {subsystem}",
                "available": list(check_map.keys()),
            }

        return checker()
