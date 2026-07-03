import { create } from 'zustand'
import type { Provider } from '../types/provider'
import { showError, showSuccess, showInfo, showWarning } from '../utils/toast'

interface ProviderState {
    providers: Provider[]
    selectedProviderId: number | null
    isLoading: boolean
    error: string | null
    selectProvider: (id: number | null) => void
    discoverModels: (id: number) => Promise<void>
    testProvider: (id: number) => Promise<{ status: string; message: string }>
}

export const useProviderStore = create<ProviderState>((set) => ({
    providers: [],
    selectedProviderId: null,
    isLoading: false,
    error: null,

    selectProvider: (id) => {
        set({ selectedProviderId: id })
    },

    discoverModels: async (id) => {
        set({ isLoading: true, error: null })
        showInfo('Discovering models...', { description: 'Fetching available models from provider' })
        try {
            const { providersApi } = await import('../api/providers')
            await providersApi.discoverModels(id)
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
            const { providersApi } = await import('../api/providers')
            const result = await providersApi.test(id)
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
