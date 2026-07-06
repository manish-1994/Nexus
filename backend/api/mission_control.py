"""Mission Control API — read-only endpoints for the Dashboard visualization.

Provides real-time state from the Agent Operating System:
- Execution Store (active executions, task status, metrics)
- Event Bus (recent events, filtered history)
- Agent Registry (built-in + custom agents, capabilities)
- Orchestrator health (agent statuses)
- Workflow Execution Engine (workflows, tasks, progress)

These are lightweight, read-only endpoints. They never modify state.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from agents.orchestration.agent_config import DEFAULT_AGENTS, AgentConfig, AgentRole
from agents.orchestration.agent_registry import registry as pluggable_registry
from agents.orchestration.event_bus import EventType
from agents.orchestration.execution_store import get_execution_store
from database import get_db
from models.workflow import Workflow, Task, WorkflowStatus, TaskStatus
from workflow.scheduler.scheduler import get_scheduler
from workflow.queue.queue import get_queue
from workflow.events.event_bus import get_event_bus as get_workflow_event_bus, WorkflowEventType

logger = logging.getLogger("mission_control")

router = APIRouter()


# ---------------------------------------------------------------------------
# Execution Store — live state of all active executions
# ---------------------------------------------------------------------------

@router.get("/executions")
async def get_all_executions(
    active_only: bool = Query(default=True, description="Only return non-terminal executions"),
) -> Dict[str, Any]:
    """Get all executions from the Live Execution Store."""
    store = get_execution_store()
    if active_only:
        executions = store.get_all_active()
    else:
        # Return all including completed/failed/cancelled
        executions = [
            e.to_dict()
            for e in store._executions.values()
        ]
    return {
        "executions": executions,
        "active_count": store.active_count,
        "total_count": len(store._executions),
    }


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str) -> Dict[str, Any]:
    """Get a specific execution by ID."""
    store = get_execution_store()
    exec_dict = store.get_execution_dict(execution_id)
    if exec_dict is None:
        return {"error": "Execution not found", "execution_id": execution_id}
    return exec_dict


@router.get("/executions/by-conversation/{conversation_id}")
async def get_execution_by_conversation(conversation_id: int) -> Dict[str, Any]:
    """Get the active execution for a conversation."""
    store = get_execution_store()
    exec_ = store.get_by_conversation(conversation_id)
    if exec_ is None:
        return {"error": "No active execution for this conversation", "conversation_id": conversation_id}
    return exec_.to_dict()


# ---------------------------------------------------------------------------
# Event Bus — recent events and filtered history
# ---------------------------------------------------------------------------

@router.get("/events")
async def get_events(
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    execution_id: Optional[str] = Query(default=None, description="Filter by execution ID"),
    limit: int = Query(default=50, ge=1, le=200, description="Max events to return"),
) -> Dict[str, Any]:
    """Get recent events from the Event Bus history."""
    store = get_execution_store()
    event_bus = store._event_bus

    if event_bus is None:
        return {"events": [], "count": 0, "note": "Event bus not attached to execution store"}

    # Convert string to EventType enum if provided
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = EventType(event_type)
        except ValueError:
            return {"error": f"Invalid event type: {event_type}", "valid_types": [e.value for e in EventType]}

    events = event_bus.get_history(
        event_type=event_type_enum,
        execution_id=execution_id,
        limit=limit,
    )

    return {
        "events": [e.to_dict() for e in events],
        "count": len(events),
        "subscriber_count": event_bus.subscriber_count,
    }


@router.get("/events/stream")
async def stream_events():
    """Stream all execution events in real-time from the Event Bus using SSE."""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    store = get_execution_store()
    event_bus = store._event_bus

    async def event_generator():
        queue = asyncio.Queue()

        async def handler(event) -> None:
            await queue.put(event)

        if event_bus:
            event_bus.subscribe_all(handler)
        
        try:
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=10.0)
                    yield f"data: {json.dumps(event.to_dict())}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        finally:
            if event_bus:
                event_bus.unsubscribe_all(handler)

    return StreamingResponse(event_generator(), media_type="text/event-stream")



# ---------------------------------------------------------------------------
# Agent Registry — all agents (built-in + custom)
# ---------------------------------------------------------------------------

@router.get("/agents")
async def get_all_agents() -> Dict[str, Any]:
    """Get all registered agents — built-in defaults + pluggable custom agents."""
    builtin_agents = {}
    for role, config in DEFAULT_AGENTS.items():
        builtin_agents[role] = config.to_dict()

    custom_agents = pluggable_registry.get_all_configs()
    custom_agents_dict = {
        role: config.to_dict() for role, config in custom_agents.items()
    }

    # Merge: custom agents can shadow built-in descriptions but not roles
    all_agents = {**builtin_agents, **custom_agents_dict}

    return {
        "agents": all_agents,
        "builtin_count": len(builtin_agents),
        "custom_count": len(custom_agents),
        "total_count": len(all_agents),
        "builtin_roles": list(builtin_agents.keys()),
        "custom_roles": list(custom_agents_dict.keys()),
    }


@router.get("/agents/{role}")
async def get_agent_by_role(role: str) -> Dict[str, Any]:
    """Get a specific agent by role (checks built-in first, then custom)."""
    # Check built-in
    if role in DEFAULT_AGENTS:
        return {
            "agent": DEFAULT_AGENTS[role].to_dict(),
            "source": "builtin",
        }

    # Check custom
    custom_config = pluggable_registry.get_config(role)
    if custom_config:
        return {
            "agent": custom_config.to_dict(),
            "source": "custom",
        }

    return {"error": f"Agent role not found: {role}"}


@router.get("/agents/capabilities")
async def get_agent_capabilities() -> Dict[str, Any]:
    """Get capability descriptions for all agents (used by Planner)."""
    builtin_capabilities = []
    for role, config in DEFAULT_AGENTS.items():
        builtin_capabilities.append({
            "role": role,
            "name": config.name,
            "description": config.description,
            "capabilities": config.capabilities,
            "tools": config.tools,
            "parallelizable": config.parallelizable,
            "requires_plan": config.requires_plan,
            "memory_access": config.memory_access,
        })

    custom_capabilities = pluggable_registry.get_all_capability_descriptions()

    return {
        "capabilities": builtin_capabilities + custom_capabilities,
        "total": len(builtin_capabilities) + len(custom_capabilities),
    }


# ---------------------------------------------------------------------------
# Orchestrator Health — agent statuses
# ---------------------------------------------------------------------------

@router.get("/health")
async def get_orchestrator_health() -> Dict[str, Any]:
    """Get health status of the Agent OS — execution store + agent registry."""
    store = get_execution_store()

    # Agent health: built-in agents are always "available", custom agents are "registered"
    agent_health = {}
    for role in DEFAULT_AGENTS:
        agent_health[role] = {
            "status": "available",
            "type": "builtin",
        }
    for role in pluggable_registry.roles:
        agent_health[role] = {
            "status": "registered",
            "type": "custom",
        }

    return {
        "status": "operational",
        "active_executions": store.active_count,
        "total_executions_tracked": len(store._executions),
        "event_bus_attached": store._event_bus is not None,
        "event_bus_subscribers": store._event_bus.subscriber_count if store._event_bus else 0,
        "builtin_agents": len(DEFAULT_AGENTS),
        "custom_agents": pluggable_registry.count,
        "agent_health": agent_health,
    }


# ---------------------------------------------------------------------------
# Workflow Execution Engine — workflows, tasks, progress
# ---------------------------------------------------------------------------

@router.get("/workflows")
async def get_active_workflows(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get all active workflows from the scheduler and queue."""
    scheduler = get_scheduler()
    queue = get_queue()
    
    workflows = []
    
    # Get active workflows from scheduler
    if scheduler:
        active = scheduler.get_all_active_workflows()
        for wf in active:
            workflows.append({
                "workflow_id": wf["workflow_id"],
                "status": wf["status"],
                "progress": wf["progress"],
                "total_tasks": wf["total_tasks"],
                "completed_tasks": wf["completed_tasks"],
                "failed_tasks": wf["failed_tasks"],
                "running_tasks": wf["running_tasks"],
                "current_task": wf["current_task"],
                "started_at": wf["started_at"],
                "source": "scheduler",
            })
    
    # Get queued workflows from database
    queued_workflows = db.query(Workflow).filter(
        Workflow.status.in_([WorkflowStatus.CREATED, WorkflowStatus.QUEUED])
    ).all()
    
    for wf in queued_workflows:
        workflows.append({
            "workflow_id": wf.workflow_id,
            "status": wf.status.value,
            "progress": 0,
            "total_tasks": len(wf.tasks),
            "completed_tasks": 0,
            "failed_tasks": 0,
            "running_tasks": 0,
            "current_task": None,
            "started_at": wf.started_at.isoformat() if wf.started_at else None,
            "source": "queue",
        })
    
    # Get queue status
    queue_status = queue.get_global_queue_status() if queue else {}
    
    return {
        "workflows": workflows,
        "total": len(workflows),
        "queue_status": queue_status,
    }


@router.get("/workflows/{workflow_id}")
async def get_workflow_details(
    workflow_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get detailed workflow information including tasks."""
    # Check scheduler first
    scheduler = get_scheduler()
    if scheduler:
        status = scheduler.get_workflow_status(workflow_id)
        if status:
            # Get tasks from database
            workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
            if workflow:
                tasks = []
                for task in workflow.tasks:
                    tasks.append({
                        "task_id": task.task_id,
                        "agent": task.agent,
                        "description": task.description,
                        "dependencies": task.dependencies,
                        "status": task.status.value,
                        "progress": task.progress,
                        "output": task.output,
                        "error_message": task.error_message,
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "latency_ms": task.latency_ms,
                        "retry_count": task.retry_count,
                    })
                status["tasks"] = tasks
            return status
    
    # Fallback to database
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not workflow:
        return {"error": "Workflow not found", "workflow_id": workflow_id}
    
    tasks = []
    for task in workflow.tasks:
        tasks.append({
            "task_id": task.task_id,
            "agent": task.agent,
            "description": task.description,
            "dependencies": task.dependencies,
            "status": task.status.value,
            "progress": task.progress,
            "output": task.output,
            "error_message": task.error_message,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "latency_ms": task.latency_ms,
            "retry_count": task.retry_count,
        })
    
    return {
        "workflow_id": workflow.workflow_id,
        "status": workflow.status.value,
        "prompt": workflow.prompt,
        "execution_graph": workflow.execution_graph,
        "results": workflow.results,
        "errors": workflow.errors,
        "total_input_tokens": workflow.total_input_tokens,
        "total_output_tokens": workflow.total_output_tokens,
        "total_tokens": workflow.total_tokens,
        "total_cost": workflow.total_cost,
        "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
        "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
        "total_latency_ms": workflow.total_latency_ms,
        "tasks": tasks,
    }


@router.get("/workflows/{workflow_id}/tasks")
async def get_workflow_tasks(
    workflow_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get all tasks for a workflow."""
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not workflow:
        return {"error": "Workflow not found", "workflow_id": workflow_id}
    
    tasks = []
    for task in workflow.tasks:
        tasks.append({
            "task_id": task.task_id,
            "agent": task.agent,
            "description": task.description,
            "dependencies": task.dependencies,
            "status": task.status.value,
            "progress": task.progress,
            "input": task.input,
            "output": task.output,
            "error_message": task.error_message,
            "error_code": task.error_code,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "latency_ms": task.latency_ms,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "input_tokens": task.input_tokens,
            "output_tokens": task.output_tokens,
            "total_tokens": task.total_tokens,
            "cost": task.cost,
        })
    
    return {
        "workflow_id": workflow_id,
        "tasks": tasks,
        "total": len(tasks),
    }


@router.get("/workflows/{workflow_id}/events")
async def stream_workflow_events(
    workflow_id: str,
    db: Session = Depends(get_db),
):
    """Stream workflow events via Server-Sent Events (SSE)."""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    # Verify workflow exists
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not workflow:
        return {"error": "Workflow not found", "workflow_id": workflow_id}
    
    event_bus = get_workflow_event_bus()
    
    async def event_generator():
        queue = asyncio.Queue()
        
        def handler(event):
            if event.workflow_id == workflow_id:
                asyncio.create_task(queue.put(event.to_sse()))
        
        event_bus.subscribe_all(handler)
        
        try:
            # Send initial events from history
            history = event_bus.get_history(workflow_id=workflow_id, limit=50)
            for event in history:
                yield event.to_sse()
            
            # Stream new events
            while True:
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event_data
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield ": keepalive\n\n"
        finally:
            event_bus.unsubscribe_all(handler)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ---------------------------------------------------------------------------
# Summary — single endpoint returning everything the Dashboard needs
# ---------------------------------------------------------------------------

@router.get("/summary")
async def get_mission_control_summary(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Single endpoint returning all Mission Control data in one call."""
    store = get_execution_store()
    scheduler = get_scheduler()
    queue = get_queue()
    workflow_event_bus = get_workflow_event_bus()

    # Active executions (from Agent OS)
    active_executions = store.get_all_active()

    # Recent events (last 20) - from both event buses
    events = []
    if store._event_bus:
        raw_events = store._event_bus.get_history(limit=20)
        events = [e.to_dict() for e in raw_events]
    
    # Add workflow events
    if workflow_event_bus:
        wf_events = workflow_event_bus.get_history(limit=20)
        events.extend([e.to_dict() for e in wf_events])
    
    # Sort by timestamp
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    events = events[:20]

    # All agents
    builtin_agents = {role: config.to_dict() for role, config in DEFAULT_AGENTS.items()}
    custom_agents = {
        role: config.to_dict()
        for role, config in pluggable_registry.get_all_configs().items()
    }

    # Agent health
    agent_health = {}
    for role in DEFAULT_AGENTS:
        agent_health[role] = {"status": "available", "type": "builtin"}
    for role in pluggable_registry.roles:
        agent_health[role] = {"status": "registered", "type": "custom"}

    # Active workflows
    active_workflows = []
    if scheduler:
        active_workflows = scheduler.get_all_active_workflows()
    
    # Queue status
    queue_status = queue.get_global_queue_status() if queue else {}

    return {
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "orchestrator": {
            "status": "operational",
            "active_executions": store.active_count,
            "total_executions_tracked": len(store._executions),
            "event_bus_attached": store._event_bus is not None,
        },
        "active_executions": active_executions,
        "recent_events": events,
        "agents": {
            "builtin": builtin_agents,
            "custom": custom_agents,
            "all": {**builtin_agents, **custom_agents},
        },
        "agent_health": agent_health,
        "workflows": {
            "active": active_workflows,
            "queue_status": queue_status,
        },
    }