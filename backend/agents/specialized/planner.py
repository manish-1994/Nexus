"""Planner Agent — the strategic brain of the Agent Operating System.

The Planner analyzes user requests and produces structured execution plans.
It NEVER answers the user directly — it only produces plans that the
Orchestrator uses to dispatch tasks to specialized agents.

Architecture:
    User Message → Planner.plan() → ExecutionPlan (JSON)
    ExecutionPlan → Orchestrator → TaskGraph → Specialized Agents
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from agents.orchestration.agent_config import AgentConfig, AgentRole, DEFAULT_AGENTS
from agents.orchestration.communication import (
    AgentMessage,
    ExecutionPlanPayload,
    MessageType,
)
from agents.orchestration.event_bus import (
    EventBus,
    EventType,
    ExecutionEvent,
    make_task_started_event,
    make_task_completed_event,
)
from models.agent import Agent
from services.ai_runtime import AIRuntime
from sqlalchemy.orm import Session

logger = logging.getLogger("planner_agent")


class PlannerAgent(BaseAgent):
    """Agent that decomposes user requests into structured execution plans.

    The Planner is the entry point for all non-trivial requests. It:
    1. Receives the user's message and conversation context
    2. Classifies the intent (code, research, analysis, memory, tool, conversation)
    3. Decomposes into discrete subtasks with dependencies
    4. Assigns each subtask to the most appropriate specialized agent
    5. Returns a structured JSON execution plan

    The Planner NEVER generates a final response for the user. Its sole
    output is an execution plan consumed by the Orchestrator.
    """

    def __init__(
        self,
        db: Session,
        agent_model: Agent,
        config: Optional[AgentConfig] = None,
        event_bus: Optional[EventBus] = None,
    ):
        super().__init__(db, agent_model)
        self._config = config or DEFAULT_AGENTS.get("planner", AgentConfig(
            name="Planner",
            role=AgentRole.PLANNER,
        ))
        self._event_bus = event_bus

    # ------------------------------------------------------------------
    # Core planning method
    # ------------------------------------------------------------------

    async def plan(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
        execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze a user message and produce an execution plan.

        This is the Planner's primary method. It sends the user message
        (with conversation context and available agent descriptions) to
        the LLM and parses the JSON execution plan from the response.

        Args:
            user_message: The user's latest message content
            conversation_history: Previous messages for context
            provider_id: Provider to use (overrides agent config)
            model: Model to use (overrides agent config)
            execution_id: Execution ID for event emission

        Returns:
            Execution plan dict with keys:
                intent, tasks, execution_strategy,
                estimated_complexity, reasoning

        Raises:
            ValueError: If the LLM response cannot be parsed as a valid plan
        """
        start_time = time.time()

        # Emit planning started event
        if self._event_bus and execution_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.PLANNING_STARTED,
                execution_id=execution_id,
                agent_role=AgentRole.PLANNER.value,
                data={"message_length": len(user_message)},
            ))

        # Build the planning prompt
        planning_messages = self._build_planning_prompt(
            user_message, conversation_history
        )

        # Resolve provider/model
        eff_provider_id = provider_id if provider_id is not None else self.agent_model.provider_id
        eff_model = model or self._config.preferred_model

        # Call the LLM
        runtime = AIRuntime(self.db)
        try:
            response_text = await runtime.chat(
                messages=planning_messages,
                provider_id=eff_provider_id,
                model=eff_model,
                temperature=self._config.temperature,
            )
        except Exception as exc:
            logger.exception("Planner LLM call failed: %s", exc)
            # Return a fallback single-task plan
            fallback_plan = self._fallback_plan(user_message)
            if self._event_bus and execution_id:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.PLANNING_COMPLETED,
                    execution_id=execution_id,
                    agent_role=AgentRole.PLANNER.value,
                    data={
                        "intent": "conversation",
                        "task_count": 1,
                        "fallback": True,
                        "error": str(exc),
                    },
                ))
            return fallback_plan

        # Parse the JSON plan from the response
        plan = self._parse_plan(response_text, user_message)

        latency_ms = int((time.time() - start_time) * 1000)

        # Emit planning completed event
        if self._event_bus and execution_id:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.PLANNING_COMPLETED,
                execution_id=execution_id,
                agent_role=AgentRole.PLANNER.value,
                data={
                    "intent": plan.get("intent"),
                    "task_count": len(plan.get("tasks", [])),
                    "strategy": plan.get("execution_strategy"),
                    "complexity": plan.get("estimated_complexity"),
                    "latency_ms": latency_ms,
                },
            ))

        return plan

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_planning_prompt(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Build the messages array for the planning LLM call.

        Constructs a system prompt describing all available agents and
        the required JSON output format, followed by conversation context
        and the user's latest message.
        """
        # Build agent capability descriptions
        agent_descriptions = self._build_agent_capabilities_text()

        system_prompt = self._config.system_prompt
        if not system_prompt:
            system_prompt = self._default_system_prompt()

        # Inject available agent descriptions into the system prompt
        system_prompt = system_prompt.replace(
            "Available agent roles and their capabilities:",
            f"Available agent roles and their capabilities:\n{agent_descriptions}",
        )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add conversation history for context (last 10 messages max)
        if conversation_history:
            recent = conversation_history[-10:]
            for msg in recent:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant"):
                    messages.append({"role": role, "content": content})

        # Add the current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _build_agent_capabilities_text(self) -> str:
        """Build a text description of all available agents and their capabilities."""
        lines = []
        for key, config in DEFAULT_AGENTS.items():
            if config.role == AgentRole.PLANNER:
                continue  # Don't describe self
            capabilities = ", ".join(config.capabilities)
            tools = ", ".join(config.tools) if config.tools else "none"
            lines.append(
                f"- {config.role.value.upper()}: {config.description}\n"
                f"  Capabilities: {capabilities}\n"
                f"  Tools: {tools}\n"
                f"  Parallelizable: {config.parallelizable}"
            )
        return "\n".join(lines)

    def _default_system_prompt(self) -> str:
        """Fallback system prompt if no config is provided."""
        return """You are the Nexus Planner. Your ONLY job is to analyze user requests
and produce structured execution plans in JSON format.

Output format:
{
    "intent": "code|research|analysis|memory|tool_execution|conversation",
    "tasks": [
        {
            "id": "task_1",
            "description": "<what this task does>",
            "agent_role": "<research|coder|analyst|memory|tool>",
            "depends_on": [],
            "priority": 1,
            "expected_output": "<what this task should produce>"
        }
    ],
    "execution_strategy": "sequential|parallel|mixed",
    "estimated_complexity": "low|medium|high",
    "reasoning": "<brief explanation>"
}

Respond ONLY with the JSON. No preamble, no markdown fences."""

    # ------------------------------------------------------------------
    # Plan parsing & validation
    # ------------------------------------------------------------------

    def _parse_plan(
        self, response_text: str, user_message: str
    ) -> Dict[str, Any]:
        """Parse the LLM response into a validated execution plan.

        Handles various response formats:
        - Pure JSON
        - JSON wrapped in markdown code fences
        - JSON with leading/trailing text

        Falls back to a single-task conversation plan if parsing fails.
        """
        # Try to extract JSON from the response
        json_str = self._extract_json(response_text)

        try:
            plan = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(
                "Planner response is not valid JSON. Raw: %s...",
                response_text[:200],
            )
            return self._fallback_plan(user_message)

        # Validate required fields
        if not isinstance(plan, dict):
            return self._fallback_plan(user_message)

        if "tasks" not in plan or not isinstance(plan["tasks"], list):
            return self._fallback_plan(user_message)

        if len(plan["tasks"]) == 0:
            return self._fallback_plan(user_message)

        # Normalize and validate each task
        validated_tasks = []
        for i, task in enumerate(plan["tasks"]):
            if not isinstance(task, dict):
                continue
            validated_task = {
                "id": task.get("id", f"task_{i + 1}"),
                "description": task.get("description", f"Task {i + 1}"),
                "agent_role": self._validate_agent_role(task.get("agent_role", "")),
                "depends_on": task.get("depends_on", []),
                "priority": task.get("priority", 1),
                "expected_output": task.get("expected_output", ""),
            }
            validated_tasks.append(validated_task)

        if not validated_tasks:
            return self._fallback_plan(user_message)

        return {
            "intent": plan.get("intent", "conversation"),
            "tasks": validated_tasks,
            "execution_strategy": plan.get("execution_strategy", "sequential"),
            "estimated_complexity": plan.get("estimated_complexity", "low"),
            "reasoning": plan.get("reasoning", ""),
        }

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may contain markdown fences or extra content."""
        text = text.strip()

        # Try to find JSON between markdown code fences
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

        # Try to find JSON object boundaries
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace >= 0 and last_brace > first_brace:
            return text[first_brace:last_brace + 1]

        return text

    def _validate_agent_role(self, role: str) -> str:
        """Validate and normalize an agent role string."""
        role_lower = role.lower().strip()
        valid_roles = {r.value for r in AgentRole}
        if role_lower in valid_roles:
            return role_lower
        # Try common aliases
        aliases = {
            "research_agent": "research",
            "coder_agent": "coder",
            "analyst_agent": "analyst",
            "memory_agent": "memory",
            "tool_agent": "tool",
            "researcher": "research",
            "developer": "coder",
            "programmer": "coder",
            "data_analyst": "analyst",
        }
        return aliases.get(role_lower, "research")  # Default to research

    def _fallback_plan(self, user_message: str) -> Dict[str, Any]:
        """Generate a minimal fallback plan when planning fails.

        Returns a single-task plan that routes to the most appropriate
        agent based on simple keyword matching.
        """
        # Simple intent classification
        intent = self._classify_intent_fallback(user_message)
        agent_role = self._intent_to_role(intent)

        return {
            "intent": intent,
            "tasks": [
                {
                    "id": "task_1",
                    "description": f"Handle user request: {user_message[:100]}",
                    "agent_role": agent_role,
                    "depends_on": [],
                    "priority": 1,
                    "expected_output": "A helpful response to the user's request",
                }
            ],
            "execution_strategy": "sequential",
            "estimated_complexity": "low",
            "reasoning": "Fallback plan due to planning failure. Single-task execution.",
        }

    def _classify_intent_fallback(self, message: str) -> str:
        """Simple keyword-based intent classification for fallback."""
        msg_lower = message.lower()

        code_keywords = [
            "code", "function", "class", "bug", "error", "fix", "implement",
            "write", "program", "script", "python", "javascript", "typescript",
            "react", "component", "api", "endpoint", "route", "database",
            "sql", "query", "refactor", "debug", "compile", "build",
        ]
        research_keywords = [
            "search", "find", "lookup", "documentation", "docs", "what is",
            "how does", "explain", "definition", "meaning", "wiki",
            "research", "learn about", "tell me about", "information",
        ]
        analysis_keywords = [
            "analyze", "calculate", "compute", "statistics", "data",
            "report", "compare", "chart", "graph", "metrics", "numbers",
            "summary", "summarize", "breakdown",
        ]
        tool_keywords = [
            "run", "execute", "terminal", "command", "shell", "bash",
            "browse", "open url", "navigate", "file", "directory",
            "list files", "read file", "write file", "create file",
        ]
        memory_keywords = [
            "remember", "recall", "memory", "previous", "past",
            "history", "what did i", "you said", "we discussed",
        ]

        scores = {
            "code": sum(1 for kw in code_keywords if kw in msg_lower),
            "research": sum(1 for kw in research_keywords if kw in msg_lower),
            "analysis": sum(1 for kw in analysis_keywords if kw in msg_lower),
            "tool_execution": sum(1 for kw in tool_keywords if kw in msg_lower),
            "memory": sum(1 for kw in memory_keywords if kw in msg_lower),
        }

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return "conversation"
        return best

    def _intent_to_role(self, intent: str) -> str:
        """Map an intent string to the primary agent role."""
        mapping = {
            "code": "coder",
            "research": "research",
            "analysis": "analyst",
            "tool_execution": "tool",
            "memory": "memory",
            "conversation": "research",  # Default to research for general Q&A
        }
        return mapping.get(intent, "research")

    # ------------------------------------------------------------------
    # BaseAgent interface implementation
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Non-streaming chat — delegates to plan() for the last user message."""
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        history = messages[:-1] if len(messages) > 1 else None
        plan = await self.plan(user_message, history, provider_id, model)
        return {"content": json.dumps(plan, indent=2), "plan": plan}

    async def stream(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
    ):
        """Streaming — not typically used for Planner; yields the plan as one chunk."""
        result = await self.chat(messages, provider_id, model)
        yield result["content"]
        # Also yield an empty string to signal completion
        if False:
            yield ""

    def buildPrompt(
        self,
        messages: List[Dict[str, Any]],
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build prompt messages for the Planner."""
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        history = messages[:-1] if len(messages) > 1 else None
        return self._build_planning_prompt(user_message, history)

    def validate(self) -> bool:
        """Validate Planner configuration."""
        return bool(self._config.system_prompt or self._default_system_prompt())

    def getCapabilities(self) -> List[str]:
        """Get Planner capabilities."""
        return self._config.capabilities