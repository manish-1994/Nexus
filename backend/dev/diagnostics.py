"""Core Diagnostics Collector — inspects all backend subsystem states.

Provides a single entry point to collect the internal state of:
- Planner
- Workflow Engine (Scheduler, Executor, Queue, Graph, Events, History)
- Agent Registry
- Active Workflows & Running Tasks
- Execution Store
- Providers
- Database
- System metrics (memory, process info)
"""

import gc
import logging
import os
import platform
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore

logger = logging.getLogger("dev.diagnostics")


class DiagnosticsCollector:
    """Collects diagnostic state from all backend subsystems."""

    def __init__(self, db=None):
        self.db = db

    # ================================================================
    # System-level diagnostics
    # ================================================================

    def collect_system_info(self) -> Dict[str, Any]:
        """Collect system-level information."""
        base = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "pid": os.getpid(),
            "cwd": os.getcwd(),
            "gc": {
                "counts": gc.get_count(),
                "objects": len(gc.get_objects()),
            },
            "sys_path_count": len(sys.path),
        }

        if not _PSUTIL_AVAILABLE:
            base["psutil_available"] = False
            base["memory"] = {"error": "psutil not installed (pip install psutil)"}
            base["cpu"] = {"error": "psutil not installed"}
            base["disk"] = {"error": "psutil not installed"}
            return base

        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        base["psutil_available"] = True
        base["memory"] = {
            "rss_mb": round(mem_info.rss / 1024 / 1024, 2),
            "vms_mb": round(mem_info.vms / 1024 / 1024, 2),
            "percent": round(process.memory_percent(), 2),
        }
        base["cpu"] = {
            "percent": process.cpu_percent(interval=0.1),
            "num_threads": process.num_threads(),
            "num_fds": self._safe_num_fds(process),
        }
        base["disk"] = self._collect_disk_usage()
        return base

    def _safe_num_fds(self, process) -> int:
        """Safely get number of file descriptors (platform-dependent)."""
        try:
            return process.num_fds() if hasattr(process, "num_fds") else 0
        except Exception:
            return 0

    def _collect_disk_usage(self) -> Dict[str, Any]:
        """Collect disk usage for the data directory."""
        try:
            data_path = os.path.join(os.getcwd(), "data")
            if os.path.exists(data_path):
                usage = psutil.disk_usage(data_path)
                return {
                    "path": data_path,
                    "total_gb": round(usage.total / 1024 / 1024 / 1024, 2),
                    "used_gb": round(usage.used / 1024 / 1024 / 1024, 2),
                    "free_gb": round(usage.free / 1024 / 1024 / 1024, 2),
                    "percent": round(usage.percent, 2),
                }
        except Exception:
            pass
        return {"path": "data/", "error": "unable to read"}

    # ================================================================
    # Workflow Engine diagnostics
    # ================================================================

    def collect_workflow_engine_state(self) -> Dict[str, Any]:
        """Collect state from all workflow engine components."""
        return {
            "scheduler": self._collect_scheduler_state(),
            "executor": self._collect_executor_state(),
            "queue": self._collect_queue_state(),
            "event_bus": self._collect_event_bus_state(),
            "history": self._collect_history_state(),
            "task_manager": self._collect_task_manager_state(),
        }

    def _collect_scheduler_state(self) -> Dict[str, Any]:
        """Collect scheduler state."""
        try:
            from workflow.scheduler.scheduler import get_scheduler

            scheduler = get_scheduler()
            if not scheduler:
                return {"status": "not_initialized", "active_workflows": 0}

            active_workflows = scheduler.get_all_active_workflows()
            return {
                "status": "initialized",
                "state": scheduler.state.value if hasattr(scheduler, "state") else "unknown",
                "active_workflow_count": scheduler.active_workflow_count,
                "active_workflows": active_workflows,
                "config": {
                    "max_concurrent_workflows": scheduler.config.max_concurrent_workflows,
                    "max_concurrent_tasks_per_workflow": scheduler.config.max_concurrent_tasks_per_workflow,
                    "default_max_retries": scheduler.config.default_max_retries,
                    "enable_parallel_execution": scheduler.config.enable_parallel_execution,
                },
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _collect_executor_state(self) -> Dict[str, Any]:
        """Collect executor state."""
        try:
            from workflow.executor.executor import get_executor

            executor = get_executor()
            if not executor:
                return {"status": "not_initialized"}

            return {
                "status": "initialized",
                "config": {
                    "max_parallel_tasks": executor.config.max_parallel_tasks,
                    "default_max_retries": executor.config.default_max_retries,
                    "base_retry_delay_ms": executor.config.base_retry_delay_ms,
                    "max_retry_delay_ms": executor.config.max_retry_delay_ms,
                    "task_timeout_seconds": executor.config.task_timeout_seconds,
                    "enable_fallback": executor.config.enable_fallback,
                },
                "semaphore_available": executor._parallel_semaphore._value if hasattr(executor, "_parallel_semaphore") else None,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _collect_queue_state(self) -> Dict[str, Any]:
        """Collect queue state."""
        try:
            from workflow.queue.queue import get_queue

            queue = get_queue()
            if not queue:
                return {"status": "not_initialized"}

            return {
                "status": "initialized",
                "global_status": queue.get_global_queue_status(),
                "config": {
                    "max_global_concurrent_tasks": queue.config.max_global_concurrent_tasks,
                    "max_workflow_concurrent_tasks": queue.config.max_workflow_concurrent_tasks,
                    "max_queue_size_per_workflow": queue.config.max_queue_size_per_workflow,
                    "task_timeout_seconds": queue.config.task_timeout_seconds,
                },
                "queued_task_count": len(queue._global_queue),
                "running_task_count": len(queue._running_tasks),
                "completed_task_count": len(queue._completed_tasks),
                "failed_task_count": len(queue._failed_tasks),
                "active_workflow_count": len(queue._active_workflows),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _collect_event_bus_state(self) -> Dict[str, Any]:
        """Collect event bus state."""
        try:
            from workflow.events.event_bus import get_event_bus

            event_bus = get_event_bus()
            return {
                "status": "initialized",
                "history_size": len(event_bus._history),
                "history_limit": event_bus._history_size,
                "subscriber_count": {
                    "specific": sum(len(v) for v in event_bus._subscribers.values()),
                    "wildcard": len(event_bus._wildcard_subscribers),
                },
                "event_types_registered": list(event_bus._subscribers.keys()),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _collect_history_state(self) -> Dict[str, Any]:
        """Collect history/resumability state."""
        try:
            from workflow.history.resumability import get_resumability_manager

            manager = get_resumability_manager()
            if not manager:
                return {"status": "not_initialized"}

            return {
                "status": "initialized",
                "checkpoint_interval_tasks": manager.checkpoint_interval_tasks,
                "max_checkpoints_per_workflow": manager.max_checkpoints_per_workflow,
                "tracked_workflows": len(manager._tasks_since_checkpoint),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _collect_task_manager_state(self) -> Dict[str, Any]:
        """Collect task manager state."""
        try:
            from workflow.tasks.task_manager import get_task_manager

            manager = get_task_manager()
            if not manager:
                return {"status": "not_initialized"}

            return {
                "status": "initialized",
                "active_executions": len(manager._active_executions),
                "active_task_ids": list(manager._active_executions.keys()),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ================================================================
    # Planner diagnostics
    # ================================================================

    def collect_planner_state(self) -> Dict[str, Any]:
        """Collect Planner agent state."""
        try:
            from agents.orchestration.agent_config import DEFAULT_AGENTS, AgentRole

            planner_config = DEFAULT_AGENTS.get("planner")
            if not planner_config:
                return {"status": "not_configured"}

            return {
                "status": "configured",
                "role": AgentRole.PLANNER.value,
                "name": planner_config.name,
                "description": planner_config.description,
                "capabilities": planner_config.capabilities,
                "tools": planner_config.tools,
                "parallelizable": planner_config.parallelizable,
                "requires_plan": planner_config.requires_plan,
                "memory_access": planner_config.memory_access,
                "system_prompt_length": len(planner_config.system_prompt) if planner_config.system_prompt else 0,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ================================================================
    # Agent Registry diagnostics
    # ================================================================

    def collect_agent_registry_state(self) -> Dict[str, Any]:
        """Collect agent registry state."""
        try:
            from agents.orchestration.agent_config import DEFAULT_AGENTS
            from agents.orchestration.agent_registry import registry as pluggable_registry

            builtin = {}
            for role, config in DEFAULT_AGENTS.items():
                builtin[role] = {
                    "name": config.name,
                    "description": config.description,
                    "capabilities": config.capabilities,
                    "tools": config.tools,
                    "parallelizable": config.parallelizable,
                    "requires_plan": config.requires_plan,
                    "memory_access": config.memory_access,
                }

            custom = {}
            for role, config in pluggable_registry.get_all_configs().items():
                custom[role] = {
                    "name": config.name,
                    "description": config.description,
                    "capabilities": config.capabilities,
                    "tools": config.tools,
                }

            return {
                "status": "initialized",
                "builtin_count": len(builtin),
                "custom_count": len(custom),
                "total_count": len(builtin) + len(custom),
                "builtin_agents": builtin,
                "custom_agents": custom,
                "custom_roles": pluggable_registry.roles,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ================================================================
    # Execution Store diagnostics
    # ================================================================

    def collect_execution_store_state(self) -> Dict[str, Any]:
        """Collect live execution store state."""
        try:
            from agents.orchestration.execution_store import get_execution_store

            store = get_execution_store()
            active = store.get_all_active()

            return {
                "status": "initialized",
                "active_count": store.active_count,
                "total_tracked": len(store._executions),
                "active_executions": active,
                "event_bus_attached": store._event_bus is not None,
                "event_bus_subscribers": store._event_bus.subscriber_count if store._event_bus else 0,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ================================================================
    # Database diagnostics
    # ================================================================

    def collect_database_state(self) -> Dict[str, Any]:
        """Collect database state."""
        try:
            from database import engine, SessionLocal
            from sqlalchemy import inspect as sql_inspect

            inspector = sql_inspect(engine)
            tables = inspector.get_table_names()

            # Count rows in key tables
            row_counts = {}
            if self.db:
                for table_name in ["workflows", "tasks", "workflow_events", "providers", "agents", "conversations", "messages"]:
                    try:
                        from sqlalchemy import text
                        result = self.db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        row_counts[table_name] = result.scalar()
                    except Exception:
                        row_counts[table_name] = "table_not_found"

            return {
                "status": "connected",
                "database_url": str(engine.url).replace("://", "://***@") if "://" in str(engine.url) else str(engine.url),
                "dialect": engine.dialect.name,
                "table_count": len(tables),
                "tables": tables,
                "row_counts": row_counts,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ================================================================
    # Provider diagnostics
    # ================================================================

    def collect_provider_state(self) -> Dict[str, Any]:
        """Collect provider registry state."""
        try:
            from providers import ProviderRegistry

            all_providers = ProviderRegistry.get_all()

            return {
                "status": "initialized",
                "registered_provider_types": list(all_providers.keys()),
                "registered_provider_count": len(all_providers),
                "provider_types": [pt.value if hasattr(pt, "value") else str(pt) for pt in all_providers.keys()],
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ================================================================
    # Workflow & Task diagnostics (from database)
    # ================================================================

    def collect_workflows(self, limit: int = 50) -> Dict[str, Any]:
        """Collect workflow records from database."""
        if not self.db:
            return {"status": "no_db_session"}

        try:
            from models.workflow import Workflow, Task, WorkflowStatus, TaskStatus

            workflows = self.db.query(Workflow).order_by(Workflow.created_at.desc()).limit(limit).all()

            result = []
            for wf in workflows:
                tasks = self.db.query(Task).filter(Task.workflow_id == wf.id).all()
                completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
                failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
                running = sum(1 for t in tasks if t.status == TaskStatus.RUNNING)
                pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)

                result.append({
                    "id": wf.id,
                    "workflow_id": wf.workflow_id,
                    "user_id": wf.user_id,
                    "prompt": wf.prompt[:200] if wf.prompt else "",
                    "status": wf.status.value if wf.status else None,
                    "provider_id": wf.provider_id,
                    "model": wf.model,
                    "total_tasks": len(tasks),
                    "completed_tasks": completed,
                    "failed_tasks": failed,
                    "running_tasks": running,
                    "pending_tasks": pending,
                    "total_tokens": wf.total_tokens,
                    "total_cost": wf.total_cost,
                    "total_latency_ms": wf.total_latency_ms,
                    "max_retries": wf.max_retries,
                    "retry_count": wf.retry_count,
                    "started_at": wf.started_at.isoformat() if wf.started_at else None,
                    "completed_at": wf.completed_at.isoformat() if wf.completed_at else None,
                    "created_at": wf.created_at.isoformat() if wf.created_at else None,
                })

            return {
                "status": "ok",
                "total_returned": len(result),
                "workflows": result,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def collect_workflow_detail(self, workflow_id: str) -> Dict[str, Any]:
        """Collect detailed workflow state including task graph."""
        if not self.db:
            return {"status": "no_db_session"}

        try:
            from models.workflow import Workflow, Task, TaskStatus
            from workflow.graph.dependency_graph import DependencyGraph

            workflow = self.db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
            if not workflow:
                return {"status": "not_found", "workflow_id": workflow_id}

            tasks = self.db.query(Task).filter(Task.workflow_id == workflow.id).order_by(Task.created_at).all()

            task_details = []
            for t in tasks:
                task_details.append({
                    "task_id": t.task_id,
                    "agent": t.agent,
                    "description": t.description,
                    "dependencies": t.dependencies or [],
                    "status": t.status.value if t.status else None,
                    "progress": t.progress,
                    "provider_id": t.provider_id,
                    "model": t.model,
                    "input_tokens": t.input_tokens,
                    "output_tokens": t.output_tokens,
                    "total_tokens": t.total_tokens,
                    "cost": t.cost,
                    "latency_ms": t.latency_ms,
                    "retry_count": t.retry_count,
                    "max_retries": t.max_retries,
                    "last_error": t.last_error,
                    "error_message": t.error_message,
                    "error_code": t.error_code,
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                })

            # Reconstruct dependency graph
            graph = DependencyGraph.from_dict(workflow.execution_graph or {"nodes": {}, "edges": []})

            return {
                "status": "ok",
                "workflow_id": workflow.workflow_id,
                "prompt": workflow.prompt,
                "status_enum": workflow.status.value if workflow.status else None,
                "execution_graph": workflow.execution_graph,
                "topological_order": graph.topological_order(),
                "parallel_groups": graph.get_parallel_groups(),
                "has_cycle": graph.has_cycle(),
                "results": workflow.results,
                "errors": workflow.errors,
                "total_input_tokens": workflow.total_input_tokens,
                "total_output_tokens": workflow.total_output_tokens,
                "total_tokens": workflow.total_tokens,
                "total_cost": workflow.total_cost,
                "total_latency_ms": workflow.total_latency_ms,
                "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "tasks": task_details,
                "task_summary": {
                    "total": len(tasks),
                    "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
                    "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
                    "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
                    "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
                },
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def collect_tasks(self, workflow_id: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Collect task records from database."""
        if not self.db:
            return {"status": "no_db_session"}

        try:
            from models.workflow import Workflow, Task, TaskStatus

            query = self.db.query(Task)

            if workflow_id:
                wf = self.db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
                if not wf:
                    return {"status": "not_found", "workflow_id": workflow_id}
                query = query.filter(Task.workflow_id == wf.id)

            if status:
                query = query.filter(Task.status == TaskStatus(status))

            tasks = query.order_by(Task.created_at.desc()).limit(limit).all()

            result = []
            for t in tasks:
                result.append({
                    "task_id": t.task_id,
                    "workflow_id": t.workflow_id,
                    "agent": t.agent,
                    "description": t.description,
                    "dependencies": t.dependencies or [],
                    "status": t.status.value if t.status else None,
                    "progress": t.progress,
                    "provider_id": t.provider_id,
                    "model": t.model,
                    "input_tokens": t.input_tokens,
                    "output_tokens": t.output_tokens,
                    "total_tokens": t.total_tokens,
                    "cost": t.cost,
                    "latency_ms": t.latency_ms,
                    "retry_count": t.retry_count,
                    "max_retries": t.max_retries,
                    "last_error": t.last_error,
                    "error_message": t.error_message,
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                })

            return {
                "status": "ok",
                "total_returned": len(result),
                "tasks": result,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ================================================================
    # Event monitor
    # ================================================================

    def collect_events(self, limit: int = 500) -> Dict[str, Any]:
        """Collect recent events from both event buses."""
        events = []

        # Workflow event bus
        try:
            from workflow.events.event_bus import get_event_bus

            wf_bus = get_event_bus()
            wf_events = wf_bus.get_history(limit=limit)
            for e in wf_events:
                events.append({
                    "source": "workflow_event_bus",
                    "event_type": e.event_type.value,
                    "workflow_id": e.workflow_id,
                    "task_id": e.task_id,
                    "agent": e.agent,
                    "data": e.data,
                    "timestamp": e.timestamp,
                })
        except Exception as e:
            events.append({"source": "workflow_event_bus", "error": str(e)})

        # Agent OS event bus
        try:
            from agents.orchestration.execution_store import get_execution_store

            store = get_execution_store()
            if store._event_bus:
                os_events = store._event_bus.get_history(limit=limit)
                for e in os_events:
                    events.append({
                        "source": "agent_os_event_bus",
                        "event_type": e.type.value if hasattr(e.type, "value") else str(e.type),
                        "execution_id": getattr(e, "execution_id", None),
                        "agent_role": getattr(e, "agent_role", None),
                        "data": getattr(e, "data", {}),
                        "timestamp": getattr(e, "timestamp", None),
                    })
        except Exception as e:
            events.append({"source": "agent_os_event_bus", "error": str(e)})

        # Sort by timestamp descending
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        events = events[:limit]

        return {
            "status": "ok",
            "total_events": len(events),
            "limit": limit,
            "events": events,
        }

    # ================================================================
    # Metrics aggregation
    # ================================================================

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect aggregated metrics across all subsystems."""
        if not self.db:
            return {"status": "no_db_session"}

        try:
            from models.workflow import Workflow, Task, TaskStatus, WorkflowStatus
            from sqlalchemy import func

            # Workflow metrics
            total_workflows = self.db.query(func.count(Workflow.id)).scalar() or 0
            completed_workflows = self.db.query(func.count(Workflow.id)).filter(
                Workflow.status.in_([WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL])
            ).scalar() or 0
            failed_workflows = self.db.query(func.count(Workflow.id)).filter(
                Workflow.status == WorkflowStatus.FAILED
            ).scalar() or 0
            running_workflows = self.db.query(func.count(Workflow.id)).filter(
                Workflow.status == WorkflowStatus.RUNNING
            ).scalar() or 0

            # Task metrics
            total_tasks = self.db.query(func.count(Task.id)).scalar() or 0
            completed_tasks = self.db.query(func.count(Task.id)).filter(Task.status == TaskStatus.COMPLETED).scalar() or 0
            failed_tasks = self.db.query(func.count(Task.id)).filter(Task.status == TaskStatus.FAILED).scalar() or 0
            running_tasks = self.db.query(func.count(Task.id)).filter(Task.status == TaskStatus.RUNNING).scalar() or 0

            # Token & cost metrics
            total_tokens = self.db.query(func.sum(Workflow.total_tokens)).scalar() or 0
            total_cost = self.db.query(func.sum(Workflow.total_cost)).scalar() or 0.0
            total_latency = self.db.query(func.sum(Workflow.total_latency_ms)).scalar() or 0

            # Retry metrics
            total_retries = self.db.query(func.sum(Task.retry_count)).scalar() or 0
            tasks_with_retries = self.db.query(func.count(Task.id)).filter(Task.retry_count > 0).scalar() or 0

            # Agent usage
            agent_usage = {}
            agent_rows = self.db.query(Task.agent, func.count(Task.id)).group_by(Task.agent).all()
            for agent, count in agent_rows:
                agent_usage[agent] = count

            return {
                "status": "ok",
                "workflows": {
                    "total": total_workflows,
                    "completed": completed_workflows,
                    "failed": failed_workflows,
                    "running": running_workflows,
                    "success_rate": round(completed_workflows / total_workflows * 100, 2) if total_workflows > 0 else 0,
                },
                "tasks": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "failed": failed_tasks,
                    "running": running_tasks,
                    "success_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
                },
                "tokens": {
                    "total": total_tokens,
                },
                "cost": {
                    "total": round(total_cost, 4),
                },
                "latency": {
                    "total_ms": total_latency,
                    "avg_ms": round(total_latency / completed_workflows) if completed_workflows > 0 else 0,
                },
                "retries": {
                    "total": total_retries,
                    "tasks_with_retries": tasks_with_retries,
                    "retry_rate": round(tasks_with_retries / total_tasks * 100, 2) if total_tasks > 0 else 0,
                },
                "agent_usage": agent_usage,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ================================================================
    # Full system snapshot
    # ================================================================

    def collect_full_snapshot(self) -> Dict[str, Any]:
        """Collect a complete snapshot of all subsystems."""
        return {
            "system": self.collect_system_info(),
            "workflow_engine": self.collect_workflow_engine_state(),
            "planner": self.collect_planner_state(),
            "agent_registry": self.collect_agent_registry_state(),
            "execution_store": self.collect_execution_store_state(),
            "database": self.collect_database_state(),
            "providers": self.collect_provider_state(),
            "metrics": self.collect_metrics(),
        }
