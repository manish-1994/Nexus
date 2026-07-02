import { apiClient } from './client'

export interface HealthResponse {
  status: string
  version: string
  database: string
  environment: string
}

export const healthApi = {
  check: async (): Promise<HealthResponse> => {
    const response = await apiClient.get('/health/health')
    return response.data
  },
}
