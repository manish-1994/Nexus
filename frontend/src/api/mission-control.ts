/** Mission Control API — fetches real-time Agent OS state for the Dashboard. */

import { apiClient } from './client';
import type {
  MissionControlSummary,
  ExecutionsResponse,
  EventsResponse,
  AgentsResponse,
  OrchestratorHealthResponse,
  ActiveExecution,
  AgentConfig,
} from '../types/mission-control';

export const missionControlApi = {
  /** Single endpoint returning all Dashboard data. */
  getSummary: async (): Promise<MissionControlSummary> => {
    const response = await apiClient.get('/mission-control/summary');
    return response.data;
  },

  /** Get all executions (active only by default). */
  getExecutions: async (activeOnly = true): Promise<ExecutionsResponse> => {
    const response = await apiClient.get('/mission-control/executions', {
      params: { active_only: activeOnly },
    });
    return response.data;
  },

  /** Get a specific execution by ID. */
  getExecution: async (executionId: string): Promise<ActiveExecution> => {
    const response = await apiClient.get(`/mission-control/executions/${executionId}`);
    return response.data;
  },

  /** Get the active execution for a conversation. */
  getExecutionByConversation: async (conversationId: number): Promise<ActiveExecution> => {
    const response = await apiClient.get(
      `/mission-control/executions/by-conversation/${conversationId}`
    );
    return response.data;
  },

  /** Get recent events from the Event Bus. */
  getEvents: async (params?: {
    event_type?: string;
    execution_id?: string;
    limit?: number;
  }): Promise<EventsResponse> => {
    const response = await apiClient.get('/mission-control/events', { params });
    return response.data;
  },

  /** Get all registered agents (built-in + custom). */
  getAgents: async (): Promise<AgentsResponse> => {
    const response = await apiClient.get('/mission-control/agents');
    return response.data;
  },

  /** Get a specific agent by role. */
  getAgentByRole: async (role: string): Promise<{ agent: AgentConfig; source: string }> => {
    const response = await apiClient.get(`/mission-control/agents/${role}`);
    return response.data;
  },

  /** Get orchestrator health status. */
  getHealth: async (): Promise<OrchestratorHealthResponse> => {
    const response = await apiClient.get('/mission-control/health');
    return response.data;
  },
};