import datetime
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("prompt_builder")


class PromptBuilder:
    """Service to compose the final system prompt for an agent.

    Supports both static variables (always available) and dynamic
    resolvers that are lazily evaluated only when the placeholder
    appears in the template. Dynamic resolvers pull from an optional
    execution_context dict that can carry conversation history,
    memory service results, workspace context, tool listings, etc.
    """

    def __init__(self, agent, execution_context: Optional[Dict[str, Any]] = None):
        self.agent = agent
        self.context = execution_context or {}

        # Static variables — always resolved
        self.variables: Dict[str, str] = {
            "agent": agent.name if agent else "Assistant",
            "agent_description": agent.description or "" if agent else "",
            "user": "User",
            "today": datetime.date.today().isoformat(),
            "now": datetime.datetime.now().isoformat(),
        }

        # Dynamic resolvers — lazily evaluated only if placeholder exists
        self.dynamic_resolvers: Dict[str, Callable[[], str]] = {
            "conversation": self._resolve_conversation,
            "workspace": self._resolve_workspace,
            "memory": self._resolve_memory,
            "files": self._resolve_files,
            "tools": self._resolve_tools,
            "capabilities": self._resolve_capabilities,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_variable(self, key: str, value: str):
        """Override or add a static variable."""
        self.variables[key] = value

    def set_context(self, key: str, value: Any):
        """Add a value to the execution context for dynamic resolvers."""
        self.context[key] = value

    def build(self) -> str:
        """Renders the prompt template with current variables.

        Static variables are always resolved. Dynamic resolvers are
        only invoked when their placeholder (e.g. {{memory}}) actually
        appears in the template — this avoids unnecessary work.
        """
        if not self.agent or not self.agent.prompt_template:
            template = (
                "You are a helpful and friendly AI assistant.\n\n"
                "Context:\nToday is {{today}}."
            )
        else:
            template = self.agent.prompt_template

        # Resolve static variables
        for key, value in self.variables.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in template:
                template = template.replace(placeholder, str(value))

        # Resolve dynamic variables (lazy — only if placeholder present)
        for key, resolver in self.dynamic_resolvers.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in template:
                try:
                    resolved = resolver()
                    template = template.replace(placeholder, str(resolved))
                except Exception as exc:
                    logger.warning(
                        "Failed to resolve dynamic variable '%s': %s", key, exc
                    )
                    template = template.replace(placeholder, "")

        return template

    # ------------------------------------------------------------------
    # Dynamic resolvers
    # ------------------------------------------------------------------

    def _resolve_conversation(self) -> str:
        """Summarize recent conversation context from execution_context."""
        messages: List[Dict] = self.context.get("conversation_messages", [])
        if not messages:
            return "No conversation history."

        # Return the last N messages as a compact summary
        max_msgs = self.context.get("conversation_max_messages", 10)
        recent = messages[-max_msgs:]

        lines = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            # Truncate long messages for the prompt context
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"[{role}]: {content}")

        return "\n".join(lines)

    def _resolve_workspace(self) -> str:
        """Describe current workspace context."""
        workspace = self.context.get("workspace_context")
        if workspace and hasattr(workspace, "get_summary"):
            try:
                return workspace.get_summary()
            except Exception:
                pass
        return "No workspace context available."

    def _resolve_memory(self) -> str:
        """Query memory service for relevant memories."""
        memory_service = self.context.get("memory_service")
        if memory_service and hasattr(memory_service, "query"):
            try:
                user_query = self.context.get("user_query", "")
                agent_id = self.agent.id if self.agent else None
                result = memory_service.query(agent_id, user_query)
                return str(result) if result else "No relevant memories found."
            except Exception:
                pass
        return "Memory service not available."

    def _resolve_files(self) -> str:
        """List relevant files in workspace."""
        workspace = self.context.get("workspace_context")
        if workspace and hasattr(workspace, "list_files"):
            try:
                files = workspace.list_files()
                if files:
                    return "\n".join(f"- {f}" for f in files)
            except Exception:
                pass
        return "No files available."

    def _resolve_tools(self) -> str:
        """List enabled tools and their descriptions."""
        tools: List[Dict] = self.context.get("enabled_tools", [])
        if not tools:
            # Fall back to agent's default_tools if available
            if self.agent and hasattr(self.agent, "default_tools"):
                raw = self.agent.default_tools
                if raw:
                    try:
                        import json

                        tools = json.loads(raw) if isinstance(raw, str) else raw
                    except (json.JSONDecodeError, TypeError):
                        pass

        if tools:
            lines = []
            for t in tools:
                name = t.get("name", "unknown")
                desc = t.get("description", "No description")
                lines.append(f"- {name}: {desc}")
            return "\n".join(lines)

        return "No tools enabled."

    def _resolve_capabilities(self) -> str:
        """List agent capabilities."""
        if self.agent and hasattr(self.agent, "capabilities"):
            caps = self.agent.capabilities
            if caps:
                try:
                    import json

                    cap_list = json.loads(caps) if isinstance(caps, str) else caps
                    if isinstance(cap_list, list):
                        return ", ".join(cap_list)
                except (json.JSONDecodeError, TypeError):
                    pass
        return "General conversation"
