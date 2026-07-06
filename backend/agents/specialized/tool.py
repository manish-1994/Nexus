"""Tool Agent — system operations specialist.

Executes system operations: Python code, terminal commands, browser
navigation, and filesystem operations. Used by the Orchestrator when
a task requires direct system interaction or when other agents need
to delegate tool execution.
"""

import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from agents.base import BaseAgent
from agents.orchestration.agent_config import AgentConfig, AgentRole, DEFAULT_AGENTS
from agents.orchestration.event_bus import (
    EventBus,
    EventType,
    ExecutionEvent,
)
from models.agent import Agent
from services.ai_runtime import AIRuntime
from sqlalchemy.orm import Session

logger = logging.getLogger("tool_agent")


class ToolAgent(BaseAgent):
    """Agent that executes system tools and returns results.

    The Tool Agent is invoked for tasks requiring:
    - Python code execution
    - Terminal/shell command execution
    - Browser navigation and content extraction
    - Filesystem operations (read, write, list, delete)
    - Search across workspace and knowledge base
    - Memory management operations

    It has access to ALL tools and is the primary executor for
    system-level operations.
    """

    def __init__(
        self,
        db: Session,
        agent_model: Agent,
        config: Optional[AgentConfig] = None,
        event_bus: Optional[EventBus] = None,
    ):
        super().__init__(db, agent_model)
        self._config = config or DEFAULT_AGENTS.get("tool", AgentConfig(
            name="Tool Agent",
            role=AgentRole.TOOL,
        ))
        self._event_bus = event_bus

    # ------------------------------------------------------------------
    # Task execution
    # ------------------------------------------------------------------

    async def execute_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
        execution_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a tool task and return structured results.

        Args:
            task_description: What tool operation to perform
            context: Additional context (previous outputs, parameters)
            provider_id: Provider override
            model: Model override
            execution_id: For event emission
            task_id: For event emission

        Returns:
            Dict with keys: operations, summary
        """
        start_time = time.time()

        # Emit task started
        if self._event_bus and execution_id and task_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_STARTED,
                execution_id=execution_id,
                task_id=task_id,
                agent_role=AgentRole.TOOL.value,
                data={"description": task_description},
            ))

        messages = self._build_tool_messages(task_description, context)

        eff_provider_id = provider_id if provider_id is not None else self.agent_model.provider_id
        eff_model = model or self._config.preferred_model

        runtime = AIRuntime(self.db)
        try:
            response_text = await runtime.chat(
                messages=messages,
                provider_id=eff_provider_id,
                model=eff_model,
                temperature=self._config.temperature,
            )
        except Exception as exc:
            logger.exception("Tool agent LLM call failed: %s", exc)
            latency_ms = int((time.time() - start_time) * 1000)
            if self._event_bus and execution_id and task_id:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.TASK_FAILED,
                    execution_id=execution_id,
                    task_id=task_id,
                    agent_role=AgentRole.TOOL.value,
                    data={"error": str(exc), "latency_ms": latency_ms},
                ))
            return {
                "operations": [],
                "summary": f"Tool execution failed: {exc}",
                "error": str(exc),
            }

        result = self._parse_tool_output(response_text, task_description)
        latency_ms = int((time.time() - start_time) * 1000)

        # Emit task completed
        if self._event_bus and execution_id and task_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_COMPLETED,
                execution_id=execution_id,
                task_id=task_id,
                agent_role=AgentRole.TOOL.value,
                data={
                    "tokens_used": len(response_text) // 4,
                    "latency_ms": latency_ms,
                    "operation_count": len(result.get("operations", [])),
                },
            ))

        return result

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_tool_messages(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build messages for the tool LLM call."""
        system_prompt = self._config.system_prompt

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add context from previous tasks
        if context:
            tool_requests = context.get("tool_requests", [])
            workspace_info = context.get("workspace_info", "")
            previous_outputs = context.get("previous_outputs", "")

            context_parts = []
            if tool_requests:
                formatted = json.dumps(tool_requests, indent=2)
                context_parts.append(f"## Requested Tool Operations\n{formatted}")
            if workspace_info:
                context_parts.append(f"## Workspace Context\n{workspace_info}")
            if previous_outputs:
                context_parts.append(f"## Previous Outputs\n{previous_outputs}")

            if context_parts:
                messages.append({
                    "role": "system",
                    "content": "Context for tool execution:\n\n" + "\n\n".join(context_parts),
                })

        messages.append({
            "role": "user",
            "content": f"Tool task: {task_description}\n\nProvide your results in the specified JSON format.",
        })

        return messages

    def _parse_tool_output(
        self, response_text: str, task_description: str
    ) -> Dict[str, Any]:
        """Parse the LLM response into structured tool output."""
        try:
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            return {
                "operations": result.get("operations", []),
                "summary": result.get("summary", ""),
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "operations": [],
                "summary": response_text,
            }

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may contain markdown fences."""
        text = text.strip()
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace >= 0 and last_brace > first_brace:
            return text[first_brace:last_brace + 1]
        return text

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Non-streaming chat — executes a tool task."""
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        result = await self.execute_task(user_message, provider_id=provider_id, model=model)
        return {"content": json.dumps(result, indent=2), "result": result}

    async def stream(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat — yields tool result."""
        result = await self.chat(messages, provider_id, model)
        yield result["content"]

    def buildPrompt(
        self,
        messages: List[Dict[str, Any]],
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build prompt messages for tool execution."""
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        return self._build_tool_messages(user_message, execution_context)

    def validate(self) -> bool:
        """Validate Tool Agent configuration."""
        return bool(self._config.system_prompt)

    def getCapabilities(self) -> List[str]:
        """Get Tool Agent capabilities."""
        return self._config.capabilities