import { create } from 'zustand'
import { providersApi } from '../api/providers'
import type { Provider } from '../types/provider'
import { showError, showSuccess, showInfo, showWarning } from '../utils/toast'

interface ProviderState {
  providers: Provider[]
  selectedProviderId: number | null
  isLoading: boolean
  error: string | null
  fetchProviders: () => Promise<void>
  selectProvider: (id: number | null) => void
  discoverModels: (id: number) => Promise<void>
  testProvider: (id: number) => Promise<{ status: string; message: string }>
}

export const useProviderStore = create<ProviderState>((set) => ({
  providers: [],
  selectedProviderId: null,
  isLoading: false,
  error: null,

  fetchProviders: async () => {
    set({ isLoading: true, error: null })
    try {
      const data = await providersApi.list()
      set({ providers: data, isLoading: false })
    } catch (err) {
      const message = 'Failed to load providers'
      showError(message, { description: err instanceof Error ? err.message : undefined })
      set({ error: message, isLoading: false })
    }
  },

  selectProvider: (id) => {
    set({ selectedProviderId: id })
  },

  discoverModels: async (id) => {
    set({ isLoading: true, error: null })
    showInfo('Discovering models...', { description: 'Fetching available models from provider' })
    try {
      await providersApi.discoverModels(id)
      const data = await providersApi.list()
      set({ providers: data, isLoading: false })
      showSuccess('Models discovered successfully')
    } catch (err) {
      const message = 'Failed to discover models'
      const description = err instanceof Error ? err.message : undefined
      showError(message, { description })
      set({ error: message, isLoading: false })
    }
  },

  testProvider: async (id) => {
    set({ isLoading: true, error: null })
    showInfo('Testing connection...', { description: 'Checking provider connectivity' })
    try {
      const result = await providersApi.test(id)
      const data = await providersApi.list()
      set({ providers: data, isLoading: false })
      if (result.status === 'success') {
        showSuccess(`Connection successful: ${result.message}`)
      } else {
        showWarning(`Connection test returned: ${result.message}`)
      }
      return result
    } catch (err) {
      const message = 'Connection test failed'
      const description = err instanceof Error ? err.message : undefined
      showError(message, { description })
      set({ error: message, isLoading: false })
      throw err
    }
  },
}))
