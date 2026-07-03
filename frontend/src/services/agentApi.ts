import { apiClient as api } from '../api/client';
import { Agent, AgentCreate, AgentUpdate, AgentTestResponse, AgentTestStreamRequest } from '../types/agent';

export const agentApi = {
  getAgents: async (): Promise<Agent[]> => {
    const response = await api.get('/agents');
    return response.data;
  },

  getAgent: async (id: number): Promise<Agent> => {
    const response = await api.get(`/agents/${id}`);
    return response.data;
  },

  createAgent: async (data: AgentCreate): Promise<Agent> => {
    const response = await api.post('/agents', data);
    return response.data;
  },

  updateAgent: async (id: number, data: AgentUpdate): Promise<Agent> => {
    const response = await api.patch(`/agents/${id}`, data);
    return response.data;
  },

  deleteAgent: async (id: number): Promise<void> => {
    await api.delete(`/agents/${id}`);
  },

  cloneAgent: async (id: number, name?: string): Promise<Agent> => {
    const response = await api.post(`/agents/${id}/clone`, { name });
    return response.data;
  },

  setDefaultAgent: async (id: number): Promise<Agent> => {
    const response = await api.patch(`/agents/${id}/default`);
    return response.data;
  },

  testAgent: async (id: number, message: string = "Hello, this is a test."): Promise<AgentTestResponse> => {
    const response = await api.post(`/agents/${id}/test`, { message });
    return response.data;
  },

  testAgentStream: async function* (
    id: number,
    data: AgentTestStreamRequest
  ): AsyncGenerator<string, void, unknown> {
    const response = await fetch(`${api.defaults.baseURL}/agents/${id}/test-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(api.defaults.headers?.common as Record<string, string>),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Stream test failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') return;
            yield data;
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
};
