"""Agent Operating System — Orchestration Layer.

Transforms Nexus from a single-agent chatbot into a multi-agent
operating system with intelligent task routing, parallel execution,
and synthesized responses.

Architecture:
    User → Orchestrator → Planner → Specialized Agents → Tools → Memory → Response Synthesizer → User
"""

from .agent_config import AgentConfig, DEFAULT_AGENTS, AgentRole
from .event_bus import EventBus, ExecutionEvent, EventType
from .task_graph import TaskGraph, TaskNode, TaskEdge, TaskStatus
from .execution_store import LiveExecutionStore, ExecutionState
from .orchestrator import Orchestrator
from .communication import AgentMessage, MessageType
from .agent_registry import PluggableAgentRegistry, registry, get_registry

__all__ = [
    "AgentConfig",
    "AgentRole",
    "DEFAULT_AGENTS",
    "EventBus",
    "ExecutionEvent",
    "EventType",
    "TaskGraph",
    "TaskNode",
    "TaskEdge",
    "TaskStatus",
    "LiveExecutionStore",
    "ExecutionState",
    "Orchestrator",
    "AgentMessage",
    "MessageType",
    "PluggableAgentRegistry",
    "registry",
    "get_registry",
]