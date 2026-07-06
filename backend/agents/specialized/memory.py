"""Memory Agent — persistent knowledge specialist.

Retrieves relevant memories, stores new information, ranks by relevance,
and manages the persistent knowledge base. Used by the Orchestrator when
a task requires accessing past conversations, user preferences, or
stored knowledge.
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

logger = logging.getLogger("memory_agent")


class MemoryAgent(BaseAgent):
    """Agent that manages persistent memory and knowledge.

    The Memory Agent is invoked for tasks requiring:
    - Retrieving relevant past conversations
    - Storing new information for future use
    - Ranking memories by relevance
    - Updating outdated information
    - Managing user preferences and project context

    It has access to memory management and search tools.
    """

    def __init__(
        self,
        db: Session,
        agent_model: Agent,
        config: Optional[AgentConfig] = None,
        event_bus: Optional[EventBus] = None,
    ):
        super().__init__(db, agent_model)
        self._config = config or DEFAULT_AGENTS.get("memory", AgentConfig(
            name="Memory Agent",
            role=AgentRole.MEMORY,
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
        """Execute a memory task and return structured results.

        Args:
            task_description: What memory operation to perform
            context: Additional context (conversation, user info)
            provider_id: Provider override
            model: Model override
            execution_id: For event emission
            task_id: For event emission

        Returns:
            Dict with keys: operation, memories, summary
        """
        start_time = time.time()

        # Emit task started
        if self._event_bus and execution_id and task_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_STARTED,
                execution_id=execution_id,
                task_id=task_id,
                agent_role=AgentRole.MEMORY.value,
                data={"description": task_description},
            ))

        messages = self._build_memory_messages(task_description, context)

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
            logger.exception("Memory agent LLM call failed: %s", exc)
            latency_ms = int((time.time() - start_time) * 1000)
            if self._event_bus and execution_id and task_id:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.TASK_FAILED,
                    execution_id=execution_id,
                    task_id=task_id,
                    agent_role=AgentRole.MEMORY.value,
                    data={"error": str(exc), "latency_ms": latency_ms},
                ))
            return {
                "operation": "retrieve",
                "memories": [],
                "summary": f"Memory operation failed: {exc}",
                "error": str(exc),
            }

        result = self._parse_memory_output(response_text, task_description)
        latency_ms = int((time.time() - start_time) * 1000)

        # Emit task completed
        if self._event_bus and execution_id and task_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_COMPLETED,
                execution_id=execution_id,
                task_id=task_id,
                agent_role=AgentRole.MEMORY.value,
                data={
                    "tokens_used": len(response_text) // 4,
                    "latency_ms": latency_ms,
                    "operation": result.get("operation"),
                    "memory_count": len(result.get("memories", [])),
                },
            ))

        return result

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_memory_messages(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build messages for the memory LLM call."""
        system_prompt = self._config.system_prompt

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add conversation context for relevance
        if context:
            conversation_summary = context.get("conversation_summary", "")
            user_query = context.get("user_query", "")
            recent_messages = context.get("recent_messages", [])

            context_parts = []
            if conversation_summary:
                context_parts.append(f"## Conversation Summary\n{conversation_summary}")
            if user_query:
                context_parts.append(f"## Current User Query\n{user_query}")
            if recent_messages:
                formatted = "\n".join(
                    f"{m.get('role', 'unknown')}: {m.get('content', '')[:200]}"
                    for m in recent_messages[-5:]
                )
                context_parts.append(f"## Recent Messages\n{formatted}")

            if context_parts:
                messages.append({
                    "role": "system",
                    "content": "Context for memory operations:\n\n" + "\n\n".join(context_parts),
                })

        messages.append({
            "role": "user",
            "content": f"Memory task: {task_description}\n\nProvide your results in the specified JSON format.",
        })

        return messages

    def _parse_memory_output(
        self, response_text: str, task_description: str
    ) -> Dict[str, Any]:
        """Parse the LLM response into structured memory output."""
        try:
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            return {
                "operation": result.get("operation", "retrieve"),
                "memories": result.get("memories", []),
                "summary": result.get("summary", ""),
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "operation": "retrieve",
                "memories": [],
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
        """Non-streaming chat — executes a memory task."""
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
        """Streaming chat — yields memory result."""
        result = await self.chat(messages, provider_id, model)
        yield result["content"]

    def buildPrompt(
        self,
        messages: List[Dict[str, Any]],
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build prompt messages for memory operations."""
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        return self._build_memory_messages(user_message, execution_context)

    def validate(self) -> bool:
        """Validate Memory Agent configuration."""
        return bool(self._config.system_prompt)

    def getCapabilities(self) -> List[str]:
        """Get Memory Agent capabilities."""
        return self._config.capabilities