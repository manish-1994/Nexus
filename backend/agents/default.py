import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from agents.base import BaseAgent
from models.agent import Agent
from services.ai_runtime import AIRuntime
from sqlalchemy.orm import Session

logger = logging.getLogger("default_agent")


class DefaultAgent(BaseAgent):
    """Default implementation of an agent."""

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a non-streaming chat request."""
        # Use provider/model from agent config if not provided explicitly
        eff_provider_id = provider_id if provider_id else self.agent_model.provider_id
        eff_model = model if model else None

        prompt_messages = self.buildPrompt(messages)
        runtime = AIRuntime(self.db)
        response_text = await runtime.chat(
            messages=prompt_messages,
            provider_id=eff_provider_id,
            model=eff_model,
        )
        return {
            "content": response_text,
            "provider_id": eff_provider_id,
            "model": eff_model,
        }

    async def stream(
        self,
        messages: List[Dict[str, Any]],
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Execute a streaming chat request."""
        eff_provider_id = provider_id if provider_id else self.agent_model.provider_id
        eff_model = model if model else None
        logger.info(
            "[DEBUG] DefaultAgent.stream called agent_id=%s provider_id=%s model=%s messages_count=%d",
            self.agent_model.id,
            eff_provider_id,
            eff_model,
            len(messages),
        )

        prompt_messages = self.buildPrompt(messages)
        logger.info(
            "[DEBUG] DefaultAgent.stream prompt_messages count=%d", len(prompt_messages)
        )
        runtime = AIRuntime(self.db)
        logger.info("[DEBUG] DefaultAgent.stream AIRuntime instantiated")

        async for chunk in runtime.stream(
            messages=prompt_messages,
            provider_id=eff_provider_id,
            model=eff_model,
        ):
            yield chunk

    def buildPrompt(
        self,
        messages: List[Dict[str, Any]],
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Construct the prompt messages, injecting system prompts.

        Args:
            messages: The conversation messages to wrap with a system prompt
            execution_context: Optional context for dynamic prompt variables
                (conversation history, memory, workspace, tools, etc.)
        """
        from agents.prompt_builder import PromptBuilder

        prompt_messages = list(messages)
        builder = PromptBuilder(self.agent_model, execution_context=execution_context)
        system_content = builder.build()

        if system_content:
            # Check if there is already a system message
            has_system = any(msg.get("role") == "system" for msg in prompt_messages)
            if not has_system:
                prompt_messages.insert(0, {"role": "system", "content": system_content})
        return prompt_messages

    def validate(self) -> bool:
        """Validate agent configuration."""
        return self.agent_model.enabled

    def getCapabilities(self) -> List[str]:
        """Get agent capabilities."""
        import json

        try:
            return json.loads(self.agent_model.capabilities or "[]")
        except:
            return []
