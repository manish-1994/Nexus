import { apiClient } from './client'
import { ProviderType } from '../types/provider'

export interface Model {
  id: number
  provider_id: number
  name: string
  display_name: string | null
  max_tokens: number | null
  supports_streaming: boolean
  supports_vision: boolean
  supports_reasoning: boolean
  is_deprecated: boolean
  is_active: boolean
  description: string | null
}

export interface Provider {
  id: number
  name: string
  type: ProviderType
  api_key: string
  base_url: string | null
  is_active: boolean
  health_status: string
  last_checked: string | null
  error_message: string | null
  default_model?: string
  timeout: number
  priority: number
  max_retries: number
  organization_id?: string
  capabilities?: Record<string, boolean>
  created_at: string
  updated_at: string
  models: Model[]
}

export const providersApi = {
  list: async (): Promise<Provider[]> => {
    const response = await apiClient.get('/providers')
    return response.data
  },
  get: async (id: number): Promise<Provider> => {
    const response = await apiClient.get(`/providers/${id}`)
    return response.data
  },
  create: async (data: Partial<Provider>): Promise<Provider> => {
    const response = await apiClient.post('/providers', data)
    return response.data
  },
  update: async (id: number, data: Partial<Provider>): Promise<Provider> => {
    const response = await apiClient.put(`/providers/${id}`, data)
    return response.data
  },
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/providers/${id}`)
  },
  test: async (id: number): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post(`/providers/${id}/test`)
    return response.data
  },
  discoverModels: async (id: number): Promise<Model[]> => {
    const response = await apiClient.post(`/providers/${id}/models`)
    return response.data
  },
  listModels: async (id: number): Promise<Model[]> => {
    const response = await apiClient.get(`/providers/${id}/models`)
    return response.data
  },
  getCapabilities: async (id: number): Promise<{ capabilities: Record<string, boolean> }> => {
    const response = await apiClient.get(`/ai/providers/${id}/capabilities`)
    return response.data
  },
  validate: async (data: { name: string; type: string; base_url?: string; api_key?: string }): Promise<{ valid: boolean; errors: string[] }> => {
    const response = await apiClient.post('/providers/validate', data)
    return response.data
  },
}
