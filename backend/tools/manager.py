"""Tool Manager — orchestrates tool execution with lifecycle, retries, cancellation, and logging."""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional

from .base import BaseTool, ToolMetadata
from .context import ExecutionContext
from .permissions import PermissionValidator
from .registry import ToolRegistry

logger = logging.getLogger("tool_manager")


@dataclass
class ToolExecutionConfig:
    """Configuration for tool execution behavior."""

    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential_base: float = 2.0


@dataclass
class ToolExecutionRecord:
    """In-memory record of a tool execution."""

    execution_id: str
    tool_id: str
    status: str  # "pending" | "running" | "completed" | "failed" | "cancelled"
    input_data: Dict[str, Any]
    output_data: Optional[Any] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    retry_count: int = 0
    start_time: float = 0.0


class ToolManager:
    """Orchestrates tool execution with full lifecycle management.

    Responsibilities:
    - Tool lookup via ToolRegistry
    - Permission validation via PermissionValidator
    - Input/output schema validation
    - Execution with retry (exponential backoff)
    - Cancellation via asyncio.Event
    - Structured logging of every execution
    """

    def __init__(
        self,
        registry: ToolRegistry,
        permission_validator: Optional[PermissionValidator] = None,
        config: Optional[ToolExecutionConfig] = None,
    ):
        self.registry = registry
        self.permission_validator = permission_validator or PermissionValidator()
        self.config = config or ToolExecutionConfig()
        self._active_executions: Dict[str, "ToolExecutionContext"] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Any:
        """Execute a tool with full lifecycle management.

        Lifecycle:
        1. Lookup tool in registry
        2. Validate permissions
        3. Validate input against schema
        4. Execute with retries and cancellation checks
        5. Validate output against schema
        6. Log execution record

        Args:
            tool_id: The tool's unique identifier
            input_data: Input matching the tool's input_schema
            context: Shared execution context

        Returns:
            Output data matching the tool's output_schema

        Raises:
            ValueError: If tool not found
            PermissionError: If permissions insufficient
            asyncio.CancelledError: If cancelled during execution
            Exception: Any error from the tool itself
        """
        tool = self._resolve_tool(tool_id)

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
            start_time=time.monotonic(),
        )
        self._active_executions[exec_id] = exec_ctx

        context.log(f"Tool execution started: tool={tool_id} exec_id={exec_id}")

        try:
            # Execute with retries
            result = await self._execute_with_retry(exec_ctx, input_data)

            # Output validation
            tool.validate_output(result)

            # Log success
            self._log_execution(exec_ctx, "completed", result=result)
            context.log(f"Tool execution completed: tool={tool_id} exec_id={exec_id}")
            return result

        except asyncio.CancelledError:
            self._log_execution(exec_ctx, "cancelled")
            context.log(f"Tool execution cancelled: tool={tool_id} exec_id={exec_id}")
            raise

        except Exception as exc:
            self._log_execution(exec_ctx, "failed", error=exc)
            context.log(
                f"Tool execution failed: tool={tool_id} exec_id={exec_id} error={exc}",
                level=logging.ERROR,
            )
            raise

        finally:
            self._active_executions.pop(exec_id, None)

    async def execute_stream(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> AsyncGenerator[str, None]:
        """Execute a streaming tool.

        Args:
            tool_id: The tool's unique identifier
            input_data: Input matching the tool's input_schema
            context: Shared execution context

        Yields:
            JSON-encoded string chunks from the tool

        Raises:
            ValueError: If tool not found or doesn't support streaming
        """
        tool = self._resolve_tool(tool_id)

        if not tool.metadata.supports_streaming:
            raise ValueError(f"Tool '{tool_id}' does not support streaming")

        # Permission check
        self.permission_validator.validate(context, tool.metadata.permissions)

        # Input validation
        tool.validate_input(input_data)

        exec_id = str(uuid.uuid4())
        exec_ctx = ToolExecutionContext(
            execution_id=exec_id,
            tool=tool,
            context=context,
            cancel_event=asyncio.Event(),
            start_time=time.monotonic(),
        )
        self._active_executions[exec_id] = exec_ctx

        context.log(f"Tool stream started: tool={tool_id} exec_id={exec_id}")

        try:
            async for chunk in tool.execute_stream(input_data, context):
                if exec_ctx.cancel_event.is_set():
                    raise asyncio.CancelledError()
                yield chunk

            self._log_execution(exec_ctx, "completed")
            context.log(f"Tool stream completed: tool={tool_id} exec_id={exec_id}")

        except asyncio.CancelledError:
            self._log_execution(exec_ctx, "cancelled")
            context.log(f"Tool stream cancelled: tool={tool_id} exec_id={exec_id}")
            raise

        except Exception as exc:
            self._log_execution(exec_ctx, "failed", error=exc)
            context.log(
                f"Tool stream failed: tool={tool_id} exec_id={exec_id} error={exc}",
                level=logging.ERROR,
            )
            raise

        finally:
            self._active_executions.pop(exec_id, None)

    def cancel(self, execution_id: str) -> bool:
        """Cancel an active tool execution.

        Args:
            execution_id: The execution ID to cancel

        Returns:
            True if the execution was found and cancellation was signaled,
            False if the execution was not found
        """
        exec_ctx = self._active_executions.get(execution_id)
        if exec_ctx and exec_ctx.tool.metadata.supports_cancellation:
            exec_ctx.cancel_event.set()
            # Also set the shared ExecutionContext's cancel_event so the tool's
            # context.check_cancellation() will raise CancelledError
            exec_ctx.context.cancel_event.set()
            logger.info("Cancellation signal sent to tool execution %s", execution_id)
            return True

        if not exec_ctx:
            logger.warning("Tool execution %s not found for cancellation", execution_id)
        else:
            logger.warning(
                "Tool %s does not support cancellation", exec_ctx.tool.metadata.id
            )

        return False

    def get_active_executions(self) -> List[str]:
        """Get list of active tool execution IDs."""
        return list(self._active_executions.keys())

    def get_execution_status(self, execution_id: str) -> Optional[str]:
        """Get the status of a tool execution."""
        exec_ctx = self._active_executions.get(execution_id)
        if exec_ctx:
            return exec_ctx.record.status
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_tool(self, tool_id: str) -> BaseTool:
        """Resolve a tool by ID, raising if not found."""
        tool = self.registry.get(tool_id)
        if not tool:
            raise ValueError(f"Tool '{tool_id}' not found in registry")
        return tool

    async def _execute_with_retry(
        self,
        exec_ctx: "ToolExecutionContext",
        input_data: Dict[str, Any],
    ) -> Any:
        """Execute with exponential backoff retry logic."""
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            # Check cancellation before each attempt
            if exec_ctx.cancel_event.is_set():
                raise asyncio.CancelledError()

            try:
                result = await exec_ctx.tool.execute(input_data, exec_ctx.context)
                exec_ctx.record.retry_count = attempt
                return result

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                last_error = exc
                exec_ctx.record.retry_count = attempt

                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay
                        * (self.config.exponential_base**attempt),
                        self.config.max_delay,
                    )
                    logger.warning(
                        "Tool %s attempt %d/%d failed: %s. Retrying in %.1fs...",
                        exec_ctx.tool.metadata.id,
                        attempt + 1,
                        self.config.max_retries + 1,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "Tool %s exhausted all %d retries. Last error: %s",
                        exec_ctx.tool.metadata.id,
                        self.config.max_retries + 1,
                        exc,
                    )

        raise last_error  # type: ignore[misc]

    def _log_execution(
        self,
        exec_ctx: "ToolExecutionContext",
        status: str,
        result: Any = None,
        error: Exception = None,
    ) -> None:
        """Record execution metrics and log."""
        duration_ms = int((time.monotonic() - exec_ctx.start_time) * 1000)

        exec_ctx.record.status = status
        exec_ctx.record.duration_ms = duration_ms

        if result is not None:
            exec_ctx.record.output_data = result

        if error is not None:
            exec_ctx.record.error_message = str(error)

        logger.info(
            "Tool execution %s: tool=%s status=%s duration_ms=%d retries=%d",
            exec_ctx.execution_id,
            exec_ctx.tool.metadata.id,
            status,
            duration_ms,
            exec_ctx.record.retry_count,
        )


@dataclass
class ToolExecutionContext:
    """Internal context for a single tool execution within ToolManager."""

    execution_id: str
    tool: BaseTool
    context: ExecutionContext
    cancel_event: asyncio.Event
    start_time: float
    record: ToolExecutionRecord = field(init=False)

    def __post_init__(self):
        self.record = ToolExecutionRecord(
            execution_id=self.execution_id,
            tool_id=self.tool.metadata.id,
            status="running",
            input_data={},
            start_time=self.start_time,
        )