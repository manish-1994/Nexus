export interface Provider {
  id: number;
  name: string;
  type: string;
  api_key: string;
  base_url: string | null;
  is_active: boolean;
  health_status: string;
  last_checked: string | null;
  error_message: string | null;
  default_model?: string;
  timeout: number;
  priority: number;
  max_retries: number;
  organization_id?: string;
  capabilities?: Record<string, boolean>;
  created_at: string;
  updated_at: string;
  models: Model[];
}

export interface Model {
  id: number;
  provider_id: number;
  name: string;
  display_name: string | null;
  max_tokens: number | null;
  supports_streaming: boolean;
  is_active: boolean;
  description: string | null;
}

export type ProviderType = 'openrouter' | 'groq' | 'ollama' | 'gemini' | 'lmstudio' | 'openai_compatible';
