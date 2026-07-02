export interface CapabilityResponse {
  provider_id: number;
  capabilities: Record<string, boolean>;
  detected_at: string;
  models_count: number;
}

export interface UsageStats {
  provider_id: number;
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  recent_usage: Array<{
    id: number;
    model: string;
    input_tokens?: number;
    output_tokens?: number;
    total_tokens?: number;
    cost?: number;
    request_type: string;
    created_at: string;
  }>;
}

export const aiRuntimeApi = {
  chat: async (data: {
    provider_id?: number;
    model?: string;
    messages: Array<{ role: string; content: string }>;
    stream?: boolean;
  }) => {
    const response = await fetch('/api/v1/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('AI request failed');
    return response.json();
  },

  stream: async (data: {
    provider_id?: number;
    model?: string;
    messages: Array<{ role: string; content: string }>;
    stream?: boolean;
  }) => {
    const response = await fetch('/api/v1/ai/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('AI stream failed');
    return response.body;
  },

  getCapabilities: async (providerId: number): Promise<CapabilityResponse> => {
    const response = await fetch(`/api/v1/ai/providers/${providerId}/capabilities`);
    if (!response.ok) throw new Error('Failed to fetch capabilities');
    return response.json();
  },

  getUsage: async (providerId: number): Promise<UsageStats> => {
    const response = await fetch(`/api/v1/providers/${providerId}/usage`);
    if (!response.ok) throw new Error('Failed to fetch usage');
    return response.json();
  },

  refreshModels: async (providerId: number) => {
    const response = await fetch(`/api/v1/providers/${providerId}/refresh-models`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to refresh models');
    return response.json();
  },
};
