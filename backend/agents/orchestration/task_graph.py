"""Task Graph — DAG representation of agent executions.

Models an execution plan as a Directed Acyclic Graph where:
- Nodes represent tasks assigned to specific agents
- Edges represent dependencies (task B depends on task A's output)

Supports topological sorting for execution ordering and cycle detection
to guarantee valid execution plans.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid


class TaskStatus(str, Enum):
    """Lifecycle status of a task node."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_TOOL = "waiting_for_tool"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    """A single task in the execution DAG.

    Attributes:
        id: Unique task identifier
        description: Human-readable description of the task
        agent_role: The agent role assigned to execute this task
        status: Current lifecycle status
        priority: Execution priority (1 = highest)
        input_data: Data passed to the agent for this task
        output_data: Result produced by the agent
        error: Error message if the task failed
        tokens_used: Token count for this task
        latency_ms: Execution duration in milliseconds
        tool_calls: Tool invocations made during this task
        started_at: ISO timestamp when execution began
        completed_at: ISO timestamp when execution finished
        metadata: Arbitrary key-value metadata
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    agent_role: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1
    input_data: Any = None
    output_data: Any = None
    error: Optional[str] = None
    tokens_used: int = 0
    latency_ms: int = 0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "agent_role": self.agent_role,
            "status": self.status.value,
            "priority": self.priority,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "tool_calls": self.tool_calls,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskNode":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            description=data.get("description", ""),
            agent_role=data.get("agent_role", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=data.get("priority", 1),
            input_data=data.get("input_data"),
            output_data=data.get("output_data"),
            error=data.get("error"),
            tokens_used=data.get("tokens_used", 0),
            latency_ms=data.get("latency_ms", 0),
            tool_calls=data.get("tool_calls", []),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TaskEdge:
    """A directed edge representing a dependency between two tasks.

    If task B depends on task A, there is an edge A → B.
    Task B cannot start until task A completes successfully.
    """

    from_task: str  # Source task ID (the dependency)
    to_task: str    # Target task ID (depends on the source)
    data_flow: Optional[str] = None  # Description of what data flows


class TaskGraph:
    """Directed Acyclic Graph of tasks for a single execution.

    Provides:
    - Topological sorting for execution ordering
    - Cycle detection to guarantee valid DAGs
    - Ready-task identification (all dependencies satisfied)
    - Parallel group extraction (tasks that can run concurrently)
    """

    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self._nodes: Dict[str, TaskNode] = {}
        self._edges: List[TaskEdge] = []
        # Adjacency: task_id → set of task_ids that depend on it
        self._dependents: Dict[str, Set[str]] = {}
        # Reverse adjacency: task_id → set of task_ids it depends on
        self._dependencies: Dict[str, Set[str]] = {}

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def add_node(self, node: TaskNode) -> None:
        """Add a task node to the graph.

        Raises ValueError if a node with the same ID already exists.
        """
        if node.id in self._nodes:
            raise ValueError(f"Task node '{node.id}' already exists in graph")
        self._nodes[node.id] = node
        self._dependents.setdefault(node.id, set())
        self._dependencies.setdefault(node.id, set())

    def add_edge(self, from_task: str, to_task: str, data_flow: Optional[str] = None) -> None:
        """Add a dependency edge: to_task depends on from_task.

        Raises ValueError if either node doesn't exist or if the edge
        would create a cycle.
        """
        if from_task not in self._nodes:
            raise ValueError(f"Source task '{from_task}' not in graph")
        if to_task not in self._nodes:
            raise ValueError(f"Target task '{to_task}' not in graph")

        # Check for duplicate edge
        if to_task in self._dependents.get(from_task, set()):
            return  # Edge already exists

        # Add edge
        edge = TaskEdge(from_task=from_task, to_task=to_task, data_flow=data_flow)
        self._edges.append(edge)
        self._dependents[from_task].add(to_task)
        self._dependencies[to_task].add(from_task)

        # Verify no cycle was created
        if self._has_cycle():
            # Rollback
            self._edges.pop()
            self._dependents[from_task].discard(to_task)
            self._dependencies[to_task].discard(from_task)
            raise ValueError(
                f"Edge {from_task} → {to_task} would create a cycle in the task graph"
            )

    def build_from_plan(self, plan: Dict[str, Any]) -> None:
        """Build the entire graph from an execution plan dict.

        The plan should have a 'tasks' list where each task has:
        - id, description, agent_role, depends_on, priority

        Args:
            plan: Execution plan dictionary from the Planner
        """
        tasks = plan.get("tasks", [])

        # Add all nodes first
        for task_data in tasks:
            node = TaskNode(
                id=task_data["id"],
                description=task_data.get("description", ""),
                agent_role=task_data.get("agent_role", ""),
                priority=task_data.get("priority", 1),
            )
            self.add_node(node)

        # Add all edges
        for task_data in tasks:
            task_id = task_data["id"]
            for dep_id in task_data.get("depends_on", []):
                if dep_id in self._nodes:
                    self.add_edge(dep_id, task_id)

    # ------------------------------------------------------------------
    # Graph queries
    # ------------------------------------------------------------------

    def get_node(self, task_id: str) -> Optional[TaskNode]:
        """Get a task node by ID."""
        return self._nodes.get(task_id)

    def get_all_nodes(self) -> List[TaskNode]:
        """Get all task nodes."""
        return list(self._nodes.values())

    def get_all_edges(self) -> List[TaskEdge]:
        """Get all dependency edges."""
        return list(self._edges)

    def get_dependencies(self, task_id: str) -> Set[str]:
        """Get the set of task IDs that this task depends on."""
        return self._dependencies.get(task_id, set())

    def get_dependents(self, task_id: str) -> Set[str]:
        """Get the set of task IDs that depend on this task."""
        return self._dependents.get(task_id, set())

    def is_ready(self, task_id: str) -> bool:
        """Check if a task is ready to execute (all dependencies completed).

        A task is ready when:
        - It exists in the graph
        - It is in PENDING or QUEUED status
        - All its dependencies have status COMPLETED
        """
        node = self._nodes.get(task_id)
        if not node:
            return False
        if node.status not in (TaskStatus.PENDING, TaskStatus.QUEUED):
            return False
        for dep_id in self._dependencies.get(task_id, set()):
            dep_node = self._nodes.get(dep_id)
            if not dep_node or dep_node.status != TaskStatus.COMPLETED:
                return False
        return True

    def get_ready_tasks(self) -> List[TaskNode]:
        """Get all tasks that are ready to execute right now."""
        return [node for node in self._nodes.values() if self.is_ready(node.id)]

    def get_parallel_groups(self) -> List[List[TaskNode]]:
        """Group ready tasks into parallel execution batches.

        Uses topological levels: tasks at the same level (same distance
        from root) with no dependencies on each other can run in parallel.

        Returns:
            List of task groups, where each group can run in parallel.
            Groups are ordered by execution sequence.
        """
        # Compute topological levels
        levels = self._topological_levels()

        # Group ready tasks by level
        groups: Dict[int, List[TaskNode]] = {}
        for task_id, level in levels.items():
            node = self._nodes[task_id]
            if node.status in (TaskStatus.PENDING, TaskStatus.QUEUED):
                groups.setdefault(level, []).append(node)

        # Return groups sorted by level
        result = []
        for level in sorted(groups.keys()):
            result.append(groups[level])

        return result

    def topological_order(self) -> List[str]:
        """Return task IDs in topological order (dependencies first).

        Raises ValueError if the graph has a cycle.
        """
        if self._has_cycle():
            raise ValueError("Cannot compute topological order: graph has a cycle")

        in_degree: Dict[str, int] = {
            task_id: len(deps) for task_id, deps in self._dependencies.items()
        }

        # Kahn's algorithm
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            # Sort by priority within same level for deterministic ordering
            queue.sort(key=lambda tid: self._nodes[tid].priority)
            current = queue.pop(0)
            result.append(current)

            for dependent in self._dependents.get(current, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(self._nodes):
            raise ValueError("Graph has a cycle — topological sort incomplete")

        return result

    # ------------------------------------------------------------------
    # Status management
    # ------------------------------------------------------------------

    def update_node_status(self, task_id: str, status: TaskStatus) -> None:
        """Update the status of a task node."""
        node = self._nodes.get(task_id)
        if not node:
            raise ValueError(f"Task '{task_id}' not found in graph")
        node.status = status

    def mark_completed(self, task_id: str, output: Any = None, tokens: int = 0, latency_ms: int = 0) -> None:
        """Mark a task as completed with its output."""
        node = self._nodes.get(task_id)
        if not node:
            raise ValueError(f"Task '{task_id}' not found in graph")
        node.status = TaskStatus.COMPLETED
        node.output_data = output
        node.tokens_used = tokens
        node.latency_ms = latency_ms

    def mark_failed(self, task_id: str, error: str) -> None:
        """Mark a task as failed with an error message."""
        node = self._nodes.get(task_id)
        if not node:
            raise ValueError(f"Task '{task_id}' not found in graph")
        node.status = TaskStatus.FAILED
        node.error = error

    def is_complete(self) -> bool:
        """Check if the entire graph has completed (all tasks terminal)."""
        terminal_states = {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.SKIPPED,
        }
        return all(node.status in terminal_states for node in self._nodes.values())

    def has_failed(self) -> bool:
        """Check if any task in the graph has failed."""
        return any(node.status == TaskStatus.FAILED for node in self._nodes.values())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _has_cycle(self) -> bool:
        """Detect whether the graph contains a cycle using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {tid: WHITE for tid in self._nodes}

        def dfs(task_id: str) -> bool:
            color[task_id] = GRAY
            for dependent in self._dependents.get(task_id, set()):
                if color[dependent] == GRAY:
                    return True  # Back edge → cycle
                if color[dependent] == WHITE:
                    if dfs(dependent):
                        return True
            color[task_id] = BLACK
            return False

        for tid in self._nodes:
            if color[tid] == WHITE:
                if dfs(tid):
                    return True
        return False

    def _topological_levels(self) -> Dict[str, int]:
        """Compute the topological level (distance from source) for each node.

        Level 0 = no dependencies (root tasks).
        Level N = longest path from any root task.
        """
        levels: Dict[str, int] = {}

        def compute_level(task_id: str) -> int:
            if task_id in levels:
                return levels[task_id]
            deps = self._dependencies.get(task_id, set())
            if not deps:
                levels[task_id] = 0
            else:
                levels[task_id] = 1 + max(compute_level(d) for d in deps)
            return levels[task_id]

        for tid in self._nodes:
            compute_level(tid)

        return levels

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)