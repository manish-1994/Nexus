"""Unit tests for the Agent Operating System components.

Tests cover:
- Event Bus (pub/sub, history, wildcard subscriptions)
- Task Graph (DAG, cycle detection, topological sort, parallel groups)
- Live Execution Store (state tracking, task lifecycle, metrics)
- Pluggable Agent Registry (register/unregister, factory, config discovery)
- Planner Agent (fallback plan generation, intent classification)
- Orchestrator (execution pipeline, sequential/parallel strategies, failover)
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _run_async(coro):
    """Run an async coroutine in a test-friendly way."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# Event Bus
from agents.orchestration.event_bus import (
    EventBus,
    EventType,
    ExecutionEvent,
    make_execution_started_event,
    make_task_completed_event,
)

# Task Graph
from agents.orchestration.task_graph import (
    TaskGraph,
    TaskNode,
    TaskStatus,
)

# Execution Store
from agents.orchestration.execution_store import (
    LiveExecutionStore,
    ExecutionState,
    get_execution_store,
    set_execution_store,
)

# Agent Config
from agents.orchestration.agent_config import (
    AgentConfig,
    AgentRole,
    DEFAULT_AGENTS,
)

# Pluggable Agent Registry
from agents.orchestration.agent_registry import (
    PluggableAgentRegistry,
    registry,
    _class_name_to_role,
)

# Base Agent
from agents.base import BaseAgent


# ==================================================================
# EVENT BUS TESTS
# ==================================================================

class TestEventBus:
    """Tests for the EventBus pub/sub system."""

    def test_subscribe_and_emit(self):
        """Handler should receive events for subscribed type."""
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(EventType.TASK_STARTED, handler)

        event = ExecutionEvent(
            type=EventType.TASK_STARTED,
            execution_id="exec-1",
            task_id="task-1",
            agent_role="research",
        )
        _run_async(bus.emit(event))

        assert len(received) == 1
        assert received[0].type == EventType.TASK_STARTED

    def test_subscribe_all_wildcard(self):
        """Wildcard handler should receive all event types."""
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe_all(handler)

        _run_async(bus.emit(
            ExecutionEvent(type=EventType.TASK_STARTED, execution_id="e1")
        ))
        _run_async(bus.emit(
            ExecutionEvent(type=EventType.TASK_COMPLETED, execution_id="e1")
        ))

        assert len(received) == 2

    def test_unsubscribe(self):
        """Unsubscribed handler should not receive events."""
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(EventType.TASK_STARTED, handler)
        bus.unsubscribe(EventType.TASK_STARTED, handler)

        _run_async(bus.emit(
            ExecutionEvent(type=EventType.TASK_STARTED, execution_id="e1")
        ))

        assert len(received) == 0

    def test_history_buffer(self):
        """Events should be stored in history."""
        bus = EventBus(history_size=10)

        for i in range(5):
            _run_async(bus.emit(
                ExecutionEvent(type=EventType.TASK_STARTED, execution_id=f"e{i}")
            ))

        history = bus.get_history()
        assert len(history) == 5

    def test_history_filtered_by_type(self):
        """History should be filterable by event type."""
        bus = EventBus()

        _run_async(bus.emit(
            ExecutionEvent(type=EventType.TASK_STARTED, execution_id="e1")
        ))
        _run_async(bus.emit(
            ExecutionEvent(type=EventType.TASK_COMPLETED, execution_id="e1")
        ))

        started = bus.get_history(event_type=EventType.TASK_STARTED)
        assert len(started) == 1
        assert started[0].type == EventType.TASK_STARTED

    def test_history_filtered_by_execution_id(self):
        """History should be filterable by execution_id."""
        bus = EventBus()

        _run_async(bus.emit(
            ExecutionEvent(type=EventType.TASK_STARTED, execution_id="exec-A")
        ))
        _run_async(bus.emit(
            ExecutionEvent(type=EventType.TASK_STARTED, execution_id="exec-B")
        ))

        filtered = bus.get_history(execution_id="exec-A")
        assert len(filtered) == 1
        assert filtered[0].execution_id == "exec-A"

    def test_handler_error_isolation(self):
        """One failing handler should not affect others."""
        bus = EventBus()
        received = []

        async def good_handler(event):
            received.append(event)

        async def bad_handler(event):
            raise RuntimeError("Handler failed!")

        bus.subscribe(EventType.TASK_STARTED, bad_handler)
        bus.subscribe(EventType.TASK_STARTED, good_handler)

        _run_async(bus.emit(
            ExecutionEvent(type=EventType.TASK_STARTED, execution_id="e1")
        ))

        assert len(received) == 1  # Good handler still received the event

    def test_subscriber_count(self):
        """subscriber_count should reflect total subscriptions."""
        bus = EventBus()

        async def h1(event): pass
        async def h2(event): pass

        bus.subscribe(EventType.TASK_STARTED, h1)
        bus.subscribe(EventType.TASK_COMPLETED, h2)

        assert bus.subscriber_count == 2

    def test_factory_make_execution_started_event(self):
        """Factory function should create properly typed event."""
        event = make_execution_started_event(
            execution_id="e1",
            agent_role="orchestrator",
            provider_id=1,
            model="gpt-4",
            input_message_count=3,
        )
        assert event.type == EventType.EXECUTION_STARTED
        assert event.execution_id == "e1"
        assert event.agent_role == "orchestrator"

    def test_factory_make_task_completed_event(self):
        """Factory function should create task completed event."""
        event = make_task_completed_event(
            execution_id="e1",
            task_id="t1",
            agent_role="coder",
            tokens_used=500,
            latency_ms=1200,
        )
        assert event.type == EventType.TASK_COMPLETED
        assert event.task_id == "t1"


# ==================================================================
# TASK GRAPH TESTS
# ==================================================================

class TestTaskGraph:
    """Tests for the TaskGraph DAG."""

    def _make_node(self, node_id, role="research", desc="Test task"):
        return TaskNode(
            id=node_id,
            description=desc,
            agent_role=role,
            status=TaskStatus.PENDING,
        )

    def test_add_node(self):
        """Adding a node should increase node count."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))
        assert graph.node_count == 1

    def test_add_edge(self):
        """Adding an edge should increase edge count."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))
        graph.add_node(self._make_node("t2"))
        graph.add_edge("t1", "t2")
        assert graph.edge_count == 1

    def test_cycle_detection(self):
        """Adding a cycle should raise ValueError."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))
        graph.add_node(self._make_node("t2"))
        graph.add_node(self._make_node("t3"))

        graph.add_edge("t1", "t2")
        graph.add_edge("t2", "t3")

        with pytest.raises(ValueError, match="cycle"):
            graph.add_edge("t3", "t1")

    def test_topological_order(self):
        """Topological order should respect dependencies."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))
        graph.add_node(self._make_node("t2"))
        graph.add_node(self._make_node("t3"))

        graph.add_edge("t1", "t2")
        graph.add_edge("t2", "t3")

        order = graph.topological_order()
        assert order.index("t1") < order.index("t2")
        assert order.index("t2") < order.index("t3")

    def test_get_ready_tasks(self):
        """Ready tasks are those with all dependencies completed."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))
        graph.add_node(self._make_node("t2"))
        graph.add_edge("t1", "t2")

        ready = graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "t1"

    def test_ready_tasks_after_completion(self):
        """After completing a dependency, its dependent should become ready."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))
        graph.add_node(self._make_node("t2"))
        graph.add_edge("t1", "t2")

        graph.mark_completed("t1", output="result")

        ready = graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "t2"

    def test_parallel_groups(self):
        """Parallel groups should group independent tasks together."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))
        graph.add_node(self._make_node("t2"))
        graph.add_node(self._make_node("t3"))

        # t1 and t2 are independent; t3 depends on both
        graph.add_edge("t1", "t3")
        graph.add_edge("t2", "t3")

        groups = graph.get_parallel_groups()
        assert len(groups) >= 2
        # First group should contain t1 and t2
        first_group_ids = {n.id for n in groups[0]}
        assert "t1" in first_group_ids
        assert "t2" in first_group_ids

    def test_mark_completed(self):
        """mark_completed should update status and store output."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))

        graph.mark_completed("t1", output="done", tokens=100, latency_ms=50)

        node = graph.get_node("t1")
        assert node.status == TaskStatus.COMPLETED
        assert node.output_data == "done"
        assert node.tokens_used == 100

    def test_mark_failed(self):
        """mark_failed should set FAILED status and error message."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))

        graph.mark_failed("t1", "Something went wrong")

        node = graph.get_node("t1")
        assert node.status == TaskStatus.FAILED
        assert node.error == "Something went wrong"

    def test_is_complete(self):
        """is_complete should be True when all tasks are completed."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))
        graph.add_node(self._make_node("t2"))

        assert not graph.is_complete()

        graph.mark_completed("t1")
        graph.mark_completed("t2")

        assert graph.is_complete()

    def test_has_failed(self):
        """has_failed should be True if any task has FAILED status."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))
        graph.add_node(self._make_node("t2"))

        graph.mark_completed("t1")
        graph.mark_failed("t2", "error")

        assert graph.has_failed()

    def test_build_from_plan(self):
        """build_from_plan should construct graph from plan dict."""
        plan = {
            "intent": "code",
            "execution_strategy": "sequential",
            "tasks": [
                {
                    "id": "task-1",
                    "description": "Research the codebase",
                    "agent_role": "research",
                    "depends_on": [],
                },
                {
                    "id": "task-2",
                    "description": "Write the code",
                    "agent_role": "coder",
                    "depends_on": ["task-1"],
                },
            ],
        }

        graph = TaskGraph("exec-1")
        graph.build_from_plan(plan)

        assert graph.node_count == 2
        assert graph.edge_count == 1

    def test_get_dependencies(self):
        """get_dependencies should return list of dependency task IDs."""
        graph = TaskGraph("exec-1")
        graph.add_node(self._make_node("t1"))
        graph.add_node(self._make_node("t2"))
        graph.add_node(self._make_node("t3"))
        graph.add_edge("t1", "t3")
        graph.add_edge("t2", "t3")

        deps = graph.get_dependencies("t3")
        assert set(deps) == {"t1", "t2"}


# ==================================================================
# LIVE EXECUTION STORE TESTS
# ==================================================================

class TestExecutionStore:
    """Tests for the LiveExecutionStore."""

    def test_create_execution(self):
        """create_execution should initialize an ActiveExecution."""
        store = LiveExecutionStore()
        exec_id = store.create_execution(
            execution_id="exec-1",
            conversation_id=1,
            provider_id=1,
            model="gpt-4",
        )
        assert exec_id.execution_id == "exec-1"

        execution = store.get_execution("exec-1")
        assert execution is not None
        assert execution.state == ExecutionState.IDLE
        assert execution.provider_id == 1
        assert execution.model == "gpt-4"

    def test_update_state(self):
        """update_state should change the execution state."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)

        store.update_state("exec-1", ExecutionState.PLANNING)

        execution = store.get_execution("exec-1")
        assert execution.state == ExecutionState.PLANNING

    def test_set_current_agent(self):
        """set_current_agent should update the current agent field."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)

        store.set_current_agent("exec-1", "research", task_id="task-1")

        execution = store.get_execution("exec-1")
        assert execution.current_agent == "research"
        assert execution.current_task_id == "task-1"

    def test_task_lifecycle(self):
        """Tasks should move through pending → running → completed."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)

        store.add_task("exec-1", "task-1")
        execution = store.get_execution("exec-1")
        assert "task-1" in execution.pending_tasks

        store.start_task("exec-1", "task-1")
        execution = store.get_execution("exec-1")
        assert "task-1" in execution.running_tasks
        assert "task-1" not in execution.pending_tasks

        store.complete_task("exec-1", "task-1", tokens=500, latency_ms=100)
        execution = store.get_execution("exec-1")
        assert "task-1" in execution.completed_tasks
        assert "task-1" not in execution.running_tasks

    def test_fail_task(self):
        """fail_task should move task to failed list."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)
        store.add_task("exec-1", "task-1")
        store.start_task("exec-1", "task-1")

        store.fail_task("exec-1", "task-1", error="API timeout")

        execution = store.get_execution("exec-1")
        assert "task-1" in execution.failed_tasks

    def test_complete_execution(self):
        """complete_execution should set state to COMPLETED."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)

        store.complete_execution("exec-1", total_tokens=1000, total_latency_ms=5000)

        execution = store.get_execution("exec-1")
        assert execution.state == ExecutionState.COMPLETED
        assert execution.total_tokens == 1000

    def test_fail_execution(self):
        """fail_execution should set state to FAILED with error."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)

        store.fail_execution("exec-1", error="Critical failure")

        execution = store.get_execution("exec-1")
        assert execution.state == ExecutionState.FAILED
        assert execution.error_message == "Critical failure"

    def test_cancel_execution(self):
        """cancel_execution should set state to CANCELLED."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)

        store.cancel_execution("exec-1")

        execution = store.get_execution("exec-1")
        assert execution.state == ExecutionState.CANCELLED

    def test_record_retry(self):
        """record_retry should increment retry count."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)

        store.record_retry("exec-1")
        store.record_retry("exec-1")

        execution = store.get_execution("exec-1")
        assert execution.retry_count == 2

    def test_record_tokens(self):
        """record_tokens should add to total token count."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)

        store.record_tokens("exec-1", 500)
        store.record_tokens("exec-1", 300)

        execution = store.get_execution("exec-1")
        assert execution.total_tokens == 800

    def test_get_execution_dict(self):
        """get_execution_dict should return serializable dict."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1, provider_id=1, model="gpt-4")

        result = store.get_execution_dict("exec-1")
        assert result is not None
        assert result["execution_id"] == "exec-1"
        assert result["state"] == ExecutionState.IDLE.value
        assert result["provider_id"] == 1

    def test_get_all_active(self):
        """get_all_active should return non-terminal executions."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)
        store.create_execution("exec-2", conversation_id=2)

        store.complete_execution("exec-1", 0, 0)

        active = store.get_all_active()
        active_ids = [e["execution_id"] for e in active]
        assert "exec-2" in active_ids
        assert "exec-1" not in active_ids

    def test_get_by_conversation(self):
        """get_by_conversation should find execution by conversation ID."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=42)

        execution = store.get_by_conversation(42)
        assert execution is not None
        assert execution.execution_id == "exec-1"

    def test_active_count_property(self):
        """active_count should return number of non-terminal executions."""
        store = LiveExecutionStore()
        store.create_execution("exec-1", conversation_id=1)
        store.create_execution("exec-2", conversation_id=2)

        assert store.active_count == 2

        store.complete_execution("exec-1", 0, 0)
        assert store.active_count == 1

    def test_singleton_accessor(self):
        """get_execution_store should return a singleton."""
        store1 = get_execution_store()
        store2 = get_execution_store()
        assert store1 is store2

    def test_set_execution_store(self):
        """set_execution_store should replace the singleton."""
        original = get_execution_store()
        new_store = LiveExecutionStore()

        set_execution_store(new_store)
        assert get_execution_store() is new_store

        # Restore original
        set_execution_store(original)


# ==================================================================
# PLUGGABLE AGENT REGISTRY TESTS
# ==================================================================

class TestPluggableAgentRegistry:
    """Tests for the PluggableAgentRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        registry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        registry.clear()

    def test_register_custom_agent(self):
        """register should store the agent class."""
        class MyAgent(BaseAgent):
            async def chat(self, messages, provider_id=None, model=None, **kwargs):
                return {"content": "test"}

            async def stream(self, messages, provider_id=None, model=None, **kwargs):
                yield "test"

            def buildPrompt(self, messages, **kwargs):
                return "test"

            def validate(self):
                return True

            def getCapabilities(self):
                return ["custom"]

        registration = registry.register(MyAgent)

        assert registration.role is not None
        assert registration.agent_cls == MyAgent
        assert registry.is_registered(registration.role)

    def test_register_with_explicit_config(self):
        """register should accept explicit AgentConfig."""
        class DataAgent(BaseAgent):
            async def chat(self, messages, provider_id=None, model=None, **kwargs):
                return {"content": "data"}

            async def stream(self, messages, provider_id=None, model=None, **kwargs):
                yield "data"

            def buildPrompt(self, messages, **kwargs):
                return "data"

            def validate(self):
                return True

            def getCapabilities(self):
                return ["data_processing"]

        config = AgentConfig(
            name="Data Processor",
            role="data_processor",
            description="Processes data",
            capabilities=["data_processing"],
            system_prompt="You process data.",
        )

        registration = registry.register(DataAgent, config=config)
        assert registration.role == "data_processor"
        assert registration.config.name == "Data Processor"

    def test_register_rejects_non_baseagent(self):
        """register should reject classes that don't extend BaseAgent."""
        class NotAnAgent:
            pass

        with pytest.raises(TypeError, match="must extend BaseAgent"):
            registry.register(NotAnAgent)

    def test_register_rejects_builtin_role(self):
        """register should reject role names that conflict with built-in roles."""
        class FakePlanner(BaseAgent):
            async def chat(self, messages, **kwargs):
                return {}

            async def stream(self, messages, **kwargs):
                yield ""

            def buildPrompt(self, messages, **kwargs):
                return ""

            def validate(self):
                return True

            def getCapabilities(self):
                return []

        config = AgentConfig(
            name="Fake",
            role="planner",  # Built-in role
            description="Fake planner",
            capabilities=[],
            system_prompt="",
        )

        with pytest.raises(ValueError, match="built-in"):
            registry.register(FakePlanner, config=config)

    def test_unregister(self):
        """unregister should remove the agent."""
        class TempAgent(BaseAgent):
            async def chat(self, messages, **kwargs):
                return {}

            async def stream(self, messages, **kwargs):
                yield ""

            def buildPrompt(self, messages, **kwargs):
                return ""

            def validate(self):
                return True

            def getCapabilities(self):
                return []

        registration = registry.register(TempAgent)
        assert registry.is_registered(registration.role)

        result = registry.unregister(registration.role)
        assert result is True
        assert not registry.is_registered(registration.role)

    def test_unregister_nonexistent(self):
        """unregister should return False for unknown role."""
        result = registry.unregister("nonexistent_role")
        assert result is False

    def test_get_factory(self):
        """get_factory should return a callable."""
        class FactoryAgent(BaseAgent):
            async def chat(self, messages, **kwargs):
                return {}

            async def stream(self, messages, **kwargs):
                yield ""

            def buildPrompt(self, messages, **kwargs):
                return ""

            def validate(self):
                return True

            def getCapabilities(self):
                return []

        registration = registry.register(FactoryAgent)
        factory = registry.get_factory(registration.role)

        assert factory is not None
        assert callable(factory)

    def test_get_config(self):
        """get_config should return the AgentConfig."""
        class ConfigAgent(BaseAgent):
            async def chat(self, messages, **kwargs):
                return {}

            async def stream(self, messages, **kwargs):
                yield ""

            def buildPrompt(self, messages, **kwargs):
                return ""

            def validate(self):
                return True

            def getCapabilities(self):
                return []

        config = AgentConfig(
            name="Config Test",
            role="config_test",
            description="Test config retrieval",
            capabilities=["testing"],
            system_prompt="Test",
        )

        registry.register(ConfigAgent, config=config)
        retrieved = registry.get_config("config_test")

        assert retrieved is not None
        assert retrieved.name == "Config Test"

    def test_get_all_configs(self):
        """get_all_configs should return dict of all configs."""
        class Agent1(BaseAgent):
            async def chat(self, messages, **kwargs): return {}
            async def stream(self, messages, **kwargs): yield ""
            def buildPrompt(self, messages, **kwargs): return ""
            def validate(self): return True
            def getCapabilities(self): return []

        class Agent2(BaseAgent):
            async def chat(self, messages, **kwargs): return {}
            async def stream(self, messages, **kwargs): yield ""
            def buildPrompt(self, messages, **kwargs): return ""
            def validate(self): return True
            def getCapabilities(self): return []

        registry.register(Agent1, config=AgentConfig(
            name="A1", role="agent_1", description="d", capabilities=[], system_prompt=""
        ))
        registry.register(Agent2, config=AgentConfig(
            name="A2", role="agent_2", description="d", capabilities=[], system_prompt=""
        ))

        configs = registry.get_all_configs()
        assert "agent_1" in configs
        assert "agent_2" in configs

    def test_get_all_capability_descriptions(self):
        """get_all_capability_descriptions should return list of dicts."""
        class CapAgent(BaseAgent):
            async def chat(self, messages, **kwargs): return {}
            async def stream(self, messages, **kwargs): yield ""
            def buildPrompt(self, messages, **kwargs): return ""
            def validate(self): return True
            def getCapabilities(self): return []

        registry.register(CapAgent, config=AgentConfig(
            name="Cap", role="cap_agent", description="Has capabilities",
            capabilities=["cap1", "cap2"], system_prompt="",
        ))

        descriptions = registry.get_all_capability_descriptions()
        assert len(descriptions) == 1
        assert descriptions[0]["capabilities"] == ["cap1", "cap2"]

    def test_count_and_roles(self):
        """count and roles properties should reflect registrations."""
        class A1(BaseAgent):
            async def chat(self, messages, **kwargs): return {}
            async def stream(self, messages, **kwargs): yield ""
            def buildPrompt(self, messages, **kwargs): return ""
            def validate(self): return True
            def getCapabilities(self): return []

        assert registry.count == 0
        assert registry.roles == []

        registry.register(A1, config=AgentConfig(
            name="A1", role="a1", description="d", capabilities=[], system_prompt=""
        ))

        assert registry.count == 1
        assert "a1" in registry.roles

    def test_class_name_to_role_conversion(self):
        """_class_name_to_role should convert PascalCase to snake_case."""
        assert _class_name_to_role("MyCustomAgent") == "my_custom"
        assert _class_name_to_role("DataProcessor") == "data_processor"
        # SQLAgent converts to s_q_l due to consecutive capitals
        assert _class_name_to_role("SQLAgent") == "s_q_l"

    def test_singleton_pattern(self):
        """PluggableAgentRegistry should be a singleton."""
        r1 = PluggableAgentRegistry()
        r2 = PluggableAgentRegistry()
        assert r1 is r2


# ==================================================================
# PLANNER AGENT FALLBACK TESTS
# ==================================================================

class TestPlannerFallback:
    """Tests for the PlannerAgent fallback plan generation."""

    def test_intent_classification_code(self):
        """Code-related keywords should classify as code intent."""
        from agents.specialized.planner import PlannerAgent

        planner = PlannerAgent.__new__(PlannerAgent)
        intent = planner._classify_intent_fallback("write a python function to sort a list")
        assert intent == "code"

    def test_intent_classification_research(self):
        """Research-related keywords should classify as research intent."""
        from agents.specialized.planner import PlannerAgent

        planner = PlannerAgent.__new__(PlannerAgent)
        intent = planner._classify_intent_fallback("search for information about quantum computing")
        assert intent == "research"

    def test_intent_classification_analysis(self):
        """Analysis-related keywords should classify as analysis intent."""
        from agents.specialized.planner import PlannerAgent

        planner = PlannerAgent.__new__(PlannerAgent)
        intent = planner._classify_intent_fallback("analyze the data and provide insights")
        assert intent == "analysis"

    def test_intent_classification_memory(self):
        """Memory-related keywords should classify as memory intent."""
        from agents.specialized.planner import PlannerAgent

        planner = PlannerAgent.__new__(PlannerAgent)
        intent = planner._classify_intent_fallback("remember this conversation and store it")
        assert intent == "memory"

    def test_intent_classification_tool(self):
        """Tool-related keywords should classify as tool_execution intent."""
        from agents.specialized.planner import PlannerAgent

        planner = PlannerAgent.__new__(PlannerAgent)
        intent = planner._classify_intent_fallback("execute the file tool and run terminal command")
        assert intent == "tool_execution"

    def test_intent_classification_default(self):
        """Unknown keywords should default to conversation intent."""
        from agents.specialized.planner import PlannerAgent

        planner = PlannerAgent.__new__(PlannerAgent)
        intent = planner._classify_intent_fallback("hello how are you today")
        assert intent == "conversation"

    def test_intent_to_role_mapping(self):
        """_intent_to_role should map intents to agent roles."""
        from agents.specialized.planner import PlannerAgent

        planner = PlannerAgent.__new__(PlannerAgent)

        assert planner._intent_to_role("code") == "coder"
        assert planner._intent_to_role("research") == "research"
        assert planner._intent_to_role("analysis") == "analyst"
        assert planner._intent_to_role("memory") == "memory"
        assert planner._intent_to_role("tool_execution") == "tool"
        assert planner._intent_to_role("conversation") == "research"  # Default fallback

    def test_fallback_plan_structure(self):
        """_fallback_plan should produce a valid plan structure."""
        from agents.specialized.planner import PlannerAgent

        planner = PlannerAgent.__new__(PlannerAgent)
        plan = planner._fallback_plan("write a python function")

        assert "intent" in plan
        assert "execution_strategy" in plan
        assert "tasks" in plan
        assert len(plan["tasks"]) >= 1
        assert "id" in plan["tasks"][0]
        assert "agent_role" in plan["tasks"][0]
        assert "description" in plan["tasks"][0]


# ==================================================================
# AGENT CONFIG TESTS
# ==================================================================

class TestAgentConfig:
    """Tests for the AgentConfig schema and DEFAULT_AGENTS."""

    def test_default_agents_count(self):
        """Should have exactly 6 default agents."""
        assert len(DEFAULT_AGENTS) == 6

    def test_default_agents_roles(self):
        """All 6 roles should be present in DEFAULT_AGENTS."""
        expected_roles = {
            AgentRole.PLANNER.value,
            AgentRole.RESEARCH.value,
            AgentRole.CODER.value,
            AgentRole.ANALYST.value,
            AgentRole.MEMORY.value,
            AgentRole.TOOL.value,
        }
        assert set(DEFAULT_AGENTS.keys()) == expected_roles

    def test_agent_config_to_dict(self):
        """to_dict should serialize config to a dict."""
        config = DEFAULT_AGENTS[AgentRole.PLANNER.value]
        d = config.to_dict()

        assert "name" in d
        assert "role" in d
        assert "system_prompt" in d
        assert "capabilities" in d

    def test_agent_config_from_dict(self):
        """from_dict should deserialize config from a dict."""
        config = DEFAULT_AGENTS[AgentRole.CODER.value]
        d = config.to_dict()

        restored = AgentConfig.from_dict(d)
        assert restored.name == config.name
        assert restored.role == config.role

    def test_planner_config(self):
        """Planner should have requires_plan=False (it IS the planner)."""
        config = DEFAULT_AGENTS[AgentRole.PLANNER.value]
        assert config.requires_plan is False

    def test_coder_config_preferred_model(self):
        """Coder should prefer gemini-2.5-pro model."""
        config = DEFAULT_AGENTS[AgentRole.CODER.value]
        assert config.preferred_model == "gemini-2.5-pro"

    def test_tool_agent_has_all_tools(self):
        """Tool agent should have access to all 6 tools."""
        config = DEFAULT_AGENTS[AgentRole.TOOL.value]
        assert len(config.tools) == 6

    def test_research_agent_parallelizable(self):
        """Research agent should be parallelizable."""
        config = DEFAULT_AGENTS[AgentRole.RESEARCH.value]
        assert config.parallelizable is True


# ==================================================================
# ORCHESTRATOR TESTS
# ==================================================================

class TestOrchestrator:
    """Tests for the Orchestrator execution pipeline."""

    @pytest.mark.asyncio
    async def test_orchestrator_run_with_mocked_planner(self, db_session):
        """Orchestrator should execute a plan end-to-end with mocked agents."""
        from agents.orchestration.orchestrator import Orchestrator
        from agents.orchestration.execution_store import LiveExecutionStore

        # Use a fresh execution store
        test_store = LiveExecutionStore()

        orchestrator = Orchestrator(
            db=db_session,
            provider_id=1,
            model="gpt-4",
            execution_store=test_store,
        )

        # Mock the planner to return a simple plan
        mock_plan = {
            "intent": "general",
            "execution_strategy": "sequential",
            "tasks": [
                {
                    "id": "task-1",
                    "description": "Research the topic",
                    "agent_role": "research",
                    "dependencies": [],
                },
            ],
        }

        # Mock AIRuntime.chat for synthesis
        async def mock_chat(*args, **kwargs):
            return "Synthesized response"

        with patch.object(orchestrator, '_phase_plan', new_callable=AsyncMock) as mock_plan_phase:
            mock_plan_phase.return_value = mock_plan

            # Mock the research agent's execute_task
            mock_agent = MagicMock()
            mock_agent.execute_task = AsyncMock(return_value={
                "output": "Research findings",
                "tokens_used": 100,
                "latency_ms": 500,
            })
            mock_agent.validate = MagicMock(return_value=True)

            with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
                with patch('agents.orchestration.orchestrator.AIRuntime') as MockRuntime:
                    MockRuntime.return_value.chat = mock_chat

                    result = await orchestrator.run(
                        user_message="Tell me about AI",
                        conversation_history=[],
                    )

        assert "response" in result
        assert result["response"] == "Synthesized response"
        assert "execution_id" in result
        assert "plan" in result
        assert "task_results" in result

    @pytest.mark.asyncio
    async def test_orchestrator_cancellation(self, db_session):
        """Orchestrator should handle cancellation gracefully."""
        from agents.orchestration.orchestrator import Orchestrator
        from agents.orchestration.execution_store import LiveExecutionStore

        test_store = LiveExecutionStore()
        orchestrator = Orchestrator(
            db=db_session,
            provider_id=1,
            model="gpt-4",
            execution_store=test_store,
        )

        # Start execution in background
        async def mock_plan(*args, **kwargs):
            await asyncio.sleep(0.1)
            return {"intent": "test", "execution_strategy": "sequential", "tasks": []}

        with patch.object(orchestrator, '_phase_plan', new_callable=AsyncMock) as mp:
            mp.return_value = {"intent": "test", "execution_strategy": "sequential", "tasks": []}

            with patch('agents.orchestration.orchestrator.AIRuntime') as MockRuntime:
                async def mock_chat(*args, **kwargs):
                    return "Done"
                MockRuntime.return_value.chat = mock_chat

                # Run and cancel
                task = asyncio.create_task(orchestrator.run("test", []))
                await asyncio.sleep(0.01)

                # Cancel
                exec_ids = list(orchestrator._cancel_events.keys())
                if exec_ids:
                    orchestrator.cancel(exec_ids[0])

                result = await task

        # Should complete (either cancelled or finished with empty plan)
        assert "execution_id" in result

    def test_orchestrator_register_agent_factory(self, db_session):
        """register_agent_factory should add a custom factory."""
        from agents.orchestration.orchestrator import Orchestrator
        from agents.orchestration.execution_store import LiveExecutionStore

        test_store = LiveExecutionStore()
        orchestrator = Orchestrator(
            db=db_session,
            provider_id=1,
            model="gpt-4",
            execution_store=test_store,
        )

        def custom_factory(db, agent_model, config, event_bus):
            return MagicMock()

        orchestrator.register_agent_factory("my_custom_role", custom_factory)

        assert "my_custom_role" in orchestrator._agent_factories

    def test_orchestrator_unregister_builtin_raises(self, db_session):
        """unregister_agent_factory should reject built-in roles."""
        from agents.orchestration.orchestrator import Orchestrator
        from agents.orchestration.execution_store import LiveExecutionStore

        test_store = LiveExecutionStore()
        orchestrator = Orchestrator(
            db=db_session,
            provider_id=1,
            model="gpt-4",
            execution_store=test_store,
        )

        with pytest.raises(ValueError, match="built-in"):
            orchestrator.unregister_agent_factory(AgentRole.PLANNER.value)

    def test_orchestrator_get_agent_health(self, db_session):
        """get_agent_health should return health status."""
        from agents.orchestration.orchestrator import Orchestrator
        from agents.orchestration.execution_store import LiveExecutionStore
        from agents.orchestration.agent_config import AgentHealth

        test_store = LiveExecutionStore()
        orchestrator = Orchestrator(
            db=db_session,
            provider_id=1,
            model="gpt-4",
            execution_store=test_store,
        )

        mock_agent = MagicMock()
        mock_agent.validate = MagicMock(return_value=True)

        with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
            health = orchestrator.get_agent_health("research")

        assert health == AgentHealth.HEALTHY

    def test_orchestrator_get_all_health(self, db_session):
        """get_all_health should return health for all agents."""
        from agents.orchestration.orchestrator import Orchestrator
        from agents.orchestration.execution_store import LiveExecutionStore

        test_store = LiveExecutionStore()
        orchestrator = Orchestrator(
            db=db_session,
            provider_id=1,
            model="gpt-4",
            execution_store=test_store,
        )

        mock_agent = MagicMock()
        mock_agent.validate = MagicMock(return_value=True)

        with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
            health_map = orchestrator.get_all_health()

        assert len(health_map) >= 6  # At least the 6 built-in agents

    def test_orchestrator_get_execution_status(self, db_session):
        """get_execution_status should return execution dict from store."""
        from agents.orchestration.orchestrator import Orchestrator
        from agents.orchestration.execution_store import LiveExecutionStore

        test_store = LiveExecutionStore()
        orchestrator = Orchestrator(
            db=db_session,
            provider_id=1,
            model="gpt-4",
            execution_store=test_store,
        )

        test_store.create_execution("test-exec", conversation_id=1, provider_id=1, model="gpt-4")

        status = orchestrator.get_execution_status("test-exec")
        assert status is not None
        assert status["execution_id"] == "test-exec"

    @pytest.mark.asyncio
    async def test_orchestrator_failover_on_task_failure(self, db_session):
        """Orchestrator should retry and attempt fallback on task failure."""
        from agents.orchestration.orchestrator import Orchestrator
        from agents.orchestration.execution_store import LiveExecutionStore

        test_store = LiveExecutionStore()
        orchestrator = Orchestrator(
            db=db_session,
            provider_id=1,
            model="gpt-4",
            execution_store=test_store,
        )

        mock_plan = {
            "intent": "general",
            "execution_strategy": "sequential",
            "tasks": [
                {
                    "id": "task-1",
                    "description": "Do research",
                    "agent_role": "research",
                    "dependencies": [],
                },
            ],
        }

        # Mock agent that always fails
        mock_agent = MagicMock()
        mock_agent.execute_task = AsyncMock(side_effect=RuntimeError("rate limit exceeded"))
        mock_agent.validate = MagicMock(return_value=True)

        # Mock fallback policy to return None (no fallback available)
        with patch.object(orchestrator, '_phase_plan', new_callable=AsyncMock) as mp:
            mp.return_value = mock_plan

            with patch.object(orchestrator, '_get_agent', return_value=mock_agent):
                with patch('agents.orchestration.orchestrator.AIRuntime') as MockRuntime:
                    async def mock_chat(*args, **kwargs):
                        return "Partial response despite failure"
                    MockRuntime.return_value.chat = mock_chat

                    with patch('agents.orchestration.orchestrator.FallbackPolicy') as MockFallback:
                        MockFallback.return_value.get_fallback.return_value = None

                        result = await orchestrator.run("test", [])

        # Should still complete (synthesis happens even with failed tasks)
        assert "response" in result
        assert "task_results" in result
        # The task should have an error
        task_result = list(result["task_results"].values())[0]
        assert task_result.get("error") is not None


# ==================================================================
# AGENT COMMUNICATION TESTS
# ==================================================================

class TestAgentCommunication:
    """Tests for the AgentMessage communication protocol."""

    def test_message_creation(self):
        """AgentMessage should be created with all fields."""
        from agents.orchestration.communication import AgentMessage, MessageType

        msg = AgentMessage(
            type=MessageType.TASK_ASSIGNMENT,
            sender="orchestrator",
            receiver="research",
            task_id="task-1",
            payload={"query": "search for X"},
        )

        assert msg.type == MessageType.TASK_ASSIGNMENT
        assert msg.sender == "orchestrator"
        assert msg.receiver == "research"
        assert msg.task_id == "task-1"

    def test_message_to_dict(self):
        """to_dict should serialize message to dict."""
        from agents.orchestration.communication import AgentMessage, MessageType

        msg = AgentMessage(
            type=MessageType.TASK_RESULT,
            sender="research",
            receiver="orchestrator",
            payload={"findings": "result"},
        )

        d = msg.to_dict()
        assert d["type"] == MessageType.TASK_RESULT.value
        assert d["sender"] == "research"

    def test_message_from_dict(self):
        """from_dict should deserialize message from dict."""
        from agents.orchestration.communication import AgentMessage, MessageType

        data = {
            "type": MessageType.TASK_RESULT.value,
            "sender": "coder",
            "receiver": "orchestrator",
            "payload": {"code": "print('hello')"},
        }

        msg = AgentMessage.from_dict(data)
        assert msg.type == MessageType.TASK_RESULT
        assert msg.sender == "coder"

    def test_message_create_reply(self):
        """create_reply should create a reply with swapped sender/receiver."""
        from agents.orchestration.communication import AgentMessage, MessageType

        msg = AgentMessage(
            type=MessageType.TASK_ASSIGNMENT,
            sender="orchestrator",
            receiver="research",
            task_id="task-1",
            correlation_id="corr-123",
            payload={},
        )

        reply = msg.create_reply(MessageType.TASK_RESULT, payload={"result": "done"})

        assert reply.type == MessageType.TASK_RESULT
        assert reply.sender == "research"  # Swapped
        assert reply.receiver == "orchestrator"  # Swapped
        assert reply.correlation_id == "corr-123"  # Linked

    def test_message_is_expired(self):
        """is_expired should return True for old messages."""
        from datetime import datetime, timedelta, timezone
        from agents.orchestration.communication import AgentMessage, MessageType

        msg = AgentMessage(
            type=MessageType.TASK_ASSIGNMENT,
            sender="a",
            receiver="b",
            ttl_ms=100,  # 100ms TTL
            payload={},
        )

        # Message was just created — not expired
        assert not msg.is_expired()

        # Manually set timestamp to the past
        msg.timestamp = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert msg.is_expired()
