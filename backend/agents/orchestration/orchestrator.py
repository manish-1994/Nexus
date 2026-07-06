"""Orchestrator — the central coordination engine of the Agent Operating System.

The Orchestrator is the bridge between the user and the agent swarm. It:
1. Receives the user prompt
2. Delegates to the Planner for task decomposition
3. Builds a TaskGraph (DAG) from the execution plan
4. Dispatches tasks to specialized agents (sequential or parallel)
5. Collects outputs from all agents
6. Synthesizes a final response for the user

Architecture:
    User → Orchestrator.run() → Planner.plan() → TaskGraph
    → [ResearchAgent, CoderAgent, AnalystAgent, MemoryAgent, ToolAgent]
    → Response Synthesis → User

The Orchestrator is the ONLY entry point for user requests in the
Agent Operating System. It replaces the direct DefaultAgent.chat()
path for all non-trivial requests.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from agents.base import BaseAgent
from agents.orchestration.agent_config import (
    AgentConfig,
    AgentHealth,
    AgentRole,
    DEFAULT_AGENTS,
)
from agents.orchestration.communication import (
    AgentMessage,
    MessageType,
    TaskResultPayload,
    SynthesisPayload,
)
from agents.orchestration.event_bus import (
    EventBus,
    EventType,
    ExecutionEvent,
    make_execution_started_event,
    make_execution_completed_event,
    make_task_started_event,
    make_task_completed_event,
)
from agents.orchestration.execution_store import (
    ExecutionState,
    LiveExecutionStore,
    get_execution_store,
)
from agents.orchestration.task_graph import (
    TaskGraph,
    TaskNode,
    TaskStatus,
)
from agents.specialized.planner import PlannerAgent
from agents.specialized.research import ResearchAgent
from agents.specialized.coder import CoderAgent
from agents.specialized.analyst import AnalystAgent
from agents.specialized.memory import MemoryAgent
from agents.specialized.tool import ToolAgent
from models.agent import Agent
from services.ai_runtime import AIRuntime
from services.retry_policy import RetryPolicy, FallbackPolicy
from agents.orchestration.agent_registry import registry as pluggable_registry

logger = logging.getLogger("orchestrator")

# Type alias for agent factory functions
AgentFactory = Callable[[Session, Agent, Optional[AgentConfig], Optional[EventBus]], BaseAgent]


class Orchestrator:
    """Central coordination engine for the Agent Operating System.

    The Orchestrator manages the full lifecycle of a user request:
    planning → task dispatch → execution → synthesis → response.

    It supports:
    - Sequential execution (tasks run one after another)
    - Parallel execution (independent tasks run concurrently)
    - Mixed execution (parallel groups with sequential dependencies)
    - Streaming response synthesis
    - Cancellation and error recovery
    - Event emission for UI observability
    """

    def __init__(
        self,
        db: Session,
        provider_id: Optional[int] = None,
        model: Optional[str] = None,
        event_bus: Optional[EventBus] = None,
        execution_store: Optional[LiveExecutionStore] = None,
    ):
        self.db = db
        self.provider_id = provider_id
        self.model = model
        self._event_bus = event_bus
        self._execution_store = execution_store or get_execution_store()

        # Agent factory registry — maps role to constructor
        self._agent_factories: Dict[str, AgentFactory] = {
            AgentRole.PLANNER.value: self._create_planner,
            AgentRole.RESEARCH.value: self._create_research,
            AgentRole.CODER.value: self._create_coder,
            AgentRole.ANALYST.value: self._create_analyst,
            AgentRole.MEMORY.value: self._create_memory,
            AgentRole.TOOL.value: self._create_tool,
        }

        # Load custom agents from the PluggableAgentRegistry
        self._load_custom_agents()

        # Agent cache — created agents reused within a session
        self._agent_cache: Dict[str, BaseAgent] = {}

        # Cancellation support
        self._cancel_events: Dict[str, asyncio.Event] = {}

    # ------------------------------------------------------------------
    # Agent factory methods
    # ------------------------------------------------------------------

    def _create_planner(
        self, db: Session, agent_model: Agent, config: Optional[AgentConfig], event_bus: Optional[EventBus]
    ) -> PlannerAgent:
        return PlannerAgent(db, agent_model, config, event_bus)

    def _create_research(
        self, db: Session, agent_model: Agent, config: Optional[AgentConfig], event_bus: Optional[EventBus]
    ) -> ResearchAgent:
        return ResearchAgent(db, agent_model, config, event_bus)

    def _create_coder(
        self, db: Session, agent_model: Agent, config: Optional[AgentConfig], event_bus: Optional[EventBus]
    ) -> CoderAgent:
        return CoderAgent(db, agent_model, config, event_bus)

    def _create_analyst(
        self, db: Session, agent_model: Agent, config: Optional[AgentConfig], event_bus: Optional[EventBus]
    ) -> AnalystAgent:
        return AnalystAgent(db, agent_model, config, event_bus)

    def _create_memory(
        self, db: Session, agent_model: Agent, config: Optional[AgentConfig], event_bus: Optional[EventBus]
    ) -> MemoryAgent:
        return MemoryAgent(db, agent_model, config, event_bus)

    def _create_tool(
        self, db: Session, agent_model: Agent, config: Optional[AgentConfig], event_bus: Optional[EventBus]
    ) -> ToolAgent:
        return ToolAgent(db, agent_model, config, event_bus)

    def _load_custom_agents(self) -> None:
        """Load custom agent factories from the PluggableAgentRegistry.

        This is called once during Orchestrator initialization.
        Any agents registered via registry.register() before the
        Orchestrator is created will be automatically available.
        """
        for role in pluggable_registry.roles:
            factory = pluggable_registry.get_factory(role)
            if factory:
                self._agent_factories[role] = factory
                logger.info(
                    "Loaded custom agent factory: role=%s",
                    role,
                )

    # ------------------------------------------------------------------
    # Agent resolution
    # ------------------------------------------------------------------

    def _get_agent(self, role: str) -> BaseAgent:
        """Get or create an agent for the given role.

        Agents are cached per Orchestrator instance to avoid
        redundant construction during a single execution.
        """
        if role in self._agent_cache:
            return self._agent_cache[role]

        factory = self._agent_factories.get(role)
        if not factory:
            raise ValueError(f"No agent factory registered for role: {role}")

        config = DEFAULT_AGENTS.get(role)
        # Create a minimal Agent model for the agent constructor
        agent_model = Agent(
            name=config.name if config else role,
            system_prompt=config.system_prompt if config else "",
            provider_id=self.provider_id,
            enabled=True,
        )

        agent = factory(self.db, agent_model, config, self._event_bus)
        self._agent_cache[role] = agent
        return agent

    def register_agent_factory(self, role: str, factory: AgentFactory) -> None:
        """Register a custom agent factory for a role.

        This enables pluggable agents — users can register their own
        agent implementations without modifying the Orchestrator code.

        Args:
            role: The agent role string (e.g., "my_custom_agent")
            factory: A callable that creates the agent instance
        """
        self._agent_factories[role] = factory
        logger.info("Registered agent factory for role: %s", role)

    def unregister_agent_factory(self, role: str) -> None:
        """Remove a custom agent factory."""
        # Don't allow removing built-in roles
        builtin_roles = {r.value for r in AgentRole}
        if role in builtin_roles:
            raise ValueError(f"Cannot unregister built-in role: {role}")
        self._agent_factories.pop(role, None)
        self._agent_cache.pop(role, None)

    # ------------------------------------------------------------------
    # Main execution entry point
    # ------------------------------------------------------------------

    async def run(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        conversation_id: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Execute a user request through the full Agent OS pipeline.

        This is the primary entry point. It:
        1. Creates an execution record
        2. Runs the Planner to decompose the request
        3. Builds a TaskGraph from the plan
        4. Dispatches tasks to specialized agents
        5. Synthesizes the final response

        Args:
            user_message: The user's message content
            conversation_history: Previous messages for context
            conversation_id: Database conversation ID
            stream: Whether to use streaming for synthesis

        Returns:
            Dict with keys:
                response: The final synthesized response text
                execution_id: The execution identifier
                plan: The execution plan used
                task_results: Results from each task
                agents_used: List of agent roles invoked
                total_tokens: Estimated token usage
                total_latency_ms: Total execution time
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()

        # Create cancel event for this execution
        cancel_event = asyncio.Event()
        self._cancel_events[execution_id] = cancel_event

        # Register in execution store
        self._execution_store.create_execution(
            execution_id=execution_id,
            conversation_id=conversation_id,
            provider_id=self.provider_id,
            model=self.model,
        )

        # Emit execution started
        if self._event_bus:
            self._event_bus.emit_sync(make_execution_started_event(
                execution_id=execution_id,
                agent_role=AgentRole.ORCHESTRATOR.value,
                provider_id=self.provider_id,
                model=self.model,
                input_message_count=len(conversation_history or []) + 1,
            ))

        try:
            # Phase 1: Planning
            plan = await self._phase_plan(user_message, conversation_history, execution_id)

            # Check cancellation
            if cancel_event.is_set():
                return self._cancelled_result(execution_id, start_time)

            # Phase 2: Build task graph
            task_graph = self._phase_build_graph(plan, execution_id)

            # Phase 3: Execute tasks
            task_results = await self._phase_execute(
                task_graph, plan, conversation_history, execution_id, cancel_event
            )

            # Check cancellation
            if cancel_event.is_set():
                return self._cancelled_result(execution_id, start_time)

            # Phase 4: Synthesize response
            final_response = await self._phase_synthesize(
                user_message, plan, task_results, execution_id, stream
            )

            total_latency_ms = int((time.time() - start_time) * 1000)
            total_tokens = sum(
                tr.get("tokens_used", 0) for tr in task_results.values()
            )
            agents_used = list(set(
                tr.get("agent_role", "") for tr in task_results.values()
            ))

            # Mark execution complete
            self._execution_store.complete_execution(
                execution_id, total_tokens, total_latency_ms
            )

            # Emit execution completed
            if self._event_bus:
                self._event_bus.emit_sync(make_execution_completed_event(
                    execution_id=execution_id,
                    total_tokens=total_tokens,
                    total_latency_ms=total_latency_ms,
                    agents_used=agents_used,
                ))

            # Cleanup
            self._cancel_events.pop(execution_id, None)

            return {
                "response": final_response,
                "execution_id": execution_id,
                "plan": plan,
                "task_results": task_results,
                "agents_used": agents_used,
                "total_tokens": total_tokens,
                "total_latency_ms": total_latency_ms,
            }

        except Exception as exc:
            logger.exception("Orchestrator execution failed: %s", exc)
            self._execution_store.fail_execution(execution_id, str(exc))

            if self._event_bus:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.EXECUTION_FAILED,
                    execution_id=execution_id,
                    agent_role=AgentRole.ORCHESTRATOR.value,
                    data={"error": str(exc)},
                ))

            self._cancel_events.pop(execution_id, None)
            raise

    async def run_stream(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        conversation_id: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Execute a user request with streaming response synthesis.

        Yields chunks of the final synthesized response as they are
        generated, providing real-time feedback to the user while
        background tasks complete.

        Args:
            user_message: The user's message content
            conversation_history: Previous messages for context
            conversation_id: Database conversation ID

        Yields:
            Response text chunks (str)
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()

        cancel_event = asyncio.Event()
        self._cancel_events[execution_id] = cancel_event

        self._execution_store.create_execution(
            execution_id=execution_id,
            conversation_id=conversation_id,
            provider_id=self.provider_id,
            model=self.model,
        )

        if self._event_bus:
            self._event_bus.emit_sync(make_execution_started_event(
                execution_id=execution_id,
                agent_role=AgentRole.ORCHESTRATOR.value,
                provider_id=self.provider_id,
                model=self.model,
                input_message_count=len(conversation_history or []) + 1,
            ))

        try:
            # Phase 1: Planning
            plan = await self._phase_plan(user_message, conversation_history, execution_id)

            if cancel_event.is_set():
                yield "Execution cancelled."
                return

            # Phase 2: Build task graph
            task_graph = self._phase_build_graph(plan, execution_id)

            # Phase 3: Execute tasks (background)
            task_results = await self._phase_execute(
                task_graph, plan, conversation_history, execution_id, cancel_event
            )

            if cancel_event.is_set():
                yield "Execution cancelled."
                return

            # Phase 4: Stream synthesis
            self._execution_store.update_state(execution_id, ExecutionState.STREAMING)
            if self._event_bus:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.STREAMING_STARTED,
                    execution_id=execution_id,
                    agent_role=AgentRole.ORCHESTRATOR.value,
                ))

            synthesis_messages = self._build_synthesis_prompt(
                user_message, plan, task_results
            )

            runtime = AIRuntime(self.db)
            chunk_index = 0
            async for chunk in runtime.stream(
                messages=synthesis_messages,
                provider_id=self.provider_id,
                model=self.model,
            ):
                if cancel_event.is_set():
                    break
                if self._event_bus:
                    self._event_bus.emit_sync(ExecutionEvent(
                        type=EventType.STREAMING_CHUNK,
                        execution_id=execution_id,
                        agent_role=AgentRole.ORCHESTRATOR.value,
                        data={"chunk": chunk, "chunk_index": chunk_index},
                    ))
                chunk_index += 1
                yield chunk

            if self._event_bus:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.STREAMING_COMPLETED,
                    execution_id=execution_id,
                ))

            total_latency_ms = int((time.time() - start_time) * 1000)
            total_tokens = sum(
                tr.get("tokens_used", 0) for tr in task_results.values()
            )
            agents_used = list(set(
                tr.get("agent_role", "") for tr in task_results.values()
            ))

            self._execution_store.complete_execution(
                execution_id, total_tokens, total_latency_ms
            )

            if self._event_bus:
                self._event_bus.emit_sync(make_execution_completed_event(
                    execution_id=execution_id,
                    total_tokens=total_tokens,
                    total_latency_ms=total_latency_ms,
                    agents_used=agents_used,
                ))

        except Exception as exc:
            logger.exception("Orchestrator streaming execution failed: %s", exc)
            self._execution_store.fail_execution(execution_id, str(exc))
            if self._event_bus:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.EXECUTION_FAILED,
                    execution_id=execution_id,
                    data={"error": str(exc)},
                ))
            yield f"\n\n[Error: {exc}]"

        finally:
            self._cancel_events.pop(execution_id, None)

    # ------------------------------------------------------------------
    # Execution phases
    # ------------------------------------------------------------------

    async def _phase_plan(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]],
        execution_id: str,
    ) -> Dict[str, Any]:
        """Phase 1: Decompose the user request into an execution plan."""
        self._execution_store.update_state(execution_id, ExecutionState.PLANNING)

        planner = self._get_agent(AgentRole.PLANNER.value)
        if not isinstance(planner, PlannerAgent):
            raise RuntimeError("Planner agent is not a PlannerAgent instance")

        plan = await planner.plan(
            user_message=user_message,
            conversation_history=conversation_history,
            provider_id=self.provider_id,
            model=self.model,
            execution_id=execution_id,
        )

        logger.info(
            "Plan created: intent=%s tasks=%d strategy=%s",
            plan.get("intent"),
            len(plan.get("tasks", [])),
            plan.get("execution_strategy"),
        )

        return plan

    def _phase_build_graph(
        self, plan: Dict[str, Any], execution_id: str
    ) -> TaskGraph:
        """Phase 2: Build a TaskGraph DAG from the execution plan."""
        graph = TaskGraph(execution_id)
        graph.build_from_plan(plan)

        logger.info(
            "Task graph built: nodes=%d edges=%d",
            graph.node_count,
            graph.edge_count,
        )

        return graph

    async def _phase_execute(
        self,
        graph: TaskGraph,
        plan: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]],
        execution_id: str,
        cancel_event: asyncio.Event,
    ) -> Dict[str, Dict[str, Any]]:
        """Phase 3: Execute all tasks in the graph.

        Dispatches tasks according to the execution strategy:
        - sequential: One at a time in topological order
        - parallel: All independent tasks concurrently
        - mixed: Parallel groups with sequential dependencies
        """
        strategy = plan.get("execution_strategy", "sequential")
        task_results: Dict[str, Dict[str, Any]] = {}

        if strategy == "parallel" and graph.edge_count == 0:
            # All tasks are independent — run them concurrently
            task_results = await self._execute_parallel(
                graph, conversation_history, execution_id, cancel_event
            )
        elif strategy == "mixed":
            # Run in parallel groups respecting dependencies
            task_results = await self._execute_mixed(
                graph, conversation_history, execution_id, cancel_event
            )
        else:
            # Sequential execution in topological order
            task_results = await self._execute_sequential(
                graph, conversation_history, execution_id, cancel_event
            )

        return task_results

    async def _execute_sequential(
        self,
        graph: TaskGraph,
        conversation_history: Optional[List[Dict[str, Any]]],
        execution_id: str,
        cancel_event: asyncio.Event,
    ) -> Dict[str, Dict[str, Any]]:
        """Execute tasks one at a time in topological order."""
        results: Dict[str, Dict[str, Any]] = {}

        try:
            order = graph.topological_order()
        except ValueError:
            # Graph has a cycle — execute in insertion order
            order = [n.id for n in graph.get_all_nodes()]

        for task_id in order:
            if cancel_event.is_set():
                break

            node = graph.get_node(task_id)
            if not node:
                continue

            result = await self._execute_single_task(
                node, graph, results, conversation_history, execution_id, cancel_event
            )
            results[task_id] = result

        return results

    async def _execute_parallel(
        self,
        graph: TaskGraph,
        conversation_history: Optional[List[Dict[str, Any]]],
        execution_id: str,
        cancel_event: asyncio.Event,
    ) -> Dict[str, Dict[str, Any]]:
        """Execute all independent tasks concurrently."""
        nodes = graph.get_all_nodes()
        tasks = []

        for node in nodes:
            if cancel_event.is_set():
                break
            tasks.append(
                self._execute_single_task(
                    node, graph, {}, conversation_history, execution_id, cancel_event
                )
            )

        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        results: Dict[str, Dict[str, Any]] = {}
        for node, result in zip(nodes, gathered):
            if isinstance(result, Exception):
                results[node.id] = {
                    "task_id": node.id,
                    "agent_role": node.agent_role,
                    "output": None,
                    "error": str(result),
                    "tokens_used": 0,
                    "latency_ms": 0,
                }
            else:
                results[node.id] = result

        return results

    async def _execute_mixed(
        self,
        graph: TaskGraph,
        conversation_history: Optional[List[Dict[str, Any]]],
        execution_id: str,
        cancel_event: asyncio.Event,
    ) -> Dict[str, Dict[str, Any]]:
        """Execute tasks in parallel groups respecting dependencies."""
        results: Dict[str, Dict[str, Any]] = {}

        while not graph.is_complete() and not cancel_event.is_set():
            # Get the next parallel group
            groups = graph.get_parallel_groups()
            if not groups:
                # Fall back to ready tasks
                ready = graph.get_ready_tasks()
                if not ready:
                    break
                groups = [ready]

            # Execute the first group in parallel
            current_group = groups[0]
            tasks = []
            for node in current_group:
                tasks.append(
                    self._execute_single_task(
                        node, graph, results, conversation_history, execution_id, cancel_event
                    )
                )

            gathered = await asyncio.gather(*tasks, return_exceptions=True)

            for node, result in zip(current_group, gathered):
                if isinstance(result, Exception):
                    graph.mark_failed(node.id, str(result))
                    results[node.id] = {
                        "task_id": node.id,
                        "agent_role": node.agent_role,
                        "output": None,
                        "error": str(result),
                        "tokens_used": 0,
                        "latency_ms": 0,
                    }
                else:
                    graph.mark_completed(
                        node.id,
                        output=result.get("output"),
                        tokens=result.get("tokens_used", 0),
                        latency_ms=result.get("latency_ms", 0),
                    )
                    results[node.id] = result

        return results

    async def _execute_single_task(
        self,
        node: TaskNode,
        graph: TaskGraph,
        accumulated_results: Dict[str, Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, Any]]],
        execution_id: str,
        cancel_event: asyncio.Event,
    ) -> Dict[str, Any]:
        """Execute a single task node with the appropriate agent.

        Includes full failover logic:
        1. Retry with exponential backoff (RetryPolicy)
        2. Fallback to alternative provider/model (FallbackPolicy)
        3. Report failure via event bus and execution store
        4. Continue with remaining tasks if possible
        """
        start_time = time.time()

        # Update graph status
        graph.update_node_status(node.id, TaskStatus.RUNNING)

        # Emit task started
        if self._event_bus:
            self._event_bus.emit_sync(make_task_started_event(
                execution_id=execution_id,
                task_id=node.id,
                agent_role=node.agent_role,
                description=node.description,
            ))

        # Build context from dependency outputs
        context = self._build_task_context(node, graph, accumulated_results)

        # Get the agent for this task's role
        try:
            agent = self._get_agent(node.agent_role)
        except ValueError as exc:
            logger.error("No agent for role %s: %s", node.agent_role, exc)
            graph.mark_failed(node.id, str(exc))
            return {
                "task_id": node.id,
                "agent_role": node.agent_role,
                "output": None,
                "error": str(exc),
                "tokens_used": 0,
                "latency_ms": 0,
            }

        # Execute with retry and failover
        retry_policy = RetryPolicy(max_retries=3)
        fallback_policy = FallbackPolicy(self.db)
        current_provider_id = self.provider_id
        current_model = self.model
        last_error: Optional[Exception] = None

        for attempt in range(retry_policy.max_retries + 1):
            if cancel_event.is_set():
                graph.mark_failed(node.id, "Execution cancelled")
                return {
                    "task_id": node.id,
                    "agent_role": node.agent_role,
                    "output": None,
                    "error": "Execution cancelled",
                    "tokens_used": 0,
                    "latency_ms": int((time.time() - start_time) * 1000),
                }

            try:
                result = await self._invoke_agent(
                    agent, node, context, execution_id, current_provider_id, current_model
                )

                # Success — build and return result
                latency_ms = int((time.time() - start_time) * 1000)
                task_result = {
                    "task_id": node.id,
                    "agent_role": node.agent_role,
                    "output": result.get("output") if isinstance(result, dict) else result,
                    "tokens_used": result.get("tokens_used", 0) if isinstance(result, dict) else 0,
                    "latency_ms": latency_ms,
                    "error": result.get("error") if isinstance(result, dict) else None,
                    "provider_used": current_provider_id,
                    "model_used": current_model,
                    "retry_count": attempt,
                }
                if isinstance(result, dict):
                    task_result["structured_output"] = result

                graph.mark_completed(
                    node.id,
                    output=task_result["output"],
                    tokens=task_result["tokens_used"],
                    latency_ms=latency_ms,
                )

                # Emit task completed
                if self._event_bus:
                    self._event_bus.emit_sync(make_task_completed_event(
                        execution_id=execution_id,
                        task_id=node.id,
                        agent_role=node.agent_role,
                        tokens_used=task_result["tokens_used"],
                        latency_ms=latency_ms,
                    ))

                return task_result

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Task %s attempt %d/%d failed: %s",
                    node.id, attempt + 1, retry_policy.max_retries + 1, exc,
                )

                # Record retry in execution store
                self._execution_store.record_retry(execution_id)

                # Emit retry event
                if self._event_bus:
                    self._event_bus.emit_sync(ExecutionEvent(
                        type=EventType.RETRY_ATTEMPTED,
                        execution_id=execution_id,
                        task_id=node.id,
                        agent_role=node.agent_role,
                        data={
                            "attempt": attempt + 1,
                            "max_retries": retry_policy.max_retries,
                            "error": str(exc),
                            "provider_id": current_provider_id,
                            "model": current_model,
                        },
                    ))

                # Check if we should retry with same provider/model
                if retry_policy.should_retry(attempt, exc):
                    await retry_policy.wait_before_retry(attempt)
                    continue

                # Retries exhausted — try fallback provider/model
                fallback = fallback_policy.get_fallback(
                    agent=agent._agent_model if hasattr(agent, '_agent_model') else Agent(
                        name=node.agent_role,
                        system_prompt="",
                        provider_id=current_provider_id,
                        enabled=True,
                    ),
                    primary_provider_id=current_provider_id,
                    primary_model=current_model,
                    failed_error=exc,
                )

                if fallback:
                    logger.info(
                        "Task %s: falling back to provider=%s model=%s",
                        node.id, fallback["provider_id"], fallback["model"],
                    )
                    current_provider_id = fallback["provider_id"]
                    current_model = fallback["model"]

                    # Emit failover event
                    if self._event_bus:
                        self._event_bus.emit_sync(ExecutionEvent(
                            type=EventType.FAILOVER_TRIGGERED,
                            execution_id=execution_id,
                            task_id=node.id,
                            agent_role=node.agent_role,
                            data={
                                "from_provider": self.provider_id,
                                "from_model": self.model,
                                "to_provider": current_provider_id,
                                "to_model": current_model,
                                "error": str(exc),
                            },
                        ))

                    # Record failover in execution store
                    self._execution_store.record_retry(execution_id)

                    # Retry with fallback provider/model (one more attempt)
                    try:
                        result = await self._invoke_agent(
                            agent, node, context, execution_id, current_provider_id, current_model
                        )
                        latency_ms = int((time.time() - start_time) * 1000)
                        task_result = {
                            "task_id": node.id,
                            "agent_role": node.agent_role,
                            "output": result.get("output") if isinstance(result, dict) else result,
                            "tokens_used": result.get("tokens_used", 0) if isinstance(result, dict) else 0,
                            "latency_ms": latency_ms,
                            "error": result.get("error") if isinstance(result, dict) else None,
                            "provider_used": current_provider_id,
                            "model_used": current_model,
                            "retry_count": attempt + 1,
                            "fallback_used": True,
                        }
                        if isinstance(result, dict):
                            task_result["structured_output"] = result

                        graph.mark_completed(
                            node.id,
                            output=task_result["output"],
                            tokens=task_result["tokens_used"],
                            latency_ms=latency_ms,
                        )

                        if self._event_bus:
                            self._event_bus.emit_sync(make_task_completed_event(
                                execution_id=execution_id,
                                task_id=node.id,
                                agent_role=node.agent_role,
                                tokens_used=task_result["tokens_used"],
                                latency_ms=latency_ms,
                            ))

                        return task_result

                    except Exception as fallback_exc:
                        last_error = fallback_exc
                        logger.exception(
                            "Task %s: fallback provider also failed: %s",
                            node.id, fallback_exc,
                        )

                # All retries and fallbacks exhausted — report failure
                break

        # Task failed after all attempts
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = str(last_error) if last_error else "Unknown error"

        logger.error("Task %s permanently failed: %s", node.id, error_msg)
        graph.mark_failed(node.id, error_msg)

        # Emit task failed event
        if self._event_bus:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.TASK_FAILED,
                execution_id=execution_id,
                task_id=node.id,
                agent_role=node.agent_role,
                data={
                    "error": error_msg,
                    "retry_count": attempt,
                    "latency_ms": latency_ms,
                },
            ))

        return {
            "task_id": node.id,
            "agent_role": node.agent_role,
            "output": None,
            "error": error_msg,
            "tokens_used": 0,
            "latency_ms": latency_ms,
            "retry_count": attempt,
        }

    async def _invoke_agent(
        self,
        agent: BaseAgent,
        node: TaskNode,
        context: Dict[str, Any],
        execution_id: str,
        provider_id: Optional[int],
        model: Optional[str],
    ) -> Any:
        """Invoke the agent's execute_task or chat method.

        Extracted as a separate method so retry/failover logic can
        call it with different provider/model combinations.
        """
        if hasattr(agent, 'execute_task'):
            return await agent.execute_task(
                task_description=node.description,
                context=context,
                provider_id=provider_id,
                model=model,
                execution_id=execution_id,
                task_id=node.id,
            )

        # Fallback to chat() for agents without execute_task
        messages = [
            {"role": "system", "content": f"Task: {node.description}"},
        ]
        if context:
            messages.append({
                "role": "system",
                "content": f"Context: {json.dumps(context)}",
            })
        messages.append({"role": "user", "content": node.description})
        chat_result = await agent.chat(
            messages=messages,
            provider_id=provider_id,
            model=model,
        )
        return {
            "output": chat_result.get("content", ""),
            "tokens_used": len(chat_result.get("content", "")) // 4,
            "latency_ms": 0,
        }

    def _build_task_context(
        self,
        node: TaskNode,
        graph: TaskGraph,
        accumulated_results: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build context dict for a task from its dependencies' outputs."""
        context: Dict[str, Any] = {}

        deps = graph.get_dependencies(node.id)
        for dep_id in deps:
            dep_result = accumulated_results.get(dep_id, {})
            dep_node = graph.get_node(dep_id)
            if dep_node:
                context[dep_node.agent_role] = dep_result.get("output")
                # Also include structured output if available
                if "structured_output" in dep_result:
                    context[f"{dep_node.agent_role}_structured"] = dep_result["structured_output"]

        return context

    # ------------------------------------------------------------------
    # Response synthesis
    # ------------------------------------------------------------------

    async def _phase_synthesize(
        self,
        user_message: str,
        plan: Dict[str, Any],
        task_results: Dict[str, Dict[str, Any]],
        execution_id: str,
        stream: bool = False,
    ) -> str:
        """Phase 4: Synthesize a final response from all task outputs."""
        self._execution_store.update_state(execution_id, ExecutionState.CALLING_PROVIDER)

        if self._event_bus:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.SYNTHESIS_STARTED,
                execution_id=execution_id,
                agent_role=AgentRole.ORCHESTRATOR.value,
            ))

        synthesis_messages = self._build_synthesis_prompt(
            user_message, plan, task_results
        )

        runtime = AIRuntime(self.db)
        response_text = await runtime.chat(
            messages=synthesis_messages,
            provider_id=self.provider_id,
            model=self.model,
        )

        if self._event_bus:
            self._event_bus.emit_sync(ExecutionEvent(
                type=EventType.SYNTHESIS_COMPLETED,
                execution_id=execution_id,
                data={"response_length": len(response_text)},
            ))

        return response_text

    def _build_synthesis_prompt(
        self,
        user_message: str,
        plan: Dict[str, Any],
        task_results: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Build the prompt for response synthesis.

        Combines all agent outputs into a coherent final response
        that directly addresses the user's original request.
        """
        system_prompt = """You are the Nexus Response Synthesizer.

Your job is to combine the outputs from multiple specialized AI agents
into a single, coherent, helpful response for the user.

Rules:
1. Address the user's original question directly
2. Integrate findings from all agents seamlessly
3. Cite which agent provided which information when relevant
4. Be concise but comprehensive
5. Use a natural, conversational tone
6. If any agent failed, acknowledge the gap gracefully
7. Format code blocks, lists, and structured data clearly
8. Do NOT mention the internal agent architecture unless relevant

The user should feel like they received one thoughtful answer,
not a patchwork of agent outputs."""

        # Build the agent outputs section
        agent_outputs_text = ""
        for task_id, result in task_results.items():
            role = result.get("agent_role", "unknown")
            output = result.get("output", "")
            error = result.get("error")

            agent_outputs_text += f"\n### {role.upper()} (Task: {task_id})\n"
            if error:
                agent_outputs_text += f"[FAILED: {error}]\n"
            elif output:
                # Truncate very long outputs
                if len(str(output)) > 2000:
                    agent_outputs_text += str(output)[:2000] + "...[truncated]\n"
                else:
                    agent_outputs_text += str(output) + "\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Original user request: {user_message}

Execution plan intent: {plan.get('intent', 'unknown')}
Execution strategy: {plan.get('execution_strategy', 'unknown')}

Agent outputs:
{agent_outputs_text}

Please synthesize a final response for the user."""},
        ]

        return messages

    # ------------------------------------------------------------------
    # Cancellation
    # ------------------------------------------------------------------

    def cancel(self, execution_id: str) -> bool:
        """Cancel an active execution.

        Args:
            execution_id: The execution to cancel

        Returns:
            True if the execution was found and cancelled
        """
        cancel_event = self._cancel_events.get(execution_id)
        if cancel_event:
            cancel_event.set()
            self._execution_store.cancel_execution(execution_id)

            if self._event_bus:
                self._event_bus.emit_sync(ExecutionEvent(
                    type=EventType.EXECUTION_CANCELLED,
                    execution_id=execution_id,
                ))

            return True
        return False

    def _cancelled_result(
        self, execution_id: str, start_time: float
    ) -> Dict[str, Any]:
        """Build a result dict for cancelled executions."""
        self._execution_store.cancel_execution(execution_id)
        self._cancel_events.pop(execution_id, None)

        return {
            "response": "Execution cancelled.",
            "execution_id": execution_id,
            "plan": {},
            "task_results": {},
            "agents_used": [],
            "total_tokens": 0,
            "total_latency_ms": int((time.time() - start_time) * 1000),
            "cancelled": True,
        }

    # ------------------------------------------------------------------
    # Health & status
    # ------------------------------------------------------------------

    def get_agent_health(self, role: str) -> AgentHealth:
        """Check the health of an agent by role."""
        try:
            agent = self._get_agent(role)
            if agent.validate():
                return AgentHealth.HEALTHY
            return AgentHealth.DEGRADED
        except Exception:
            return AgentHealth.UNHEALTHY

    def get_all_health(self) -> Dict[str, AgentHealth]:
        """Get health status for all registered agents."""
        return {
            role: self.get_agent_health(role)
            for role in self._agent_factories
        }

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of an execution."""
        return self._execution_store.get_execution_dict(execution_id)