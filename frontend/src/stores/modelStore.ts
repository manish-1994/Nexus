import { create } from 'zustand'
import { providersApi } from '../api/providers'
import type { Model } from '../types/provider'

interface ModelState {
  models: Model[]
  selectedModel: Model | null
  isLoading: boolean
  error: string | null
  fetchModelsForProvider: (providerId: number) => Promise<void>
  selectModel: (model: Model | null) => void
}

export const useModelStore = create<ModelState>((set) => ({
  models: [],
  selectedModel: null,
  isLoading: false,
  error: null,

  fetchModelsForProvider: async (providerId) => {
    set({ isLoading: true, error: null })
    try {
      const data = await providersApi.listModels(providerId)
      set({ models: data, isLoading: false })
    } catch {
      set({ error: 'Failed to load models', isLoading: false })
    }
  },

  selectModel: (model) => {
    set({ selectedModel: model })
  },
}))
