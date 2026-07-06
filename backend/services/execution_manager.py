"""Agent Execution Manager — the core orchestration service for the Agent Runtime.

Coordinates the full execution lifecycle:
1. Creates execution records with unique execution IDs
2. Manages the state machine (IDLE → QUEUED → RUNNING → WAITING_FOR_TOOL → COMPLETED/FAILED/CANCELLED)
3. Resolves agent configuration and builds prompts
4. Executes via AIRuntime with retry/fallback policies
5. Persists execution logs with metrics, token usage, and error details
6. Supports both streaming and non-streaming execution
7. Provides cancellation for active executions
8. Integrates with Tool Runtime for agent-initiated tool calls
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

from agents.manager import AgentManager
from models.agent import Agent
from models.execution import Execution, ExecutionStatus
from services.ai_runtime import AIRuntime
from services.retry_policy import FallbackPolicy, RetryPolicy
from services.usage_tracker import UsageTracker
from sqlalchemy.orm import Session

# Tool Runtime integration
from tools.context import ExecutionContext as ToolExecutionContext
from tools.manager import ToolManager
from tools.permissions import PermissionValidator
from tools.registry import ToolRegistry

logger = logging.getLogger("execution_manager")

# In-memory registry of active executions for cancellation support
_active_executions: Dict[str, "ExecutionContext"] = {}

# Singleton Tool Runtime (lazy-initialized)
_tool_registry: Optional[ToolRegistry] = None
_tool_manager: Optional[ToolManager] = None


def _get_tool_manager() -> ToolManager:
    """Get or create the singleton ToolManager with auto-discovered tools."""
    global _tool_registry, _tool_manager
    if _tool_manager is None:
        _tool_registry = ToolRegistry()
        _tool_registry.discover("tools.builtins")
        _tool_manager = ToolManager(
            registry=_tool_registry,
            permission_validator=PermissionValidator(),
        )
    return _tool_manager


class ExecutionContext:
    """Holds runtime state for an active execution."""

    def __init__(self, execution: Execution):
        self.execution = execution
        self.cancel_event = asyncio.Event()
        self.start_time: Optional[float] = None


class AgentExecutionManager:
    """Coordinates the full agent execution lifecycle.

    Wraps AgentManager, AIRuntime, and UsageTracker with:
    - Execution state machine
    - Retry and fallback policies
    - Execution log persistence
    - Cancellation support
    - Tool Runtime integration for agent-initiated tool calls
    """

    def __init__(self, db: Session):
        # --- RUNTIME VERIFICATION (diagnostic only) ---
        print("=" * 80)
        print("EXECUTION MANAGER CREATED")
        print("__file__ =", __file__)
        print("Class id:", id(self))
        # --- END RUNTIME VERIFICATION ---
        self.db = db
        self.agent_manager = AgentManager(db)
        self.ai_runtime = AIRuntime(db)
        self.usage_tracker = UsageTracker(db)
        self.retry_policy = RetryPolicy()
        self.fallback_policy = FallbackPolicy(db)
        self._tool_manager: Optional[ToolManager] = None

    @property
    def tool_manager(self) -> ToolManager:
        """Lazy-loaded ToolManager for agent-initiated tool calls."""
        if self._tool_manager is None:
            self._tool_manager = _get_tool_manager()
        return self._tool_manager

    # ------------------------------------------------------------------
    # Execution lifecycle: create → submit → execute → complete/fail
    # ------------------------------------------------------------------

    def create_execution(
        self,
        agent_id: int,
        conversation_id: Optional[int] = None,
        input_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> Execution:
        """Create a new execution record in IDLE state.

        Args:
            agent_id: The agent to execute
            conversation_id: Optional conversation context
            input_messages: The message list to send (before prompt assembly)

        Returns:
            The persisted Execution record with a unique execution_id
        """
        execution_id = str(uuid.uuid4())

        execution = Execution(
            execution_id=execution_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            status=ExecutionStatus.IDLE,
            input_messages=json.dumps(input_messages) if input_messages else None,
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        logger.info(
            "Created execution %s for agent_id=%d conversation_id=%s",
            execution_id,
            agent_id,
            conversation_id,
        )
        return execution

    def submit(self, execution_id: str) -> Execution:
        """Transition an execution from IDLE to QUEUED.

        Args:
            execution_id: The UUID of the execution to submit

        Returns:
            The updated Execution record

        Raises:
            ValueError: If execution not found or not in IDLE state
        """
        execution = self._get_execution(execution_id)

        if execution.status != ExecutionStatus.IDLE:
            raise ValueError(
                f"Cannot submit execution in status '{execution.status}'. "
                f"Expected '{ExecutionStatus.IDLE}'."
            )

        execution.status = ExecutionStatus.QUEUED
        self.db.commit()
        self.db.refresh(execution)

        logger.info("Execution %s submitted (IDLE → QUEUED)", execution_id)
        return execution

    async def execute(
        self,
        execution_id: str,
        provider_id_override: Optional[int] = None,
        model_override: Optional[str] = None,
    ) -> Execution:
        """Execute a queued execution (non-streaming).

        Full lifecycle:
        1. QUEUED → RUNNING
        2. Resolve agent, get config, validate
        3. Build prompt with execution context
        4. Call provider via AIRuntime with retry/fallback
        5. Record metrics, token usage
        6. RUNNING → COMPLETED or FAILED

        Args:
            execution_id: The UUID of the execution to run
            provider_id_override: Optional provider_id from the HTTP request
                that takes precedence over the agent's configured provider_id.
            model_override: Optional model name from the HTTP request that
                takes precedence over the agent's configured model.

        Returns:
            The completed/failed Execution record
        """
        execution = self._get_execution(execution_id)

        if execution.status != ExecutionStatus.QUEUED:
            raise ValueError(
                f"Cannot execute in status '{execution.status}'. "
                f"Expected '{ExecutionStatus.QUEUED}'."
            )

        # Transition to RUNNING
        self._transition_status(execution, ExecutionStatus.RUNNING)
        start_time = time.monotonic()

        # Register for cancellation
        ctx = ExecutionContext(execution)
        ctx.start_time = start_time
        _active_executions[execution_id] = ctx

        try:
            # Resolve agent and config
            agent = self.agent_manager.resolve_agent(execution.agent_id)
            config = self.agent_manager.get_agent_config(execution.agent_id)
            # Request overrides take precedence over agent config so that
            # callers can supply provider_id/model even when the agent row
            # has them set to NULL (nullable columns per models/agent.py).
            # Use explicit "is not None" checks so a legitimate provider_id
            # of 0 is not discarded by a falsy `or` fallback.
            provider_id = (
                provider_id_override
                if provider_id_override is not None
                else config["provider_id"]
            )
            model = (
                model_override
                if model_override is not None
                else config["model"]
            )

            # Defensive validation: fail fast with a clear error instead of
            # the opaque "Provider with ID None does not exist." downstream.
            if provider_id is None:
                raise RuntimeError(
                    "Execution started without a provider_id. "
                    "Neither request override nor agent configuration "
                    "supplied one."
                )

            # Validate
            self.agent_manager.validate_execution(provider_id, model)

            # Build prompt
            input_msgs = self._parse_input_messages(execution.input_messages)
            messages = self.agent_manager.build_prompt_for_agent(
                execution.agent_id, input_msgs
            )
            execution.system_prompt = self._extract_system_prompt(messages)
            execution.provider_id = provider_id
            execution.model = model
            execution.max_retries = self.retry_policy.max_retries

            # Execute with retry/fallback
            response = await self._execute_with_retry(
                execution=execution,
                messages=messages,
                provider_id=provider_id,
                model=model,
                config=config,
                agent=agent.agent_model,
            )

            # Success — record metrics
            execution.output_response = response
            execution.latency_ms = int((time.monotonic() - start_time) * 1000)
            self._transition_status(execution, ExecutionStatus.COMPLETED)

            logger.info(
                "Execution %s completed successfully (latency=%dms)",
                execution_id,
                execution.latency_ms,
            )
            return execution

        except asyncio.CancelledError:
            self._transition_status(execution, ExecutionStatus.CANCELLED)
            logger.info("Execution %s cancelled", execution_id)
            return execution

        except Exception as exc:
            self._transition_status(execution, ExecutionStatus.FAILED)
            execution.error_message = str(exc)
            execution.latency_ms = int((time.monotonic() - start_time) * 1000)
            logger.exception("Execution %s failed: %s", execution_id, exc)
            return execution

        finally:
            _active_executions.pop(execution_id, None)

    async def execute_stream(
        self,
        execution_id: str,
        provider_id_override: Optional[int] = None,
        model_override: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Execute a queued execution with streaming response.

        Yields response chunks as they arrive from the provider.
        On completion, the full response is stored on the execution record.

        Args:
            execution_id: The UUID of the execution to run
            provider_id_override: Optional provider_id from the HTTP request
                that takes precedence over the agent's configured provider_id.
            model_override: Optional model name from the HTTP request that
                takes precedence over the agent's configured model.

        Yields:
            Response text chunks from the provider
        """
        # --- RUNTIME VERIFICATION (diagnostic only) ---
        import inspect as _inspect
        print("=" * 80)
        print("EXECUTE_STREAM ENTERED")
        print("__file__ =", __file__)
        print("Function signature:")
        print(_inspect.signature(self.execute_stream))
        print("execution_id =", execution_id)
        print("provider_id_override =", provider_id_override)
        print("model_override =", model_override)
        # --- END RUNTIME VERIFICATION ---
        execution = self._get_execution(execution_id)

        if execution.status != ExecutionStatus.QUEUED:
            raise ValueError(
                f"Cannot execute in status '{execution.status}'. "
                f"Expected '{ExecutionStatus.QUEUED}'."
            )

        # Transition to RUNNING
        self._transition_status(execution, ExecutionStatus.RUNNING)
        start_time = time.monotonic()

        # Register for cancellation
        ctx = ExecutionContext(execution)
        ctx.start_time = start_time
        _active_executions[execution_id] = ctx

        full_response = ""
        chunk_count = 0

        try:
            # Resolve agent and config
            agent = self.agent_manager.resolve_agent(execution.agent_id)
            config = self.agent_manager.get_agent_config(execution.agent_id)
            # Request overrides take precedence over agent config so that
            # callers can supply provider_id/model even when the agent row
            # has them set to NULL (nullable columns per models/agent.py).
            # Use explicit "is not None" checks so a legitimate provider_id
            # of 0 is not discarded by a falsy `or` fallback.
            provider_id = (
                provider_id_override
                if provider_id_override is not None
                else config["provider_id"]
            )
            model = (
                model_override
                if model_override is not None
                else config["model"]
            )

            # Defensive validation: fail fast with a clear error instead of
            # the opaque "Provider with ID None does not exist." downstream.
            if provider_id is None:
                raise RuntimeError(
                    "Execution started without a provider_id. "
                    "Neither request override nor agent configuration "
                    "supplied one."
                )

            # --- RUNTIME VERIFICATION (diagnostic only) ---
            print("=" * 80)
            print("ABOUT TO VALIDATE")
            print("provider_id =", provider_id)
            print("model =", model)
            # --- END RUNTIME VERIFICATION ---
            # Validate
            self.agent_manager.validate_execution(provider_id, model)

            # Build prompt
            input_msgs = self._parse_input_messages(execution.input_messages)
            messages = self.agent_manager.build_prompt_for_agent(
                execution.agent_id, input_msgs
            )
            execution.system_prompt = self._extract_system_prompt(messages)
            execution.provider_id = provider_id
            execution.model = model
            execution.max_retries = self.retry_policy.max_retries

            # Stream with retry/fallback
            cancelled = False
            async for chunk in self._stream_with_retry(
                execution=execution,
                messages=messages,
                provider_id=provider_id,
                model=model,
                config=config,
                agent=agent.agent_model,
                cancel_event=ctx.cancel_event,
            ):
                # Check cancellation between chunks
                if ctx.cancel_event.is_set():
                    logger.info("Execution %s cancelled during streaming", execution_id)
                    self._transition_status(execution, ExecutionStatus.CANCELLED)
                    cancelled = True
                    return

                full_response += chunk
                chunk_count += 1
                yield chunk

            # If cancelled, don't run success path
            if cancelled:
                return

            # Success — record metrics
            execution.output_response = full_response
            execution.streaming_chunks = chunk_count
            execution.latency_ms = int((time.monotonic() - start_time) * 1000)
            self._transition_status(execution, ExecutionStatus.COMPLETED)

            logger.info(
                "Execution %s stream completed (chunks=%d, latency=%dms)",
                execution_id,
                chunk_count,
                execution.latency_ms,
            )

        except asyncio.CancelledError:
            self._transition_status(execution, ExecutionStatus.CANCELLED)
            execution.output_response = full_response  # Save partial
            logger.info("Execution %s cancelled", execution_id)

        except Exception as exc:
            self._transition_status(execution, ExecutionStatus.FAILED)
            execution.error_message = str(exc)
            execution.output_response = full_response  # Save partial
            execution.latency_ms = int((time.monotonic() - start_time) * 1000)
            logger.exception("Execution %s stream failed: %s", execution_id, exc)

        finally:
            _active_executions.pop(execution_id, None)

    def cancel(self, execution_id: str) -> Execution:
        """Cancel an active execution.

        Can cancel executions in QUEUED, RUNNING, or WAITING_FOR_TOOL states.
        For streaming executions, signals the cancel_event to break the stream loop.
        For non-streaming, only QUEUED state can be cancelled.

        Args:
            execution_id: The UUID of the execution to cancel

        Returns:
            The updated Execution record

        Raises:
            ValueError: If execution not found or in a terminal state
        """
        execution = self._get_execution(execution_id)

        cancellable_states = {
            ExecutionStatus.QUEUED,
            ExecutionStatus.RUNNING,
            ExecutionStatus.WAITING_FOR_TOOL,
        }

        if execution.status not in cancellable_states:
            raise ValueError(
                f"Cannot cancel execution in terminal state '{execution.status}'. "
                f"Must be one of: {', '.join(s.value for s in cancellable_states)}."
            )

        # Signal cancellation for streaming executions
        ctx = _active_executions.get(execution_id)
        if ctx:
            ctx.cancel_event.set()
            logger.info("Cancellation signal sent to execution %s", execution_id)

        self._transition_status(execution, ExecutionStatus.CANCELLED)
        logger.info("Execution %s cancelled", execution_id)
        return execution

    # ------------------------------------------------------------------
    # Tool Runtime Integration
    # ------------------------------------------------------------------

    async def execute_tool(
        self,
        execution_id: str,
        tool_id: str,
        input_data: Dict[str, Any],
    ) -> Any:
        """Execute a tool on behalf of an agent execution.

        This is the bridge between Agent Runtime and Tool Runtime.
        Agents invoke tools through this method, which:
        1. Validates the execution is in RUNNING or WAITING_FOR_TOOL state
        2. Transitions to WAITING_FOR_TOOL while the tool runs
        3. Builds a shared ExecutionContext bridging both runtimes
        4. Delegates to ToolManager.execute() for full lifecycle
        5. Transitions back to RUNNING on completion

        Args:
            execution_id: The agent execution UUID
            tool_id: The tool's unique identifier (e.g., "browser.navigate")
            input_data: Input matching the tool's input_schema

        Returns:
            Tool output data matching the tool's output_schema

        Raises:
            ValueError: If execution not found or in invalid state
            PermissionError: If agent lacks required permissions
            Exception: Any error from the tool itself
        """
        execution = self._get_execution(execution_id)

        # Validate execution state
        allowed_states = {ExecutionStatus.RUNNING, ExecutionStatus.WAITING_FOR_TOOL}
        if execution.status not in allowed_states:
            raise ValueError(
                f"Cannot execute tool in execution status '{execution.status}'. "
                f"Expected one of: {', '.join(s.value for s in allowed_states)}."
            )

        # Transition to WAITING_FOR_TOOL
        previous_status = execution.status
        self._transition_status(execution, ExecutionStatus.WAITING_FOR_TOOL)

        # Build shared ExecutionContext (Tool Runtime version)
        ctx = _active_executions.get(execution_id)
        tool_context = ToolExecutionContext(
            execution_id=execution_id,
            agent_id=execution.agent_id,
            conversation_id=execution.conversation_id,
            workspace_id=None,  # Future: resolve from execution context
            cancel_event=ctx.cancel_event if ctx else asyncio.Event(),
            logger=logger,
        )

        try:
            # Delegate to ToolManager for full lifecycle
            result = await self.tool_manager.execute(
                tool_id=tool_id,
                input_data=input_data,
                context=tool_context,
            )

            # Record tool usage on execution
            tool_calls = execution.tool_calls or []
            tool_calls.append({
                "tool_id": tool_id,
                "input": input_data,
                "output": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            execution.tool_calls = tool_calls
            self.db.commit()

            logger.info(
                "Execution %s tool call completed: tool=%s",
                execution_id,
                tool_id,
            )
            return result

        except Exception as exc:
            # Record failed tool call
            tool_calls = execution.tool_calls or []
            tool_calls.append({
                "tool_id": tool_id,
                "input": input_data,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            execution.tool_calls = tool_calls
            self.db.commit()

            logger.error(
                "Execution %s tool call failed: tool=%s error=%s",
                execution_id,
                tool_id,
                exc,
            )
            raise

        finally:
            # Transition back to previous state (RUNNING)
            self._transition_status(execution, previous_status)

    async def execute_tool_stream(
        self,
        execution_id: str,
        tool_id: str,
        input_data: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """Execute a streaming tool on behalf of an agent execution.

        Similar to execute_tool() but yields chunks for streaming tools.

        Args:
            execution_id: The agent execution UUID
            tool_id: The tool's unique identifier
            input_data: Input matching the tool's input_schema

        Yields:
            JSON-encoded string chunks from the tool
        """
        execution = self._get_execution(execution_id)

        allowed_states = {ExecutionStatus.RUNNING, ExecutionStatus.WAITING_FOR_TOOL}
        if execution.status not in allowed_states:
            raise ValueError(
                f"Cannot execute tool in execution status '{execution.status}'."
            )

        previous_status = execution.status
        self._transition_status(execution, ExecutionStatus.WAITING_FOR_TOOL)

        ctx = _active_executions.get(execution_id)
        tool_context = ToolExecutionContext(
            execution_id=execution_id,
            agent_id=execution.agent_id,
            conversation_id=execution.conversation_id,
            workspace_id=None,
            cancel_event=ctx.cancel_event if ctx else asyncio.Event(),
            logger=logger,
        )

        full_output = ""
        try:
            async for chunk in self.tool_manager.execute_stream(
                tool_id=tool_id,
                input_data=input_data,
                context=tool_context,
            ):
                full_output += chunk
                yield chunk

            # Record successful tool call
            tool_calls = execution.tool_calls or []
            tool_calls.append({
                "tool_id": tool_id,
                "input": input_data,
                "output": full_output,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            execution.tool_calls = tool_calls
            self.db.commit()

        except Exception as exc:
            tool_calls = execution.tool_calls or []
            tool_calls.append({
                "tool_id": tool_id,
                "input": input_data,
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            execution.tool_calls = tool_calls
            self.db.commit()
            raise

        finally:
            self._transition_status(execution, previous_status)

    def list_available_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tools available to agents through the Tool Runtime.

        Args:
            category: Optional category filter

        Returns:
            List of tool metadata dicts suitable for prompt assembly
        """
        tools = self.tool_manager.registry.list_tools(category=category)
        return [
            {
                "id": t.metadata.id,
                "name": t.metadata.name,
                "description": t.metadata.description,
                "category": t.metadata.category,
                "input_schema": t.metadata.input_schema,
                "supports_streaming": t.metadata.supports_streaming,
                "permissions": t.metadata.permissions,
            }
            for t in tools
        ]

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_execution(self, execution_id: str) -> Optional[Execution]:
        """Get an execution by its UUID."""
        return (
            self.db.query(Execution)
            .filter(Execution.execution_id == execution_id)
            .first()
        )

    def list_active_executions(self) -> List[Execution]:
        """List all executions in non-terminal states."""
        terminal_states = {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        }
        return (
            self.db.query(Execution)
            .filter(Execution.status.notin_(terminal_states))
            .order_by(Execution.created_at.desc())
            .all()
        )

    def get_execution_history(
        self,
        agent_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Execution]:
        """Get historical executions with optional agent filter."""
        query = self.db.query(Execution).order_by(Execution.created_at.desc())

        if agent_id is not None:
            query = query.filter(Execution.agent_id == agent_id)

        return query.offset(offset).limit(limit).all()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_execution(self, execution_id: str) -> Execution:
        """Get execution or raise ValueError."""
        execution = self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution '{execution_id}' not found")
        return execution

    def _transition_status(
        self, execution: Execution, new_status: ExecutionStatus
    ) -> None:
        """Transition execution to a new status and persist."""
        now = datetime.now(timezone.utc)

        execution.status = new_status

        if new_status == ExecutionStatus.RUNNING:
            execution.started_at = now
        elif new_status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        ):
            execution.completed_at = now

        self.db.commit()
        self.db.refresh(execution)

        logger.debug(
            "Execution %s status: %s → %s",
            execution.execution_id,
            execution.status,
            new_status,
        )

    async def _execute_with_retry(
        self,
        execution: Execution,
        messages: List[Dict[str, Any]],
        provider_id: int,
        model: str,
        config: Dict[str, Any],
        agent: Agent,
    ) -> str:
        """Call AIRuntime.chat() with retry and fallback logic.

        On failure:
        1. Check RetryPolicy.should_retry()
        2. If retryable: wait with exponential backoff, retry same provider
        3. If retries exhausted: check FallbackPolicy.get_fallback()
        4. If fallback available: try fallback provider
        5. If all fail: raise the last error
        """
        last_error = None
        current_provider_id = provider_id
        current_model = model
        fallback_used = False

        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                # Build kwargs from agent config (exclude provider_id and model)
                kwargs = {
                    k: v
                    for k, v in config.items()
                    if k not in ("provider_id", "model", "streaming") and v is not None
                }

                response = await self.ai_runtime.chat(
                    messages=messages,
                    provider_id=current_provider_id,
                    model=current_model,
                    **kwargs,
                )

                # Record retry/fallback info
                execution.retry_count = attempt
                if fallback_used:
                    execution.fallback_provider_id = current_provider_id
                    execution.fallback_model = current_model

                return response

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Execution %s attempt %d failed: %s",
                    execution.execution_id,
                    attempt + 1,
                    exc,
                )

                # Check if we should retry with same provider
                if self.retry_policy.should_retry(attempt, exc):
                    await self.retry_policy.wait_before_retry(attempt)
                    continue

                # Retries exhausted — try fallback
                if not fallback_used:
                    fallback = self.fallback_policy.get_fallback(
                        agent=agent,
                        primary_provider_id=current_provider_id,
                        primary_model=current_model,
                        failed_error=exc,
                    )
                    if fallback:
                        logger.info(
                            "Execution %s switching to fallback provider %d model %s",
                            execution.execution_id,
                            fallback["provider_id"],
                            fallback["model"],
                        )
                        current_provider_id = fallback["provider_id"]
                        current_model = fallback["model"]
                        fallback_used = True
                        # Reset attempt counter for fallback (give it fresh retries)
                        continue

                # No fallback available — re-raise
                raise

        # Should not reach here, but just in case
        raise last_error or RuntimeError("Execution failed with no error captured")

    async def _stream_with_retry(
        self,
        execution: Execution,
        messages: List[Dict[str, Any]],
        provider_id: int,
        model: str,
        config: Dict[str, Any],
        agent: Agent,
        cancel_event: asyncio.Event,
    ) -> AsyncGenerator[str, None]:
        """Call AIRuntime.stream() with retry and fallback logic.

        Yields chunks as they arrive. On failure, applies retry/fallback
        and resumes streaming from the new provider.
        """
        last_error = None
        current_provider_id = provider_id
        current_model = model
        fallback_used = False

        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                kwargs = {
                    k: v
                    for k, v in config.items()
                    if k not in ("provider_id", "model", "streaming") and v is not None
                }

                async for chunk in self.ai_runtime.stream(
                    messages=messages,
                    provider_id=current_provider_id,
                    model=current_model,
                    **kwargs,
                ):
                    if cancel_event.is_set():
                        raise asyncio.CancelledError("Execution cancelled")
                    yield chunk

                # Stream completed successfully
                execution.retry_count = attempt
                if fallback_used:
                    execution.fallback_provider_id = current_provider_id
                    execution.fallback_model = current_model
                return

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Execution %s stream attempt %d failed: %s",
                    execution.execution_id,
                    attempt + 1,
                    exc,
                )

                if self.retry_policy.should_retry(attempt, exc):
                    await self.retry_policy.wait_before_retry(attempt)
                    continue

                if not fallback_used:
                    fallback = self.fallback_policy.get_fallback(
                        agent=agent,
                        primary_provider_id=current_provider_id,
                        primary_model=current_model,
                        failed_error=exc,
                    )
                    if fallback:
                        logger.info(
                            "Execution %s stream switching to fallback provider %d model %s",
                            execution.execution_id,
                            fallback["provider_id"],
                            fallback["model"],
                        )
                        current_provider_id = fallback["provider_id"]
                        current_model = fallback["model"]
                        fallback_used = True
                        continue

                raise

        raise last_error or RuntimeError(
            "Stream execution failed with no error captured"
        )

    @staticmethod
    def _parse_input_messages(raw: Optional[str]) -> List[Dict[str, Any]]:
        """Parse JSON-serialized input messages."""
        if not raw:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse input_messages JSON")
            return []

    @staticmethod
    def _extract_system_prompt(messages: List[Dict[str, Any]]) -> Optional[str]:
        """Extract the system prompt from the message list."""
        for msg in messages:
            if msg.get("role") == "system":
                return msg.get("content")
        return None
