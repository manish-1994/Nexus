"""Research Agent — information gathering specialist.

Searches documentation, browses the web, reads files, and summarizes
findings into concise, cited reports. Used by the Orchestrator when
a task requires fact-finding, documentation lookup, or web research.
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

logger = logging.getLogger("research_agent")


class ResearchAgent(BaseAgent):
    """Agent that searches, browses, and summarizes information.

    The Research Agent is invoked for tasks requiring:
    - Documentation search and lookup
    - Web browsing and content extraction
    - Fact verification and citation
    - Information summarization

    It has access to search, browser, file, and memory tools.
    """

    def __init__(
        self,
        db: Session,
        agent_model: Agent,
        config: Optional[AgentConfig] = None,
        event_bus: Optional[EventBus] = None,
    ):
        super().__init__(db, agent_model)
        self._config = config or DEFAULT_AGENTS.get("research", AgentConfig(
            name="Research Agent",
            role=AgentRole.RESEARCH,
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
        """Execute a research task and return structured findings.

        Args:
            task_description: What to research
            context: Additional context (previous task outputs, etc.)
            provider_id: Provider override
            model: Model override
            execution_id: For event emission
            task_id: For event emission

        Returns:
            Dict with keys: findings, sources, confidence, gaps
        """
        start_time = time.time()

        # Emit task started
        if self._event_bus and execution_id and task_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_STARTED,
                execution_id=execution_id,
                task_id=task_id,
                agent_role=AgentRole.RESEARCH.value,
                data={"description": task_description},
            ))

        messages = self._build_research_messages(task_description, context)

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
            logger.exception("Research agent LLM call failed: %s", exc)
            latency_ms = int((time.time() - start_time) * 1000)
            if self._event_bus and execution_id and task_id:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.TASK_FAILED,
                    execution_id=execution_id,
                    task_id=task_id,
                    agent_role=AgentRole.RESEARCH.value,
                    data={"error": str(exc), "latency_ms": latency_ms},
                ))
            return {
                "findings": f"Research failed: {exc}",
                "sources": [],
                "confidence": "low",
                "gaps": ["Research execution failed"],
                "error": str(exc),
            }

        result = self._parse_research_output(response_text, task_description)
        latency_ms = int((time.time() - start_time) * 1000)

        # Emit task completed
        if self._event_bus and execution_id and task_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_COMPLETED,
                execution_id=execution_id,
                task_id=task_id,
                agent_role=AgentRole.RESEARCH.value,
                data={
                    "tokens_used": len(response_text) // 4,
                    "latency_ms": latency_ms,
                    "confidence": result.get("confidence"),
                },
            ))

        return result

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_research_messages(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build messages for the research LLM call."""
        system_prompt = self._config.system_prompt

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add context from previous tasks if available
        if context:
            context_text = json.dumps(context, indent=2)
            messages.append({
                "role": "system",
                "content": f"Additional context from previous tasks:\n{context_text}",
            })

        messages.append({
            "role": "user",
            "content": f"Research task: {task_description}\n\nProvide your findings in the specified JSON format.",
        })

        return messages

    def _parse_research_output(
        self, response_text: str, task_description: str
    ) -> Dict[str, Any]:
        """Parse the LLM response into structured research output."""
        try:
            # Try to extract JSON
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            return {
                "findings": result.get("findings", response_text),
                "sources": result.get("sources", []),
                "confidence": result.get("confidence", "medium"),
                "gaps": result.get("gaps", []),
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "findings": response_text,
                "sources": [],
                "confidence": "medium",
                "gaps": [],
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
        """Non-streaming chat — executes a research task."""
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
        """Streaming chat — yields research result."""
        result = await self.chat(messages, provider_id, model)
        yield result["content"]

    def buildPrompt(
        self,
        messages: List[Dict[str, Any]],
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build prompt messages for research."""
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        return self._build_research_messages(user_message, execution_context)

    def validate(self) -> bool:
        """Validate Research Agent configuration."""
        return bool(self._config.system_prompt)

    def getCapabilities(self) -> List[str]:
        """Get Research Agent capabilities."""
        return self._config.capabilities