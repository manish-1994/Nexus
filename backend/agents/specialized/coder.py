"""Coder Agent — software engineering specialist.

Writes, explains, debugs, and refactors code. Creates projects,
implements features, and provides technical guidance. Used by the
Orchestrator when a task involves code generation, explanation,
debugging, or project creation.
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

logger = logging.getLogger("coder_agent")


class CoderAgent(BaseAgent):
    """Agent that writes, explains, and improves code.

    The Coder Agent is invoked for tasks requiring:
    - Code generation and implementation
    - Code explanation and documentation
    - Debugging and error fixing
    - Code review and refactoring
    - Project scaffolding and file creation

    It has access to file operations, Python execution, terminal,
    and search tools.
    """

    def __init__(
        self,
        db: Session,
        agent_model: Agent,
        config: Optional[AgentConfig] = None,
        event_bus: Optional[EventBus] = None,
    ):
        super().__init__(db, agent_model)
        self._config = config or DEFAULT_AGENTS.get("coder", AgentConfig(
            name="Coder",
            role=AgentRole.CODER,
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
        """Execute a coding task and return the result.

        Args:
            task_description: What code to write/explain/fix
            context: Additional context (research findings, previous outputs)
            provider_id: Provider override
            model: Model override
            execution_id: For event emission
            task_id: For event emission

        Returns:
            Dict with keys: code, explanation, language, files_modified
        """
        start_time = time.time()

        # Emit task started
        if self._event_bus and execution_id and task_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_STARTED,
                execution_id=execution_id,
                task_id=task_id,
                agent_role=AgentRole.CODER.value,
                data={"description": task_description},
            ))

        messages = self._build_coder_messages(task_description, context)

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
            logger.exception("Coder agent LLM call failed: %s", exc)
            latency_ms = int((time.time() - start_time) * 1000)
            if self._event_bus and execution_id and task_id:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.TASK_FAILED,
                    execution_id=execution_id,
                    task_id=task_id,
                    agent_role=AgentRole.CODER.value,
                    data={"error": str(exc), "latency_ms": latency_ms},
                ))
            return {
                "code": "",
                "explanation": f"Coding task failed: {exc}",
                "language": "text",
                "files_modified": [],
                "error": str(exc),
            }

        result = self._parse_coder_output(response_text, task_description)
        latency_ms = int((time.time() - start_time) * 1000)

        # Emit task completed
        if self._event_bus and execution_id and task_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_COMPLETED,
                execution_id=execution_id,
                task_id=task_id,
                agent_role=AgentRole.CODER.value,
                data={
                    "tokens_used": len(response_text) // 4,
                    "latency_ms": latency_ms,
                    "language": result.get("language"),
                },
            ))

        return result

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_coder_messages(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build messages for the coder LLM call."""
        system_prompt = self._config.system_prompt

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add context from previous tasks (e.g., research findings)
        if context:
            # Extract relevant context
            research_findings = context.get("research_findings", "")
            previous_code = context.get("previous_code", "")
            workspace_info = context.get("workspace_info", "")

            context_parts = []
            if research_findings:
                context_parts.append(f"## Research Findings\n{research_findings}")
            if previous_code:
                context_parts.append(f"## Existing Code\n{previous_code}")
            if workspace_info:
                context_parts.append(f"## Workspace Context\n{workspace_info}")

            if context_parts:
                messages.append({
                    "role": "system",
                    "content": "Context from previous tasks:\n\n" + "\n\n".join(context_parts),
                })

        messages.append({
            "role": "user",
            "content": f"Coding task: {task_description}",
        })

        return messages

    def _parse_coder_output(
        self, response_text: str, task_description: str
    ) -> Dict[str, Any]:
        """Parse the LLM response into structured coder output.

        Extracts code blocks, identifies languages, and separates
        explanation from code.
        """
        # Extract code blocks from markdown
        code_blocks = []
        explanation_parts = []
        current_pos = 0

        while True:
            fence_start = response_text.find("```", current_pos)
            if fence_start == -1:
                # No more code blocks — rest is explanation
                explanation_parts.append(response_text[current_pos:])
                break

            # Text before the fence is explanation
            explanation_parts.append(response_text[current_pos:fence_start])

            # Find the language specifier
            lang_end = response_text.find("\n", fence_start)
            if lang_end == -1:
                break
            language = response_text[fence_start + 3:lang_end].strip()

            # Find the closing fence
            fence_end = response_text.find("```", lang_end + 1)
            if fence_end == -1:
                break

            code = response_text[lang_end + 1:fence_end]
            code_blocks.append({
                "language": language or "text",
                "code": code.strip(),
            })

            current_pos = fence_end + 3

        # If no code blocks found, treat entire response as explanation
        if not code_blocks:
            return {
                "code": response_text,
                "explanation": "",
                "language": "text",
                "files_modified": [],
            }

        # Combine code blocks
        primary_code = code_blocks[0]["code"] if code_blocks else ""
        primary_language = code_blocks[0]["language"] if code_blocks else "text"
        explanation = "\n".join(explanation_parts).strip()

        return {
            "code": primary_code,
            "explanation": explanation,
            "language": primary_language,
            "all_code_blocks": code_blocks,
            "files_modified": [],
        }

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Non-streaming chat — executes a coding task."""
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
        """Streaming chat — yields coder result."""
        result = await self.chat(messages, provider_id, model)
        yield result["content"]

    def buildPrompt(
        self,
        messages: List[Dict[str, Any]],
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build prompt messages for coding."""
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        return self._build_coder_messages(user_message, execution_context)

    def validate(self) -> bool:
        """Validate Coder Agent configuration."""
        return bool(self._config.system_prompt)

    def getCapabilities(self) -> List[str]:
        """Get Coder Agent capabilities."""
        return self._config.capabilities