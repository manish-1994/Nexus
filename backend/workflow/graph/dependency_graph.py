"""Dependency graph for workflow task scheduling.

Implements a Directed Acyclic Graph (DAG) for task dependencies
with topological sorting and parallel group detection.
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskNode:
    """A node in the task dependency graph."""
    task_id: str
    agent_role: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    input: Dict[str, Any] = field(default_factory=dict)
    output: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def agent(self) -> str:
        """Backward-compatible alias for agent_role."""
        return self.agent_role
    
    def __hash__(self):
        return hash(self.task_id)
    
    def __eq__(self, other):
        if isinstance(other, TaskNode):
            return self.task_id == other.task_id
        return False


class DependencyGraph:
    """Directed Acyclic Graph for task dependencies.
    
    Provides:
    - Topological sorting for execution order
    - Parallel group detection for concurrent execution
    - Dependency validation (cycle detection)
    - Ready task identification
    """
    
    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)  # task_id -> set of dependent task_ids
        self.reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)  # task_id -> set of prerequisite task_ids
        self._topo_order: Optional[List[str]] = None
        self._parallel_groups: Optional[List[List[str]]] = None
    
    def add_node(self, node: TaskNode) -> None:
        """Add a task node to the graph."""
        if node.task_id in self.nodes:
            raise ValueError(f"Task {node.task_id} already exists in graph")
        self.nodes[node.task_id] = node
        # Initialize adjacency sets
        self.adjacency[node.task_id] = set()
        self.reverse_adjacency[node.task_id] = set(node.dependencies)
        # Add reverse edges
        for dep in node.dependencies:
            self.adjacency[dep].add(node.task_id)
        # Invalidate cached computations
        self._topo_order = None
        self._parallel_groups = None
    
    def add_edge(self, from_task: str, to_task: str) -> None:
        """Add a dependency edge: to_task depends on from_task."""
        if from_task not in self.nodes:
            raise ValueError(f"Task {from_task} not found in graph")
        if to_task not in self.nodes:
            raise ValueError(f"Task {to_task} not found in graph")
        
        if to_task in self.adjacency[from_task]:
            return  # Edge already exists
        
        self.adjacency[from_task].add(to_task)
        self.reverse_adjacency[to_task].add(from_task)
        self.nodes[to_task].dependencies.append(from_task)
        
        # Invalidate cached computations
        self._topo_order = None
        self._parallel_groups = None
    
    def has_cycle(self) -> bool:
        """Check if the graph has cycles using Kahn's algorithm."""
        in_degree = {task_id: len(self.reverse_adjacency[task_id]) for task_id in self.nodes}
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        visited = 0
        
        while queue:
            task_id = queue.popleft()
            visited += 1
            for dependent in self.adjacency[task_id]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        return visited != len(self.nodes)
    
    def topological_order(self) -> List[str]:
        """Get topological order of tasks (Kahn's algorithm).
        
        Returns list of task_ids in execution order.
        Raises ValueError if cycle detected.
        """
        if self._topo_order is not None:
            return self._topo_order
        
        if self.has_cycle():
            raise ValueError("Graph contains cycles, cannot compute topological order")
        
        in_degree = {task_id: len(self.reverse_adjacency[task_id]) for task_id in self.nodes}
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        order = []
        
        while queue:
            task_id = queue.popleft()
            order.append(task_id)
            for dependent in self.adjacency[task_id]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        self._topo_order = order
        return order
    
    def get_parallel_groups(self) -> List[List[str]]:
        """Get parallel execution groups.
        
        Returns list of groups, where each group contains task_ids
        that can be executed in parallel (no dependencies between them).
        """
        if self._parallel_groups is not None:
            return self._parallel_groups
        
        order = self.topological_order()
        groups = []
        remaining = set(order)
        
        while remaining:
            # Find all tasks with no unmet dependencies in remaining
            ready = []
            for task_id in remaining:
                deps = self.reverse_adjacency[task_id]
                if not deps or all(d not in remaining for d in deps):
                    ready.append(task_id)
            
            if not ready:
                # Should not happen if graph is valid
                break
            
            groups.append(ready)
            for task_id in ready:
                remaining.remove(task_id)
        
        self._parallel_groups = groups
        return groups
    
    def get_ready_tasks(self, completed: Set[str]) -> List[str]:
        """Get tasks that are ready to execute given completed tasks."""
        ready = []
        for task_id, node in self.nodes.items():
            if node.status != "pending":
                continue
            deps = self.reverse_adjacency[task_id]
            if all(dep in completed for dep in deps):
                ready.append(task_id)
        return ready
    
    def get_dependents(self, task_id: str) -> Set[str]:
        """Get all tasks that depend on the given task (transitive)."""
        dependents = set()
        queue = deque([task_id])
        visited = set()
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for dep in self.adjacency[current]:
                dependents.add(dep)
                queue.append(dep)
        
        return dependents
    
    def get_prerequisites(self, task_id: str) -> Set[str]:
        """Get all prerequisites for the given task (transitive)."""
        prereqs = set()
        queue = deque([task_id])
        visited = set()
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for prereq in self.reverse_adjacency[current]:
                prereqs.add(prereq)
                queue.append(prereq)
        
        return prereqs
    
    def update_node_status(self, task_id: str, status: str, error: Optional[str] = None) -> None:
        """Update the status of a task node."""
        if task_id in self.nodes:
            self.nodes[task_id].status = status
            if error:
                self.nodes[task_id].output = {"error": error}
    
    def get_node(self, task_id: str) -> Optional[TaskNode]:
        """Get a task node by ID."""
        return self.nodes.get(task_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize graph to dictionary."""
        return {
            "nodes": {
                task_id: {
                    "task_id": node.task_id,
                    "agent_role": node.agent_role,
                    "agent": node.agent_role,  # backward compat
                    "description": node.description,
                    "dependencies": node.dependencies,
                    "status": node.status,
                    "input": node.input,
                    "output": node.output,
                    "metadata": node.metadata,
                }
                for task_id, node in self.nodes.items()
            },
            "edges": [
                {"from": from_task, "to": to_task}
                for from_task, deps in self.adjacency.items()
                for to_task in deps
            ],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DependencyGraph":
        """Create graph from dictionary."""
        graph = cls()
        # Add nodes
        for task_id, node_data in data.get("nodes", {}).items():
            node = TaskNode(
                task_id=node_data["task_id"],
                agent_role=node_data.get("agent_role", node_data.get("agent", "")),
                description=node_data["description"],
                dependencies=node_data.get("dependencies", []),
                status=node_data.get("status", "pending"),
                input=node_data.get("input", {}),
                output=node_data.get("output", {}),
                metadata=node_data.get("metadata", {}),
            )
            graph.add_node(node)
        # Add edges
        for edge in data.get("edges", []):
            graph.add_edge(edge["from"], edge["to"])
        return graph


def build_graph_from_plan(execution_plan: Dict[str, Any]) -> DependencyGraph:
    """Build a DependencyGraph from a Planner execution plan.
    
    This is the critical bridge between the Planner (which decides WHAT to do)
    and the Workflow Execution Engine (which decides HOW to execute it).
    
    The execution plan format from the Planner:
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
    
    Args:
        execution_plan: The execution plan dict from the Planner agent
        
    Returns:
        DependencyGraph with all tasks as nodes and dependencies as edges
    """
    graph = DependencyGraph()
    tasks = execution_plan.get("tasks", [])
    
    if not tasks:
        logger.warning("build_graph_from_plan: execution plan has no tasks")
        return graph
    
    # Add all nodes first
    for task_data in tasks:
        task_id = task_data.get("id", task_data.get("task_id", ""))
        if not task_id:
            logger.warning("build_graph_from_plan: skipping task without id")
            continue
        
        node = TaskNode(
            task_id=task_id,
            agent_role=task_data.get("agent_role", task_data.get("agent", "")),
            description=task_data.get("description", ""),
            dependencies=task_data.get("depends_on", task_data.get("dependencies", [])),
            status="pending",
            input=task_data.get("input", task_data.get("input_data", {})),
            output={},
            metadata={
                "priority": task_data.get("priority", 1),
                "expected_output": task_data.get("expected_output", ""),
                "parameters": task_data.get("parameters", {}),
            },
        )
        graph.add_node(node)
    
    # Add all edges (dependencies)
    for task_data in tasks:
        task_id = task_data.get("id", task_data.get("task_id", ""))
        if not task_id or task_id not in graph.nodes:
            continue
        
        depends_on = task_data.get("depends_on", task_data.get("dependencies", []))
        for dep_id in depends_on:
            if dep_id in graph.nodes:
                try:
                    graph.add_edge(dep_id, task_id)
                except ValueError:
                    logger.warning(
                        "build_graph_from_plan: could not add edge %s -> %s",
                        dep_id, task_id
                    )
    
    # Validate graph
    if graph.has_cycle():
        logger.error("build_graph_from_plan: cycle detected in execution plan!")
        # Return graph anyway — scheduler will handle cycle detection
    
    logger.info(
        "build_graph_from_plan: built graph with %d nodes, intent=%s, strategy=%s",
        len(graph.nodes),
        execution_plan.get("intent", "unknown"),
        execution_plan.get("execution_strategy", "sequential"),
    )
    
    return graph