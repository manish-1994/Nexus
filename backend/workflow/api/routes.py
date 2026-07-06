"""Workflow API Endpoints - REST API for workflow execution management.

Endpoints:
- POST /api/workflows - Create a new workflow from execution plan
- GET /api/workflows - List workflows with filtering
- GET /api/workflows/{workflow_id} - Get workflow details
- GET /api/workflows/{workflow_id}/tasks - Get tasks for a workflow
- GET /api/workflows/{workflow_id}/events - Get workflow event stream
- GET /api/execution - Get current execution status
- POST /api/workflows/{workflow_id}/cancel - Cancel a workflow
- POST /api/workflows/{workflow_id}/retry - Retry failed tasks
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from workflow.queue.queue import TaskPriority

from database import get_db
from models.workflow import Workflow, Task, WorkflowEvent, WorkflowStatus, TaskStatus
from workflow.graph.dependency_graph import DependencyGraph, build_graph_from_plan
from workflow.scheduler.scheduler import (
    WorkflowScheduler,
    SchedulerConfig,
    get_scheduler,
    create_scheduler,
)
from workflow.executor.executor import (
    WorkflowExecutor,
    ExecutorConfig,
    get_executor,
    create_executor,
)
from workflow.queue.queue import (
    WorkflowQueue,
    QueueConfig,
    get_queue,
    create_queue,
)
from workflow.tasks.task_manager import (
    TaskManager,
    get_task_manager,
    create_task_manager,
)
from workflow.events.event_bus import (
    EventBus,
    WorkflowEventType,
    get_event_bus,
)
from agents.orchestration.orchestrator import Orchestrator
from agents.orchestration.agent_registry import PluggableAgentRegistry
from services.ai_runtime import AIRuntime
from services.execution_manager import AgentExecutionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


# ============================================================
# Request/Response Models
# ============================================================

class WorkflowCreateRequest(BaseModel):
    """Request to create a new workflow."""
    prompt: str = Field(..., description="User prompt for the workflow")
    execution_plan: Dict[str, Any] = Field(..., description="Execution plan from Planner")
    user_id: Optional[str] = Field(None, description="User identifier")
    provider_id: Optional[int] = Field(None, description="Provider ID for LLM")
    model: Optional[str] = Field(None, description="Model name")
    max_retries: int = Field(3, description="Maximum retries per task")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    """Workflow response model."""
    id: int
    workflow_id: str
    user_id: Optional[str]
    prompt: str
    status: str
    execution_graph: Dict[str, Any]
    provider_id: Optional[int]
    model: Optional[str]
    results: Dict[str, Any]
    errors: List[Dict[str, Any]]
    workflow_metadata: Dict[str, Any]
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: float
    started_at: Optional[str]
    completed_at: Optional[str]
    total_latency_ms: Optional[int]
    max_retries: int
    retry_count: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """Task response model."""
    id: int
    task_id: str
    workflow_id: int
    agent: str
    description: str
    dependencies: List[str]
    status: str
    progress: int
    input: Dict[str, Any]
    output: Dict[str, Any]
    provider_id: Optional[int]
    model: Optional[str]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    started_at: Optional[str]
    completed_at: Optional[str]
    latency_ms: Optional[int]
    retry_count: int
    max_retries: int
    last_error: Optional[str]
    error_message: Optional[str]
    error_code: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """Paginated workflow list response."""
    workflows: List[WorkflowResponse]
    total: int
    page: int
    page_size: int


class WorkflowStatusResponse(BaseModel):
    """Workflow execution status response."""
    workflow_id: str
    status: str
    progress: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: int
    current_task: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    total_latency_ms: Optional[int]


class ExecutionStatusResponse(BaseModel):
    """Global execution status response."""
    active_workflows: int
    total_queued_tasks: int
    total_running_tasks: int
    total_completed_tasks: int
    total_failed_tasks: int
    workflows: List[WorkflowStatusResponse]


class CancelWorkflowRequest(BaseModel):
    """Request to cancel a workflow."""
    force: bool = Field(False, description="Force cancel running tasks")


class RetryWorkflowRequest(BaseModel):
    """Request to retry failed tasks in a workflow."""
    task_ids: Optional[List[str]] = Field(None, description="Specific task IDs to retry (None = all failed)")


# ============================================================
# Dependency Injection
# ============================================================

def get_workflow_scheduler(
    db: Session = Depends(get_db),
) -> WorkflowScheduler:
    """Get or create workflow scheduler."""
    scheduler = get_scheduler()
    if not scheduler:
        # This would need proper initialization with all dependencies
        # For now, return None and handle in endpoints
        pass
    return scheduler


def get_workflow_executor(
    db: Session = Depends(get_db),
) -> WorkflowExecutor:
    """Get or create workflow executor."""
    executor = get_executor()
    return executor


def get_workflow_queue(
    db: Session = Depends(get_db),
) -> WorkflowQueue:
    """Get or create workflow queue."""
    queue = get_queue()
    return queue


def get_task_mgr(
    db: Session = Depends(get_db),
) -> TaskManager:
    """Get or create task manager."""
    manager = get_task_manager()
    return manager


# ============================================================
# Helper Functions
# ============================================================

def workflow_to_response(workflow: Workflow) -> WorkflowResponse:
    """Convert Workflow model to response."""
    return WorkflowResponse(
        id=workflow.id,
        workflow_id=workflow.workflow_id,
        user_id=workflow.user_id,
        prompt=workflow.prompt,
        status=workflow.status.value,
        execution_graph=workflow.execution_graph or {},
        provider_id=workflow.provider_id,
        model=workflow.model,
        results=workflow.results or {},
        errors=workflow.errors or [],
        workflow_metadata=workflow.workflow_metadata or {},
        total_input_tokens=workflow.total_input_tokens,
        total_output_tokens=workflow.total_output_tokens,
        total_tokens=workflow.total_tokens,
        total_cost=workflow.total_cost,
        started_at=workflow.started_at.isoformat() if workflow.started_at else None,
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
        total_latency_ms=workflow.total_latency_ms,
        max_retries=workflow.max_retries,
        retry_count=workflow.retry_count,
        created_at=workflow.created_at.isoformat() if workflow.created_at else "",
        updated_at=workflow.updated_at.isoformat() if workflow.updated_at else "",
    )


def task_to_response(task: Task) -> TaskResponse:
    """Convert Task model to response."""
    return TaskResponse(
        id=task.id,
        task_id=task.task_id,
        workflow_id=task.workflow_id,
        agent=task.agent,
        description=task.description,
        dependencies=task.dependencies or [],
        status=task.status.value,
        progress=task.progress,
        input=task.input or {},
        output=task.output or {},
        provider_id=task.provider_id,
        model=task.model,
        input_tokens=task.input_tokens,
        output_tokens=task.output_tokens,
        total_tokens=task.total_tokens,
        cost=task.cost,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        latency_ms=task.latency_ms,
        retry_count=task.retry_count,
        max_retries=task.max_retries,
        last_error=task.last_error,
        error_message=task.error_message,
        error_code=task.error_code,
        created_at=task.created_at.isoformat() if task.created_at else "",
        updated_at=task.updated_at.isoformat() if task.updated_at else "",
    )


# ============================================================
# API Endpoints
# ============================================================

@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    request: WorkflowCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create a new workflow from an execution plan.
    
    The workflow will be created in CREATED status and queued for execution.
    """
    try:
        # Build dependency graph from execution plan
        graph = build_graph_from_plan(request.execution_plan)
        
        # Create workflow record
        workflow = Workflow(
            workflow_id=str(uuid4()),
            user_id=request.user_id,
            prompt=request.prompt,
            status=WorkflowStatus.CREATED,
            execution_graph=graph.to_dict(),
            provider_id=request.provider_id,
            model=request.model,
            max_retries=request.max_retries,
            workflow_metadata=request.metadata,
        )
        
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        
        # Create tasks from graph
        task_manager = get_task_mgr(db)
        if task_manager:
            await task_manager.create_tasks_from_plan(workflow, request.execution_plan, graph)
        
        # Queue workflow for execution (background)
        scheduler = get_workflow_scheduler(db)
        if scheduler:
            background_tasks.add_task(
                scheduler.submit_workflow,
                workflow,
                request.execution_plan
            )
        
        logger.info("Created workflow %s with %d tasks", workflow.workflow_id, len(graph.nodes))
        
        return workflow_to_response(workflow)
        
    except Exception as e:
        logger.exception("Failed to create workflow")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[WorkflowStatus] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
):
    """List workflows with pagination and filtering."""
    query = db.query(Workflow)
    
    if status:
        query = query.filter(Workflow.status == status)
    if user_id:
        query = query.filter(Workflow.user_id == user_id)
    
    # Order by created_at descending
    query = query.order_by(Workflow.created_at.desc())
    
    total = query.count()
    workflows = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return WorkflowListResponse(
        workflows=[workflow_to_response(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
):
    """Get workflow details by workflow_id."""
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow_to_response(workflow)


@router.get("/{workflow_id}/tasks", response_model=List[TaskResponse])
async def get_workflow_tasks(
    workflow_id: str,
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    db: Session = Depends(get_db),
):
    """Get all tasks for a workflow."""
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    query = db.query(Task).filter(Task.workflow_id == workflow.id)
    
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.order_by(Task.created_at).all()
    
    return [task_to_response(t) for t in tasks]


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    db: Session = Depends(get_db),
):
    """Get real-time workflow execution status."""
    # Check active workflows in scheduler
    scheduler = get_workflow_scheduler(db)
    if scheduler:
        status = scheduler.get_workflow_status(workflow_id)
        if status:
            return WorkflowStatusResponse(**status)
    
    # Fallback to database
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    total_tasks = len(workflow.tasks)
    completed = sum(1 for t in workflow.tasks if t.status == TaskStatus.COMPLETED)
    failed = sum(1 for t in workflow.tasks if t.status == TaskStatus.FAILED)
    running = sum(1 for t in workflow.tasks if t.status == TaskStatus.RUNNING)
    
    return WorkflowStatusResponse(
        workflow_id=workflow.workflow_id,
        status=workflow.status.value,
        progress=int((completed / total_tasks) * 100) if total_tasks > 0 else 0,
        total_tasks=total_tasks,
        completed_tasks=completed,
        failed_tasks=failed,
        running_tasks=running,
        current_task=next((t.task_id for t in workflow.tasks if t.status == TaskStatus.RUNNING), None),
        started_at=workflow.started_at.isoformat() if workflow.started_at else None,
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
        total_latency_ms=workflow.total_latency_ms,
    )


@router.post("/{workflow_id}/cancel", response_model=WorkflowResponse)
async def cancel_workflow(
    workflow_id: str,
    request: CancelWorkflowRequest,
    db: Session = Depends(get_db),
):
    """Cancel a running workflow."""
    scheduler = get_workflow_scheduler(db)
    
    if scheduler:
        success = await scheduler.cancel_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found or not running")
    
    # Also cancel in queue
    queue = get_workflow_queue(db)
    if queue:
        queue.cancel_workflow_tasks(workflow_id)
    
    # Return updated workflow
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow_to_response(workflow)


@router.post("/{workflow_id}/retry", response_model=WorkflowResponse)
async def retry_workflow(
    workflow_id: str,
    request: RetryWorkflowRequest,
    db: Session = Depends(get_db),
):
    """Retry failed tasks in a workflow."""
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Get failed tasks
    query = db.query(Task).filter(
        Task.workflow_id == workflow.id,
        Task.status == TaskStatus.FAILED
    )
    
    if request.task_ids:
        query = query.filter(Task.task_id.in_(request.task_ids))
    
    failed_tasks = query.all()
    
    if not failed_tasks:
        raise HTTPException(status_code=400, detail="No failed tasks to retry")
    
    # Reset failed tasks to pending
    for task in failed_tasks:
        task.status = TaskStatus.PENDING
        task.retry_count = 0
        task.last_error = None
        task.error_message = None
        task.error_code = None
        task.started_at = None
        task.completed_at = None
        task.progress = 0
    
    # Update workflow status
    workflow.status = WorkflowStatus.QUEUED
    workflow.retry_count += 1
    
    db.commit()
    
    # Requeue tasks
    queue = get_workflow_queue(db)
    if queue:
        for task in failed_tasks:
            queue.requeue_task(task.task_id, priority=TaskPriority.HIGH)
    
    logger.info("Retrying %d failed tasks for workflow %s", len(failed_tasks), workflow_id)
    
    return workflow_to_response(workflow)


@router.get("/{workflow_id}/events")
async def stream_workflow_events(
    workflow_id: str,
    db: Session = Depends(get_db),
):
    """Stream workflow events via Server-Sent Events (SSE)."""
    # Verify workflow exists
    workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    event_bus = get_event_bus()
    
    async def event_generator():
        queue = asyncio.Queue()
        
        def handler(event: WorkflowEvent):
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


# ============================================================
# Global Execution Endpoint
# ============================================================

@router.get("/execution/status", response_model=ExecutionStatusResponse)
async def get_execution_status(
    db: Session = Depends(get_db),
):
    """Get global execution status across all workflows."""
    scheduler = get_workflow_scheduler(db)
    queue = get_workflow_queue(db)
    
    workflows = []
    
    if scheduler:
        active = scheduler.get_all_active_workflows()
        for wf in active:
            workflows.append(WorkflowStatusResponse(**wf))
    
    # Add queued workflows from database
    queued_workflows = db.query(Workflow).filter(
        Workflow.status.in_([WorkflowStatus.CREATED, WorkflowStatus.QUEUED])
    ).all()
    
    for wf in queued_workflows:
        workflows.append(WorkflowStatusResponse(
            workflow_id=wf.workflow_id,
            status=wf.status.value,
            progress=0,
            total_tasks=len(wf.tasks),
            completed_tasks=0,
            failed_tasks=0,
            running_tasks=0,
            current_task=None,
            started_at=wf.started_at.isoformat() if wf.started_at else None,
            completed_at=None,
            total_latency_ms=None,
        ))
    
    queue_status = queue.get_global_queue_status() if queue else {}
    
    return ExecutionStatusResponse(
        active_workflows=len([w for w in workflows if w.status == "running"]),
        total_queued_tasks=queue_status.get("global_queued_tasks", 0),
        total_running_tasks=queue_status.get("global_running_tasks", 0),
        total_completed_tasks=queue_status.get("global_completed_tasks", 0),
        total_failed_tasks=queue_status.get("global_failed_tasks", 0),
        workflows=workflows,
    )


# ============================================================
# Initialization Endpoint
# ============================================================

@router.post("/initialize")
async def initialize_workflow_engine(
    db: Session = Depends(get_db),
):
    """Initialize the workflow engine components.
    
    This endpoint sets up the scheduler, executor, queue, and task manager
    with all required dependencies. Should be called on application startup.
    """
    try:
        # Get required services (these would be injected in real app)
        from agents.orchestration.orchestrator import get_orchestrator
        from agents.orchestration.agent_registry import get_agent_registry
        from services.ai_runtime import get_ai_runtime
        from services.execution_manager import get_execution_manager
        from workflow.events.event_bus import get_event_bus
        
        orchestrator = get_orchestrator()
        agent_registry = get_agent_registry()
        ai_runtime = get_ai_runtime()
        execution_manager = get_execution_manager()
        event_bus = get_event_bus()
        
        if not all([orchestrator, agent_registry, ai_runtime, execution_manager, event_bus]):
            raise HTTPException(
                status_code=503, 
                detail="Required services not available. Ensure Agent OS is initialized."
            )
        
        # Create components
        scheduler_config = SchedulerConfig()
        executor_config = ExecutorConfig()
        queue_config = QueueConfig()
        
        await create_scheduler(
            db=db,
            orchestrator=orchestrator,
            ai_runtime=ai_runtime,
            execution_manager=execution_manager,
            agent_registry=agent_registry,
            event_bus=event_bus,
            config=scheduler_config,
        )
        
        create_executor(
            db=db,
            orchestrator=orchestrator,
            ai_runtime=ai_runtime,
            execution_manager=execution_manager,
            agent_registry=agent_registry,
            event_bus=event_bus,
            config=executor_config,
        )
        
        create_queue(db=db, config=queue_config)
        
        create_task_manager(
            db=db,
            orchestrator=orchestrator,
            ai_runtime=ai_runtime,
            agent_registry=agent_registry,
            event_bus=event_bus,
        )
        
        # Start queue (scheduler is already started by create_scheduler)
        queue = get_queue()
        
        if queue:
            await queue.start()
        
        return {"status": "initialized", "components": ["scheduler", "executor", "queue", "task_manager"]}
        
    except Exception as e:
        logger.exception("Failed to initialize workflow engine")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shutdown")
async def shutdown_workflow_engine():
    """Shutdown the workflow engine gracefully."""
    scheduler = get_scheduler()
    queue = get_queue()
    
    if scheduler:
        await scheduler.stop(graceful=True)
    
    if queue:
        await queue.stop()
    
    return {"status": "shutdown"}