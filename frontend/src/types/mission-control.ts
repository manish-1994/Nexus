/** Mission Control types — Dashboard visualization data structures. */

// ── Execution State (from backend ExecutionState enum) ──
export type ExecutionState =
  | 'idle'
  | 'thinking'
  | 'planning'
  | 'researching'
  | 'calling_provider'
  | 'streaming'
  | 'completed'
  | 'failed'
  | 'cancelled';

// ── Agent Status (for orb visualization) ──
export type AgentStatus =
  | 'idle'
  | 'thinking'
  | 'running'
  | 'streaming'
  | 'completed'
  | 'failed'
  | 'disabled';

// ── Active Execution ──
export interface ActiveExecution {
  execution_id: string;
  conversation_id: number | null;
  state: ExecutionState;
  current_agent: string | null;
  current_task_id: string | null;
  current_task: string | null;
  completed_tasks: string[];
  running_tasks: string[];
  pending_tasks: string[];
  failed_tasks: string[];
  provider_id: number | null;
  provider_name: string | null;
  provider_used: string | null;
  model: string | null;
  model_used: string | null;
  total_tokens: number;
  token_count: number;
  tokens_per_second: number;
  elapsed_ms: number;
  total_latency_ms: number;
  estimated_cost: number;
  retry_count: number;
  fallback_used: boolean;
  started_at: string | null;
  completed_at: string | null;
  events: ExecutionEvent[];
  error_message: string | null;
  task_details?: Array<{
    id: string;
    label: string;
    role: string;
    depends_on: string[];
  }>;
}

// ── Execution Event ──
export interface ExecutionEvent {
  id: string;
  type: string;
  execution_id: string | null;
  task_id: string | null;
  agent_role: string | null;
  timestamp: string;
  data: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

// ── Agent Config ──
export interface AgentConfig {
  name: string;
  role: string;
  description: string;
  capabilities: string[];
  system_prompt: string;
  preferred_provider: string | null;
  preferred_model: string | null;
  temperature: number;
  tools: string[];
  memory_access: boolean;
  parallelizable: boolean;
  requires_plan: boolean;
  permissions: string[];
}

// ── Agent Health ──
export interface AgentHealth {
  status: 'available' | 'registered' | 'unhealthy' | 'unknown';
  type: 'builtin' | 'custom';
  latency_ms?: number;
}

// ── Mission Control Summary (from /mission-control/summary) ──
export interface MissionControlSummary {
  timestamp: string;
  orchestrator: {
    status: string;
    active_executions: number;
    total_executions_tracked: number;
    event_bus_attached: boolean;
  };
  active_executions: ActiveExecution[];
  recent_events: ExecutionEvent[];
  agents: {
    builtin: Record<string, AgentConfig>;
    custom: Record<string, AgentConfig>;
    all: Record<string, AgentConfig>;
  };
  agent_health: Record<string, AgentHealth>;
}

// ── Executions Response ──
export interface ExecutionsResponse {
  executions: ActiveExecution[];
  active_count: number;
  total_count: number;
}

// ── Events Response ──
export interface EventsResponse {
  events: ExecutionEvent[];
  count: number;
  subscriber_count: number;
}

// ── Agents Response ──
export interface AgentsResponse {
  agents: Record<string, AgentConfig>;
  builtin_count: number;
  custom_count: number;
  total_count: number;
  builtin_roles: string[];
  custom_roles: string[];
}

// ── Orchestrator Health Response ──
export interface OrchestratorHealthResponse {
  status: string;
  active_executions: number;
  total_executions_tracked: number;
  event_bus_attached: boolean;
  event_bus_subscribers: number;
  builtin_agents: number;
  custom_agents: number;
  agent_health: Record<string, AgentHealth>;
}

// ── Agent Orb Position (for layout) ──
export interface AgentOrbPosition {
  role: string;
  label: string;
  angle: number;    // degrees from top (0 = 12 o'clock)
  radius: number;    // distance from center (0-1 normalized)
  ring: number;      // which orbital ring (0 = inner, 1 = outer)
}