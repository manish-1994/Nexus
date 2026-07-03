export interface Agent {
  id: number;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  category?: string;
  provider_id?: number;
  preferred_model_id?: number | null;
  temperature: number;
  top_p: number;
  max_tokens?: number;
  context_window?: number;
  streaming: boolean;
  enabled: boolean;
  prompt_template?: string;
  capabilities?: string;
  tools?: string;
  default_tools?: string;
  memory_enabled: boolean;
  presence_penalty: number;
  frequency_penalty: number;
  is_default: boolean;
  created_at?: string;
  updated_at?: string;
}

export type AgentCreate = Omit<Agent, 'id' | 'created_at' | 'updated_at' | 'is_default'>;
export type AgentUpdate = Partial<AgentCreate>;

export interface AgentTestResponse {
  status: string;
  response?: string;
  latency_ms?: number;
  provider_id?: number;
  model?: string;
  tokens_used?: number | null;
  error?: string;
}

export interface AgentTestStreamRequest {
  message: string;
  provider_id?: number;
  model?: string;
}

export interface AgentCloneRequest {
  name?: string;
}
