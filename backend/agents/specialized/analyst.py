"""Analyst Agent — data processing and insights specialist.

Processes data, creates reports, analyzes files, performs calculations,
and generates insights from structured and unstructured information.
Used by the Orchestrator when a task involves data analysis, statistics,
or report generation.
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

logger = logging.getLogger("analyst_agent")


class AnalystAgent(BaseAgent):
    """Agent that analyzes data and generates insights.

    The Analyst Agent is invoked for tasks requiring:
    - Data processing and analysis
    - Statistical calculations
    - Report generation
    - File analysis and parsing
    - Trend identification and forecasting

    It has access to Python execution, file operations, search,
    and terminal tools.
    """

    def __init__(
        self,
        db: Session,
        agent_model: Agent,
        config: Optional[AgentConfig] = None,
        event_bus: Optional[EventBus] = None,
    ):
        super().__init__(db, agent_model)
        self._config = config or DEFAULT_AGENTS.get("analyst", AgentConfig(
            name="Analyst",
            role=AgentRole.ANALYST,
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
        """Execute an analysis task and return structured results.

        Args:
            task_description: What to analyze
            context: Additional context (data, previous task outputs)
            provider_id: Provider override
            model: Model override
            execution_id: For event emission
            task_id: For event emission

        Returns:
            Dict with keys: summary, details, data_sources,
                           calculations, confidence, recommendations
        """
        start_time = time.time()

        # Emit task started
        if self._event_bus and execution_id and task_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_STARTED,
                execution_id=execution_id,
                task_id=task_id,
                agent_role=AgentRole.ANALYST.value,
                data={"description": task_description},
            ))

        messages = self._build_analyst_messages(task_description, context)

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
            logger.exception("Analyst agent LLM call failed: %s", exc)
            latency_ms = int((time.time() - start_time) * 1000)
            if self._event_bus and execution_id and task_id:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.TASK_FAILED,
                    execution_id=execution_id,
                    task_id=task_id,
                    agent_role=AgentRole.ANALYST.value,
                    data={"error": str(exc), "latency_ms": latency_ms},
                ))
            return {
                "summary": f"Analysis failed: {exc}",
                "details": "",
                "data_sources": [],
                "calculations": [],
                "confidence": "low",
                "recommendations": [],
                "error": str(exc),
            }

        result = self._parse_analyst_output(response_text, task_description)
        latency_ms = int((time.time() - start_time) * 1000)

        # Emit task completed
        if self._event_bus and execution_id and task_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_COMPLETED,
                execution_id=execution_id,
                task_id=task_id,
                agent_role=AgentRole.ANALYST.value,
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

    def _build_analyst_messages(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build messages for the analyst LLM call."""
        system_prompt = self._config.system_prompt

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add context from previous tasks
        if context:
            data_content = context.get("data", "")
            research_findings = context.get("research_findings", "")
            file_contents = context.get("file_contents", "")

            context_parts = []
            if data_content:
                context_parts.append(f"## Data to Analyze\n{data_content}")
            if research_findings:
                context_parts.append(f"## Research Context\n{research_findings}")
            if file_contents:
                context_parts.append(f"## File Contents\n{file_contents}")

            if context_parts:
                messages.append({
                    "role": "system",
                    "content": "Context for analysis:\n\n" + "\n\n".join(context_parts),
                })

        messages.append({
            "role": "user",
            "content": f"Analysis task: {task_description}\n\nProvide your analysis in the specified JSON format.",
        })

        return messages

    def _parse_analyst_output(
        self, response_text: str, task_description: str
    ) -> Dict[str, Any]:
        """Parse the LLM response into structured analyst output."""
        try:
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            return {
                "summary": result.get("summary", ""),
                "details": result.get("details", ""),
                "data_sources": result.get("data_sources", []),
                "calculations": result.get("calculations", []),
                "confidence": result.get("confidence", "medium"),
                "recommendations": result.get("recommendations", []),
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "summary": response_text,
                "details": "",
                "data_sources": [],
                "calculations": [],
                "confidence": "medium",
                "recommendations": [],
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
        """Non-streaming chat — executes an analysis task."""
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
        """Streaming chat — yields analyst result."""
        result = await self.chat(messages, provider_id, model)
        yield result["content"]

    def buildPrompt(
        self,
        messages: List[Dict[str, Any]],
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build prompt messages for analysis."""
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        return self._build_analyst_messages(user_message, execution_context)

    def validate(self) -> bool:
        """Validate Analyst Agent configuration."""
        return bool(self._config.system_prompt)

    def getCapabilities(self) -> List[str]:
        """Get Analyst Agent capabilities."""
        return self._config.capabilities