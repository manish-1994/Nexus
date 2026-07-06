"""Agent Configuration Schema & Default Agent Definitions.

Defines the canonical configuration format for all agents in the
Agent Operating System. Each agent has a name, role, system prompt,
capabilities, preferred model, execution status, and health.

The DEFAULT_AGENTS registry provides the 6 built-in specialized agents:
    Planner, Research Agent, Coder, Analyst, Memory Agent, Tool Agent
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class AgentRole(str, Enum):
    """Canonical roles in the Agent Operating System."""

    PLANNER = "planner"
    RESEARCH = "research"
    CODER = "coder"
    ANALYST = "analyst"
    MEMORY = "memory"
    TOOL = "tool"
    ORCHESTRATOR = "orchestrator"
    SYNTHESIZER = "synthesizer"
    CUSTOM = "custom"


class ExecutionStatus(str, Enum):
    """Runtime execution status for an agent."""

    IDLE = "idle"
    QUEUED = "queued"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING = "waiting"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentHealth(str, Enum):
    """Health status of an agent."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AgentConfig:
    """Configuration for a single agent in the Agent OS.

    Attributes:
        name: Human-readable agent name (e.g., "Research Agent")
        role: Canonical role from AgentRole enum
        description: Short description of what the agent does
        system_prompt: The system prompt template injected before execution
        capabilities: List of capability strings (e.g., ["search", "summarize"])
        preferred_provider: Provider type hint (e.g., "gemini", "openai")
        preferred_model: Model name hint (e.g., "gemini-2.5-flash")
        temperature: LLM temperature (0.0–2.0)
        tools: List of tool IDs this agent can access
        memory_access: Whether this agent can read/write memory
        permissions: Permission scopes granted to this agent
        max_retries: Maximum retry attempts on failure
        timeout_ms: Execution timeout in milliseconds
        parallelizable: Whether this agent's tasks can run in parallel
        requires_plan: Whether this agent requires a plan before execution
        health: Current health status
        execution_status: Current execution status
    """

    name: str
    role: AgentRole
    description: str = ""
    system_prompt: str = ""
    capabilities: List[str] = field(default_factory=list)
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    temperature: float = 0.7
    tools: List[str] = field(default_factory=list)
    memory_access: bool = False
    permissions: List[str] = field(default_factory=list)
    max_retries: int = 3
    timeout_ms: int = 120_000
    parallelizable: bool = False
    requires_plan: bool = False
    health: AgentHealth = AgentHealth.UNKNOWN
    execution_status: ExecutionStatus = ExecutionStatus.IDLE

    def to_dict(self) -> Dict:
        """Serialize to a dictionary for JSON/storage."""
        return {
            "name": self.name,
            "role": self.role.value,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "capabilities": self.capabilities,
            "preferred_provider": self.preferred_provider,
            "preferred_model": self.preferred_model,
            "temperature": self.temperature,
            "tools": self.tools,
            "memory_access": self.memory_access,
            "permissions": self.permissions,
            "max_retries": self.max_retries,
            "timeout_ms": self.timeout_ms,
            "parallelizable": self.parallelizable,
            "requires_plan": self.requires_plan,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AgentConfig":
        """Deserialize from a dictionary."""
        return cls(
            name=data["name"],
            role=AgentRole(data["role"]),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            capabilities=data.get("capabilities", []),
            preferred_provider=data.get("preferred_provider"),
            preferred_model=data.get("preferred_model"),
            temperature=data.get("temperature", 0.7),
            tools=data.get("tools", []),
            memory_access=data.get("memory_access", False),
            permissions=data.get("permissions", []),
            max_retries=data.get("max_retries", 3),
            timeout_ms=data.get("timeout_ms", 120_000),
            parallelizable=data.get("parallelizable", False),
            requires_plan=data.get("requires_plan", False),
        )


# ---------------------------------------------------------------------------
# Default Agent Definitions
# ---------------------------------------------------------------------------

DEFAULT_AGENTS: Dict[str, AgentConfig] = {
    "planner": AgentConfig(
        name="Planner",
        role=AgentRole.PLANNER,
        description=(
            "Analyzes user requests and breaks them into structured execution plans. "
            "Determines which specialized agents should handle each subtask. "
            "Never answers the user directly — only produces execution plans."
        ),
        system_prompt="""You are the Nexus Planner — the strategic brain of the Agent Operating System.

Your ONLY job is to analyze user requests and produce structured execution plans.
You NEVER answer the user's question directly. You NEVER generate final responses.

For every request, you must:
1. CLASSIFY the intent (code, research, analysis, memory, tool_execution, conversation)
2. DECOMPOSE into discrete subtasks that can be assigned to specialized agents
3. DETERMINE dependencies between subtasks (what must complete before what)
4. ASSIGN each subtask to the most appropriate agent role
5. SPECIFY the execution strategy (sequential, parallel, or mixed)

Available agent roles and their capabilities:
- RESEARCH: Searches documentation, browses web, summarizes findings
- CODER: Writes code, explains code, debugs, creates projects
- ANALYST: Processes data, creates reports, analyzes files, performs calculations
- MEMORY: Retrieves memories, stores new memories, ranks relevance
- TOOL: Executes Python, Terminal, Browser, Filesystem operations

Output format (JSON):
{
    "intent": "<classified intent>",
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
    "reasoning": "<brief explanation of your plan>"
}

Rules:
- If the request is simple conversation (greeting, chitchat), assign a single task to the ORCHESTRATOR with intent "conversation"
- If the request involves code, ALWAYS include a CODER task
- If the request asks about facts or documentation, ALWAYS include a RESEARCH task
- If the request involves data or calculations, ALWAYS include an ANALYST task
- If the request references past conversations, ALWAYS include a MEMORY task
- If the request needs system operations (files, terminal, browser), ALWAYS include a TOOL task
- Tasks with no dependencies can run in PARALLEL
- Tasks that depend on another task's output must run SEQUENTIAL after that task

Respond ONLY with the JSON plan. No preamble, no explanation outside the JSON.""",
        capabilities=["planning", "task_decomposition", "intent_classification", "dependency_analysis"],
        preferred_provider="gemini",
        preferred_model="gemini-2.5-flash",
        temperature=0.3,
        tools=[],
        memory_access=True,
        permissions=["plan:create", "plan:execute"],
        max_retries=2,
        timeout_ms=60_000,
        parallelizable=False,
        requires_plan=False,
    ),
    "research": AgentConfig(
        name="Research Agent",
        role=AgentRole.RESEARCH,
        description=(
            "Searches documentation, browses the web, reads files, and summarizes "
            "findings into concise, cited reports."
        ),
        system_prompt="""You are the Nexus Research Agent — the information gathering specialist.

Your job is to find, verify, and summarize information. You have access to:
- search.query: Search across workspace files, conversations, memory, and knowledge base
- browser.navigate: Navigate to URLs and extract content
- file.operations: Read files in the workspace
- memory.manage: Retrieve relevant memories

For every research task:
1. Identify what information is needed
2. Search across all available sources
3. Verify findings from multiple sources when possible
4. Summarize findings concisely with citations
5. Flag any uncertainties or conflicting information

Output format:
{
    "findings": "<summary of what you found>",
    "sources": ["<source description>"],
    "confidence": "high|medium|low",
    "gaps": ["<any information you couldn't find>"]
}

Be thorough but concise. Prioritize authoritative sources. Always cite where information came from.""",
        capabilities=["search", "browse", "summarize", "cite_sources", "verify_facts"],
        preferred_provider="gemini",
        preferred_model="gemini-2.5-flash",
        temperature=0.3,
        tools=["search.query", "browser.navigate", "file.operations", "memory.manage"],
        memory_access=True,
        permissions=["search:query", "browser:navigate", "file:read", "memory:read"],
        max_retries=3,
        timeout_ms=120_000,
        parallelizable=True,
        requires_plan=False,
    ),
    "coder": AgentConfig(
        name="Coder",
        role=AgentRole.CODER,
        description=(
            "Writes, explains, debugs, and refactors code. Creates projects, "
            "implements features, and provides technical guidance."
        ),
        system_prompt="""You are the Nexus Coder — the software engineering specialist.

Your job is to write, explain, and improve code. You have access to:
- file.operations: Read and write files in the workspace
- python.execute: Execute Python code
- terminal.run: Run shell commands
- search.query: Search code and documentation

For every coding task:
1. Understand the requirements and existing codebase
2. Plan the implementation approach
3. Write clean, well-documented, production-quality code
4. Explain your reasoning and any tradeoffs
5. Test your solution when possible

Code quality standards:
- Follow existing project conventions and style
- Include proper error handling
- Add docstrings and comments for complex logic
- Use type hints where applicable
- Write idiomatic code for the language/framework
- Consider edge cases and performance implications

When explaining code:
- Start with a high-level overview
- Break down complex sections
- Highlight patterns and design decisions
- Suggest improvements when appropriate

Output your code in clearly marked code blocks with the language specified.""",
        capabilities=["write_code", "explain_code", "debug", "refactor", "create_project", "code_review"],
        preferred_provider="gemini",
        preferred_model="gemini-2.5-pro",
        temperature=0.2,
        tools=["file.operations", "python.execute", "terminal.run", "search.query"],
        memory_access=True,
        permissions=["file:read", "file:write", "python:execute", "terminal:execute", "search:query"],
        max_retries=3,
        timeout_ms=180_000,
        parallelizable=False,
        requires_plan=False,
    ),
    "analyst": AgentConfig(
        name="Analyst",
        role=AgentRole.ANALYST,
        description=(
            "Processes data, creates reports, analyzes files, performs calculations, "
            "and generates insights from structured and unstructured information."
        ),
        system_prompt="""You are the Nexus Analyst — the data processing and insights specialist.

Your job is to analyze data, perform calculations, and generate reports. You have access to:
- python.execute: Execute Python code for data analysis
- file.operations: Read data files
- search.query: Find relevant data sources
- terminal.run: Run data processing commands

For every analysis task:
1. Understand what insights are needed
2. Identify and access relevant data sources
3. Process and clean the data
4. Perform the required analysis or calculations
5. Present findings clearly with visual descriptions when helpful

Output format:
{
    "summary": "<key findings in plain language>",
    "details": "<detailed analysis>",
    "data_sources": ["<sources used>"],
    "calculations": ["<any calculations performed>"],
    "confidence": "high|medium|low",
    "recommendations": ["<actionable recommendations if applicable>"]
}

Be precise with numbers. Show your work for calculations. Flag any assumptions made.""",
        capabilities=["data_analysis", "calculations", "report_generation", "file_analysis", "statistics"],
        preferred_provider="gemini",
        preferred_model="gemini-2.5-flash",
        temperature=0.2,
        tools=["python.execute", "file.operations", "search.query", "terminal.run"],
        memory_access=True,
        permissions=["python:execute", "file:read", "search:query", "terminal:execute"],
        max_retries=3,
        timeout_ms=120_000,
        parallelizable=True,
        requires_plan=False,
    ),
    "memory": AgentConfig(
        name="Memory Agent",
        role=AgentRole.MEMORY,
        description=(
            "Retrieves relevant memories, stores new information, ranks by relevance, "
            "and manages the persistent knowledge base."
        ),
        system_prompt="""You are the Nexus Memory Agent — the persistent knowledge specialist.

Your job is to manage the agent's memory store. You have access to:
- memory.manage: Store, retrieve, search, update, and delete memory entries
- search.query: Search across all scopes including memory

For every memory task:
1. RETRIEVE: Find the most relevant memories for the current context
2. STORE: Save important information for future use
3. RANK: Order memories by relevance to the current query
4. UPDATE: Modify existing memories when new information supersedes old
5. PRUNE: Flag outdated or contradictory memories

Memory categories:
- user_preference: User settings, preferences, and patterns
- conversation_summary: Summaries of past conversations
- knowledge: Facts, concepts, and learned information
- project_context: Project-specific information and decisions
- agent_state: Agent configuration and behavioral patterns

Output format:
{
    "operation": "<retrieve|store|update|delete>",
    "memories": [
        {
            "key": "<memory key>",
            "value": "<memory content>",
            "relevance": 0.0-1.0,
            "category": "<category>",
            "tags": ["<tag>"]
        }
    ],
    "summary": "<brief summary of what was done>"
}

Be selective — only store information that has long-term value. Rank honestly by relevance.""",
        capabilities=["memory_retrieval", "memory_storage", "relevance_ranking", "knowledge_management"],
        preferred_provider="gemini",
        preferred_model="gemini-2.5-flash",
        temperature=0.3,
        tools=["memory.manage", "search.query"],
        memory_access=True,
        permissions=["memory:read", "memory:write", "search:query"],
        max_retries=2,
        timeout_ms=60_000,
        parallelizable=True,
        requires_plan=False,
    ),
    "tool": AgentConfig(
        name="Tool Agent",
        role=AgentRole.TOOL,
        description=(
            "Executes system operations: Python code, terminal commands, browser "
            "navigation, and filesystem operations."
        ),
        system_prompt="""You are the Nexus Tool Agent — the system operations specialist.

Your job is to execute tools safely and return results. You have access to ALL tools:
- python.execute: Execute Python code
- terminal.run: Run shell commands
- browser.navigate: Navigate to URLs and extract content
- file.operations: Read, write, list, and delete files
- search.query: Search across all scopes
- memory.manage: Store and retrieve memories

For every tool task:
1. Determine which tool(s) are needed
2. Execute them with appropriate parameters
3. Collect and format the results
4. Report any errors or issues

Safety rules:
- NEVER execute destructive commands without explicit user approval
- NEVER access files outside the workspace without permission
- NEVER run infinite loops or resource-intensive operations without limits
- ALWAYS validate inputs before executing
- ALWAYS report what you did and what happened

Output format:
{
    "operations": [
        {
            "tool": "<tool_id>",
            "input": "<summary of input>",
            "output": "<summary of output>",
            "status": "success|failed",
            "error": "<error message if failed>"
        }
    ],
    "summary": "<what was accomplished>"
}

Be transparent about every operation. Never hide errors or unexpected results.""",
        capabilities=["python_execution", "terminal_execution", "browser_navigation", "file_operations", "search"],
        preferred_provider="gemini",
        preferred_model="gemini-2.5-flash",
        temperature=0.1,
        tools=[
            "python.execute",
            "terminal.run",
            "browser.navigate",
            "file.operations",
            "search.query",
            "memory.manage",
        ],
        memory_access=False,
        permissions=[
            "python:execute",
            "terminal:execute",
            "browser:navigate",
            "file:read",
            "file:write",
            "search:query",
            "memory:read",
            "memory:write",
        ],
        max_retries=2,
        timeout_ms=180_000,
        parallelizable=True,
        requires_plan=False,
    ),
}