# Phase 7 — Universal Tool Runtime Architecture Plan

## Overview

Phase 7 builds the **Universal Tool Runtime** — a provider-agnostic, extensible tool execution framework that allows every agent to invoke capabilities (Browser, Python, Files, Memory, Terminal, Planner, etc.) through a single execution pipeline. This is the next architectural layer on top of the Phase 6 Agent Runtime.

**Goal**: NEXUS evolves into an extensible AI Operating System where every capability is a first-class tool that plugs into the Agent Runtime.

---

## 1. Core Concepts

### 1.1 Tool Definition
A **Tool** is a self-contained capability with:
- **Identity**: `id`, `name`, `description`, `version`, `category`
- **Contracts**: `input_schema` (JSON Schema), `output_schema` (JSON Schema)
- **Runtime behavior**: `timeout`, `supports_streaming`, `supports_cancellation`
- **Security**: `permissions` (required scopes/roles)

### 1.2 Tool Registry
- **Auto-discovery**: Scans `backend/tools/` directory for tool modules
- **Registration**: Each tool module exports a `TOOL` instance
- **Lookup**: By `id`, `name`, or `category`
- **Validation**: Schema validation on registration

### 1.3 Tool Manager
Orchestrates tool execution:
- Tool lookup & permission validation
- Execution lifecycle (pending → running → completed/failed/cancelled)
- Cancellation via `asyncio.Event`
- Retry with exponential backoff (configurable per-tool)
- Structured logging (execution_id, tool_id, duration, tokens, errors)

### 1.4 Shared ExecutionContext
Single context object passed between Agent Runtime and Tool Runtime:
```python
@dataclass
class ExecutionContext:
    execution_id: str
    conversation_id: Optional[int]
    agent_id: int
    workspace_id: Optional[int]
    cancel_event: asyncio.Event
    logger: logging.Logger
    stream_callback: Optional[Callable[[str], Awaitable[None]]]
    metadata: Dict[str, Any]
```

---

## 2. Directory Structure

```
backend/
├── tools/
│   ├── __init__.py              # ToolRegistry, auto-discovery
│   ├── base.py                  # BaseTool abstract class
│   ├── registry.py              # ToolRegistry implementation
│   ├── manager.py               # ToolManager implementation
│   ├── context.py               # ExecutionContext dataclass
│   ├── schemas.py               # Pydantic schemas for tool I/O
│   ├── permissions.py           # Permission validation
│   ├── builtins/
│   │   ├── __init__.py          # Exports all builtin tools
│   │   ├── browser.py           # BrowserTool
│   │   ├── python.py            # PythonTool
│   │   ├── terminal.py          # TerminalTool
│   │   ├── file.py              # FileTool
│   │   ├── memory.py            # MemoryTool
│   │   └── search.py            # SearchTool
│   └── models.py                # ToolExecution ORM model (optional persistence)
├── services/
│   ├── __init__.py              # Export ToolManager, ToolRegistry
│   └── tool_service.py          # High-level service (optional)
├── api/
│   ├── __init__.py              # Export tool_router
│   └── tools.py                 # Tool Runtime API endpoints
├── schemas/
│   ├── __init__.py              # Export tool schemas
│   └── tool.py                  # ToolResponse, ToolExecuteRequest, etc.
└── models/
    ├── __init__.py              # Export ToolExecution
    └── tool_execution.py        # ToolExecution ORM model
```

---

## 3. BaseTool Interface

```python
# backend/tools/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional
import json

@dataclass
class ToolMetadata:
    id: str                    # Unique identifier (e.g., "browser.navigate")
    name: str                  # Human-readable name
    description: str           # What the tool does
    version: str               # Semantic version
    category: str              # "browser", "python", "file", "memory", "terminal", "search"
    input_schema: Dict[str, Any]      # JSON Schema for input validation
    output_schema: Dict[str, Any]     # JSON Schema for output validation
    timeout: float = 30.0      # Default timeout in seconds
    supports_streaming: bool = False
    supports_cancellation: bool = True
    permissions: list[str] = None  # Required permission scopes

class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    # Class-level metadata (must be defined by subclasses)
    metadata: ToolMetadata
    
    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: "ExecutionContext"
    ) -> Any:
        """Execute the tool synchronously (non-streaming)."""
        pass
    
    async def execute_stream(
        self,
        input_data: Dict[str, Any],
        context: "ExecutionContext"
    ) -> AsyncGenerator[str, None]:
        """Execute the tool with streaming output. Default: yield single result."""
        result = await self.execute(input_data, context)
        yield json.dumps(result)
    
    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate input against input_schema. Raises ValidationError."""
        pass
    
    def validate_output(self, output_data: Any) -> None:
        """Validate output against output_schema. Raises ValidationError."""
        pass
```

---

## 4. Tool Registry

```python
# backend/tools/registry.py
from typing import Dict, List, Optional, Type
from .base import BaseTool, ToolMetadata

class ToolRegistry:
    """Auto-discovers and registers tools from backend/tools/builtins/"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}  # id -> tool instance
        self._by_name: Dict[str, BaseTool] = {}  # name -> tool instance
        self._by_category: Dict[str, List[BaseTool]] = {}
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        meta = tool.metadata
        self._tools[meta.id] = tool
        self._by_name[meta.name] = tool
        self._by_category.setdefault(meta.category, []).append(tool)
    
    def get(self, tool_id: str) -> Optional[BaseTool]:
        return self._tools.get(tool_id)
    
    def get_by_name(self, name: str) -> Optional[BaseTool]:
        return self._by_name.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[BaseTool]:
        if category:
            return self._by_category.get(category, [])
        return list(self._tools.values())
    
    def discover(self, package: str = "backend.tools.builtins") -> None:
        """Auto-discover tools from a package."""
        import importlib
        import pkgutil
        
        for _, module_name, _ in pkgutil.iter_modules(
            importlib.import_module(package).__path__
        ):
            module = importlib.import_module(f"{package}.{module_name}")
            if hasattr(module, "TOOL"):
                self.register(module.TOOL)
```

---

## 5. Tool Manager

```python
# backend/tools/manager.py
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional

from .base import BaseTool, ToolMetadata
from .registry import ToolRegistry
from .context import ExecutionContext
from .permissions import PermissionValidator
from .schemas import ToolExecutionRecord, ToolExecutionStatus

logger = logging.getLogger("tool_manager")

@dataclass
class ToolExecutionConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0

class ToolManager:
    """Orchestrates tool execution with lifecycle, retries, cancellation, logging."""
    
    def __init__(
        self,
        registry: ToolRegistry,
        permission_validator: PermissionValidator,
        config: Optional[ToolExecutionConfig] = None
    ):
        self.registry = registry
        self.permission_validator = permission_validator
        self.config = config or ToolExecutionConfig()
        self._active_executions: Dict[str, "ToolExecutionContext"] = {}
    
    async def execute(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Any:
        """Execute a tool with full lifecycle management."""
        tool = self.registry.get(tool_id)
        if not tool:
            raise ValueError(f"Tool '{tool_id}' not found")
        
        # Permission check
        self.permission_validator.validate(context, tool.metadata.permissions)
        
        # Input validation
        tool.validate_input(input_data)
        
        # Create execution record
        exec_id = str(uuid.uuid4())
        exec_ctx = ToolExecutionContext(
            execution_id=exec_id,
            tool=tool,
            context=context,
            cancel_event=asyncio.Event(),
            start_time=time.monotonic()
        )
        self._active_executions[exec_id] = exec_ctx
        
        try:
            # Execute with retries
            result = await self._execute_with_retry(exec_ctx, input_data)
            
            # Output validation
            tool.validate_output(result)
            
            # Log success
            self._log_execution(exec_ctx, ToolExecutionStatus.COMPLETED, result=result)
            return result
            
        except asyncio.CancelledError:
            self._log_execution(exec_ctx, ToolExecutionStatus.CANCELLED)
            raise
        except Exception as exc:
            self._log_execution(exec_ctx, ToolExecutionStatus.FAILED, error=exc)
            raise
        finally:
            self._active_executions.pop(exec_id, None)
    
    async def execute_stream(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> AsyncGenerator[str, None]:
        """Execute a streaming tool."""
        tool = self.registry.get(tool_id)
        if not tool or not tool.metadata.supports_streaming:
            raise ValueError(f"Tool '{tool_id}' does not support streaming")
        
        # Similar lifecycle with streaming...
        pass
    
    def cancel(self, execution_id: str) -> bool:
        """Cancel an active tool execution."""
        exec_ctx = self._active_executions.get(execution_id)
        if exec_ctx and exec_ctx.tool.metadata.supports_cancellation:
            exec_ctx.cancel_event.set()
            return True
        return False
    
    async def _execute_with_retry(
        self,
        exec_ctx: "ToolExecutionContext",
        input_data: Dict[str, Any]
    ) -> Any:
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            if exec_ctx.cancel_event.is_set():
                raise asyncio.CancelledError()
            
            try:
                return await exec_ctx.tool.execute(input_data, exec_ctx.context)
            except Exception as exc:
                last_error = exc
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay * (self.config.exponential_base ** attempt),
                        self.config.max_delay
                    )
                    await asyncio.sleep(delay)
        
        raise last_error
    
    def _log_execution(
        self,
        exec_ctx: "ToolExecutionContext",
        status: ToolExecutionStatus,
        result: Any = None,
        error: Exception = None
    ) -> None:
        duration_ms = int((time.monotonic() - exec_ctx.start_time) * 1000)
        logger.info(
            "Tool execution %s: tool=%s status=%s duration_ms=%d",
            exec_ctx.execution_id,
            exec_ctx.tool.metadata.id,
            status.value,
            duration_ms
        )
        # Persist to DB if needed
```

---

## 6. ExecutionContext (Shared)

```python
# backend/tools/context.py
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
import asyncio
import logging

@dataclass
class ExecutionContext:
    """Shared context between Agent Runtime and Tool Runtime."""
    
    execution_id: str
    agent_id: int
    conversation_id: Optional[int] = None
    workspace_id: Optional[int] = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("execution"))
    stream_callback: Optional[Callable[[str], Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set()
    
    def check_cancellation(self) -> None:
        if self.is_cancelled():
            raise asyncio.CancelledError()
```

---

## 7. Built-in Tools (Placeholders)

Each tool in `backend/tools/builtins/` follows the pattern:

```python
# backend/tools/builtins/browser.py
from ..base import BaseTool, ToolMetadata
from ..context import ExecutionContext
from typing import Any, Dict

class BrowserTool(BaseTool):
    metadata = ToolMetadata(
        id="browser.navigate",
        name="Browser Navigate",
        description="Navigate to a URL and extract content",
        version="0.1.0",
        category="browser",
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "wait_for": {"type": "string", "enum": ["load", "domcontentloaded", "networkidle"]},
                "extract": {"type": "string", "enum": ["text", "html", "markdown", "screenshot"]}
            },
            "required": ["url"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "title": {"type": "string"},
                "url": {"type": "string"}
            }
        },
        timeout=60.0,
        supports_streaming=False,
        supports_cancellation=True,
        permissions=["browser:navigate"]
    )
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Any:
        # Placeholder implementation
        context.logger.info("BrowserTool.execute called with %s", input_data)
        return {
            "content": f"[BrowserTool] Would navigate to {input_data['url']}",
            "title": "Placeholder",
            "url": input_data["url"]
        }

TOOL = BrowserTool()
```

Similar structure for:
- **PythonTool** (`python.execute`) — sandboxed Python execution
- **TerminalTool** (`terminal.run`) — shell command execution
- **FileTool** (`file.read`, `file.write`, `file.list`) — filesystem operations
- **MemoryTool** (`memory.store`, `memory.recall`, `memory.search`) — agent memory
- **SearchTool** (`search.web`, `search.local`) — web/local search

---

## 8. Tool Runtime API

```python
# backend/api/tools.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from database import get_db
from tools.registry import ToolRegistry
from tools.manager import ToolManager
from tools.context import ExecutionContext
from schemas.tool import ToolResponse, ToolExecuteRequest, ToolExecuteResponse

router = APIRouter(prefix="/tools", tags=["tools"])

# Dependency injection
def get_tool_manager(db: Session = Depends(get_db)) -> ToolManager:
    registry = ToolRegistry()
    registry.discover()
    return ToolManager(registry, PermissionValidator(db))

@router.get("", response_model=List[ToolResponse])
async def list_tools(
    category: Optional[str] = None,
    manager: ToolManager = Depends(get_tool_manager)
):
    """List all available tools, optionally filtered by category."""
    tools = manager.registry.list_tools(category)
    return [ToolResponse.from_tool(t) for t in tools]

@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    manager: ToolManager = Depends(get_tool_manager)
):
    """Get tool metadata by ID."""
    tool = manager.registry.get(tool_id)
    if not tool:
        raise HTTPException(404, f"Tool '{tool_id}' not found")
    return ToolResponse.from_tool(tool)

@router.post("/{tool_id}/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    tool_id: str,
    request: ToolExecuteRequest,
    background_tasks: BackgroundTasks,
    manager: ToolManager = Depends(get_tool_manager)
):
    """Execute a tool with the given input."""
    context = ExecutionContext(
        execution_id=request.execution_id,
        agent_id=request.agent_id,
        conversation_id=request.conversation_id,
        workspace_id=request.workspace_id
    )
    
    result = await manager.execute(tool_id, request.input_data, context)
    return ToolExecuteResponse(
        execution_id=request.execution_id,
        tool_id=tool_id,
        status="completed",
        output=result
    )

@router.post("/{tool_id}/cancel")
async def cancel_tool(
    tool_id: str,
    execution_id: str,
    manager: ToolManager = Depends(get_tool_manager)
):
    """Cancel a running tool execution."""
    success = manager.cancel(execution_id)
    if not success:
        raise HTTPException(404, "Execution not found or not cancellable")
    return {"status": "cancelled", "execution_id": execution_id}
```

---

## 9. Integration with AgentExecutionManager

### 9.1 AgentExecutionManager Changes

```python
# backend/services/execution_manager.py (additions)
from tools.manager import ToolManager
from tools.registry import ToolRegistry
from tools.context import ExecutionContext

class AgentExecutionManager:
    def __init__(self, db: Session):
        # ... existing init ...
        self.tool_registry = ToolRegistry()
        self.tool_registry.discover()
        self.tool_manager = ToolManager(
            self.tool_registry,
            PermissionValidator(db)
        )
    
    async def _execute_with_retry(self, ...):
        # ... existing code ...
        
        # NEW: Check if agent wants to invoke a tool
        # This would be triggered by the LLM response containing tool calls
        if self._should_invoke_tool(response):
            tool_result = await self._invoke_tool(response.tool_call, execution_context)
            # Feed tool result back into conversation
            messages.append({"role": "tool", "content": tool_result, "tool_call_id": ...})
            # Continue execution loop
```

### 9.2 Tool Invocation Flow

```
AgentExecutionManager.execute()
    │
    ├─► AIRuntime.chat() → LLM Response
    │
    ├─► Parse LLM response for tool calls
    │
    ├─► For each tool_call:
    │     ├─► Create ExecutionContext (shared)
    │     ├─► ToolManager.execute(tool_id, input, context)
    │     │     ├─► Permission check
    │     │     ├─► Input validation
    │     │     ├─► Execute with retries/cancellation
    │     │     ├─► Output validation
    │     │     └─► Log execution
    │     └─► Append tool result to messages
    │
    └─► Continue loop (LLM sees tool results, responds)
```

---

## 10. Schemas

```python
# backend/schemas/tool.py
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

class ToolMetadataResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    category: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    timeout: float
    supports_streaming: bool
    supports_cancellation: bool
    permissions: List[str]

class ToolResponse(BaseModel):
    metadata: ToolMetadataResponse
    
    @classmethod
    def from_tool(cls, tool: "BaseTool") -> "ToolResponse":
        meta = tool.metadata
        return cls(metadata=ToolMetadataResponse(
            id=meta.id,
            name=meta.name,
            description=meta.description,
            version=meta.version,
            category=meta.category,
            input_schema=meta.input_schema,
            output_schema=meta.output_schema,
            timeout=meta.timeout,
            supports_streaming=meta.supports_streaming,
            supports_cancellation=meta.supports_cancellation,
            permissions=meta.permissions or []
        ))

class ToolExecuteRequest(BaseModel):
    execution_id: str
    agent_id: int
    conversation_id: Optional[int] = None
    workspace_id: Optional[int] = None
    input_data: Dict[str, Any]

class ToolExecuteResponse(BaseModel):
    execution_id: str
    tool_id: str
    status: str  # "completed" | "failed" | "cancelled"
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
```

---

## 11. Module Registration

```python
# backend/tools/__init__.py
from .base import BaseTool, ToolMetadata
from .registry import ToolRegistry
from .manager import ToolManager, ToolExecutionConfig
from .context import ExecutionContext
from .schemas import ToolResponse, ToolExecuteRequest, ToolExecuteResponse

__all__ = [
    "BaseTool",
    "ToolMetadata",
    "ToolRegistry",
    "ToolManager",
    "ToolExecutionConfig",
    "ExecutionContext",
    "ToolResponse",
    "ToolExecuteRequest",
    "ToolExecuteResponse",
]

# backend/services/__init__.py (add)
from tools import ToolManager, ToolRegistry, ExecutionContext

# backend/api/__init__.py (add)
from .tools import router as tools_router
api_router.include_router(tools_router, prefix="", tags=["tools"])

# backend/schemas/__init__.py (add)
from .tool import ToolResponse, ToolExecuteRequest, ToolExecuteResponse
```

---

## 12. Database Model (Optional Persistence)

```python
# backend/models/tool_execution.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum, ForeignKey, Float
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class ToolExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ToolExecution(BaseModel):
    __tablename__ = "tool_executions"
    
    execution_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(100), nullable=False, index=True)
    agent_execution_id = Column(String(36), ForeignKey("execution_logs.execution_id"), nullable=True)
    
    status = Column(SQLEnum(ToolExecutionStatus), default=ToolExecutionStatus.PENDING, index=True)
    
    input_data = Column(Text, nullable=True)  # JSON
    output_data = Column(Text, nullable=True)  # JSON
    error_message = Column(Text, nullable=True)
    
    duration_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
```

---

## 13. Migration Plan

1. **Create tool infrastructure** (`tools/` directory, base classes, registry, manager)
2. **Implement 6 placeholder tools** in `tools/builtins/`
3. **Add ToolExecution model + migration** (if persistence needed)
4. **Create API endpoints** in `api/tools.py`
5. **Register modules** in `__init__.py` files
6. **Integrate ToolManager into AgentExecutionManager** (minimal changes)
7. **Write unit tests** for registry, manager, permissions, cancellation, retries
8. **Run full test suite** — ensure all 82 existing tests + new tool tests pass

---

## 14. Test Plan

| Test File | Coverage |
|-----------|----------|
| `tests/test_tool_registry.py` | Auto-discovery, registration, lookup by id/name/category |
| `tests/test_tool_manager.py` | Execute, stream, cancel, retry, permission validation, logging |
| `tests/test_tool_permissions.py` | Permission grants/denials, scope checking |
| `tests/test_builtin_tools.py` | Each placeholder tool executes without error |
| `tests/test_tool_api.py` | List, get, execute, cancel endpoints |
| `tests/test_agent_tool_integration.py` | AgentExecutionManager → ToolManager flow |

---

## 15. Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking Phase 6 Agent Runtime | Minimal integration — only add ToolManager as dependency, no changes to execution state machine |
| Tool execution blocking agent | All tool execution is async with timeout/cancellation support |
| Permission bypass | Centralized PermissionValidator, checked on every execute() |
| Schema drift | JSON Schema validation on input/output for every tool |
| Tool discovery failures | Explicit registry.discover() at startup, clear error messages |

---

## 16. Future Extensibility

- **Plugin packages**: External packages can register tools via entry points
- **Tool composition**: Tools can invoke other tools via ToolManager
- **Workflow tools**: Multi-step tools with checkpointing
- **Remote tools**: gRPC/HTTP adapters for distributed tool execution
- **Tool marketplace**: Install/uninstall tools at runtime

---

## 17. Acceptance Criteria

- [ ] `ToolRegistry.discover()` finds all 6 builtin tools
- [ ] `ToolManager.execute()` runs tool with retries, cancellation, logging
- [ ] Permission validation blocks unauthorized tool calls
- [ ] API endpoints return correct schemas and execute tools
- [ ] AgentExecutionManager can invoke tools during execution loop
- [ ] All 82 existing tests pass
- [ ] New tool tests pass (target: 20+ new tests)
- [ ] Code passes `black`, `isort`, `mypy` (if configured)