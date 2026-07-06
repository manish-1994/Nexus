"""Pluggable Agent Registry for the Agent Operating System.

Provides a global registry where custom agents can be registered
without modifying any core system code. The pattern is:

    from agents.orchestration.agent_registry import registry
    from agents.base import BaseAgent

    class MyCustomAgent(BaseAgent):
        ...

    registry.register(MyCustomAgent)

Once registered, the Orchestrator can discover and use the custom
agent just like any built-in agent. The Planner can include it in
execution plans, and the Orchestrator can dispatch tasks to it.

Architecture:
    registry.register(MyCustomAgent)
        → stores AgentRegistration (class + config)
        → Orchestrator discovers via registry.get_factory()
        → Planner sees capability in agent list
        → Tasks can be routed to the custom agent
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Type

from agents.base import BaseAgent
from agents.orchestration.agent_config import AgentConfig, AgentRole
from agents.orchestration.event_bus import EventBus, EventType, ExecutionEvent
from sqlalchemy.orm import Session

logger = logging.getLogger("agent_registry")


class AgentRegistration:
    """A registered custom agent entry.

    Holds the agent class (or factory function), its configuration,
    and metadata needed by the Orchestrator to instantiate and use it.
    """

    def __init__(
        self,
        role: str,
        agent_cls: Type[BaseAgent],
        config: AgentConfig,
        factory: Optional[Callable[..., BaseAgent]] = None,
    ):
        self.role = role
        self.agent_cls = agent_cls
        self.config = config
        self.factory = factory
        self.registered_at = None  # Set by registry

    def create_instance(
        self,
        db: Session,
        agent_model: Any,
        event_bus: Optional[EventBus] = None,
    ) -> BaseAgent:
        """Create an instance of the registered agent.

        Prefers the factory function if provided, otherwise
        attempts to instantiate the class directly.
        """
        if self.factory:
            return self.factory(db, agent_model, self.config, event_bus)

        # Try direct instantiation with standard constructor signature
        try:
            return self.agent_cls(db, agent_model, self.config, event_bus)
        except TypeError:
            # Try simpler constructor (db, agent_model)
            try:
                return self.agent_cls(db, agent_model)
            except TypeError:
                # Try simplest constructor (db only)
                return self.agent_cls(db)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize registration info for Planner discovery."""
        return {
            "role": self.role,
            "name": self.config.name,
            "description": self.config.description,
            "capabilities": self.config.capabilities,
            "tools": self.config.tools,
            "preferred_provider": self.config.preferred_provider,
            "preferred_model": self.config.preferred_model,
            "temperature": self.config.temperature,
            "parallelizable": self.config.parallelizable,
            "requires_plan": self.config.requires_plan,
            "memory_access": self.config.memory_access,
            "permissions": self.config.permissions,
        }


class PluggableAgentRegistry:
    """Global registry for custom agents in the Agent Operating System.

    Singleton pattern — one registry per process. Agents registered
    here are automatically discoverable by the Planner and usable
    by the Orchestrator without any code changes to the core system.

    Usage:
        registry = PluggableAgentRegistry()

        # Register a custom agent class
        registry.register(MyCustomAgent)

        # Register with explicit config
        registry.register(
            MyCustomAgent,
            config=AgentConfig(
                name="My Custom Agent",
                role="my_custom",
                description="Does custom things",
                capabilities=["custom_processing", "data_transformation"],
                system_prompt="You are a custom agent...",
            ),
        )

        # Register with a factory function
        registry.register(
            MyCustomAgent,
            factory=lambda db, model, config, eb: MyCustomAgent(db, model, config, eb),
        )
    """

    _instance: Optional["PluggableAgentRegistry"] = None

    def __new__(cls) -> "PluggableAgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registrations: Dict[str, AgentRegistration] = {}
            cls._instance._event_bus: Optional[EventBus] = None
        return cls._instance

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Attach an event bus for emitting registration events."""
        self._event_bus = event_bus

    def register(
        self,
        agent_cls: Type[BaseAgent],
        config: Optional[AgentConfig] = None,
        factory: Optional[Callable[..., BaseAgent]] = None,
        role: Optional[str] = None,
    ) -> AgentRegistration:
        """Register a custom agent class with the Agent OS.

        Args:
            agent_cls: The agent class (must extend BaseAgent)
            config: AgentConfig with name, role, capabilities, etc.
                    If not provided, a minimal config is derived from the class.
            factory: Optional factory function for custom instantiation logic.
                     Signature: (db, agent_model, config, event_bus) -> BaseAgent
            role: Override the role string. Defaults to config.role or
                  a snake_case version of the class name.

        Returns:
            AgentRegistration: The registration record

        Raises:
            ValueError: If the role conflicts with a built-in AgentRole
            TypeError: If agent_cls does not extend BaseAgent
        """
        # Validate agent_cls extends BaseAgent
        if not issubclass(agent_cls, BaseAgent):
            raise TypeError(
                f"{agent_cls.__name__} must extend BaseAgent to be registered"
            )

        # Build or validate config
        if config is None:
            # Derive minimal config from class
            class_name = agent_cls.__name__
            derived_role = role or _class_name_to_role(class_name)
            config = AgentConfig(
                name=class_name,
                role=derived_role,
                description=f"Custom agent: {class_name}",
                capabilities=getattr(agent_cls, 'CAPABILITIES', []),
                system_prompt=getattr(agent_cls, 'SYSTEM_PROMPT', f"You are {class_name}."),
                tools=getattr(agent_cls, 'TOOLS', []),
                temperature=getattr(agent_cls, 'TEMPERATURE', 0.5),
            )

        resolved_role = role or config.role

        # Prevent overriding built-in roles
        builtin_roles = {r.value for r in AgentRole if r != AgentRole.CUSTOM}
        if resolved_role in builtin_roles:
            raise ValueError(
                f"Role '{resolved_role}' is a built-in AgentRole. "
                f"Use a custom role name for your agent."
            )

        # Create registration
        import datetime
        registration = AgentRegistration(
            role=resolved_role,
            agent_cls=agent_cls,
            config=config,
            factory=factory,
        )
        registration.registered_at = datetime.datetime.utcnow()

        self._registrations[resolved_role] = registration

        logger.info(
            "Registered custom agent: role=%s class=%s capabilities=%s",
            resolved_role,
            agent_cls.__name__,
            config.capabilities,
        )

        # Emit event
        if self._event_bus:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.AGENT_REGISTERED,
                agent_role=resolved_role,
                data={
                    "role": resolved_role,
                    "class": agent_cls.__name__,
                    "capabilities": config.capabilities,
                    "config": config.to_dict(),
                },
            ))

        return registration

    def unregister(self, role: str) -> bool:
        """Unregister a custom agent by role.

        Args:
            role: The role string to unregister

        Returns:
            True if the agent was found and removed
        """
        if role in self._registrations:
            registration = self._registrations.pop(role)
            logger.info("Unregistered custom agent: role=%s", role)

            if self._event_bus:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.AGENT_UNREGISTERED,
                    agent_role=role,
                    data={"role": role, "class": registration.agent_cls.__name__},
                ))

            return True
        return False

    def get(self, role: str) -> Optional[AgentRegistration]:
        """Get a registered agent by role."""
        return self._registrations.get(role)

    def get_factory(self, role: str) -> Optional[Callable[..., BaseAgent]]:
        """Get a factory function that creates the agent instance.

        Returns a callable with signature:
            (db, agent_model, config, event_bus) -> BaseAgent

        This is the format the Orchestrator's _agent_factories expects.
        """
        registration = self._registrations.get(role)
        if not registration:
            return None

        # Return a lambda that wraps create_instance
        reg = registration  # Capture for closure
        return lambda db, agent_model, config, event_bus: reg.create_instance(
            db, agent_model, event_bus
        )

    def get_config(self, role: str) -> Optional[AgentConfig]:
        """Get the AgentConfig for a registered agent."""
        registration = self._registrations.get(role)
        return registration.config if registration else None

    def get_all(self) -> List[AgentRegistration]:
        """Get all registered custom agents."""
        return list(self._registrations.values())

    def get_all_configs(self) -> Dict[str, AgentConfig]:
        """Get all registered agent configs keyed by role."""
        return {
            role: reg.config
            for role, reg in self._registrations.items()
        }

    def get_all_capability_descriptions(self) -> List[Dict[str, Any]]:
        """Get capability descriptions for all registered agents.

        Used by the Planner to know what agents are available.
        """
        return [reg.to_dict() for reg in self._registrations.values()]

    def is_registered(self, role: str) -> bool:
        """Check if a role is registered."""
        return role in self._registrations

    @property
    def count(self) -> int:
        """Number of registered custom agents."""
        return len(self._registrations)

    @property
    def roles(self) -> List[str]:
        """List of registered role strings."""
        return list(self._registrations.keys())

    def clear(self) -> None:
        """Remove all custom registrations (useful for testing)."""
        self._registrations.clear()


def _class_name_to_role(class_name: str) -> str:
    """Convert a PascalCase class name to snake_case role string.

    Examples:
        MyCustomAgent → my_custom_agent
        DataProcessor → data_processor
        SQLAgent → sql_agent
    """
    import re
    # Insert underscore before capital letters, then lowercase
    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
    # Remove trailing "agent" if present
    if snake.endswith('_agent'):
        snake = snake[:-6]
    return snake


# ------------------------------------------------------------------
# Global singleton instance
# ------------------------------------------------------------------

registry = PluggableAgentRegistry()
"""Global pluggable agent registry singleton.

Import and use directly:

    from agents.orchestration.agent_registry import registry

    registry.register(MyCustomAgent)
    registry.unregister("my_custom")
    configs = registry.get_all_configs()
"""


def get_registry() -> PluggableAgentRegistry:
    """Get the global PluggableAgentRegistry singleton."""
    return registry