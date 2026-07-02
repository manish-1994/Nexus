import { useState, useEffect, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { providersApi } from '../../api/providers'
import { useProviderStore } from '../../stores/providerStore'
import { useModelStore } from '../../stores/modelStore'
import { toast } from 'sonner'

function ProviderModelSelector() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { providers, selectedProviderId, selectProvider } = useProviderStore()
  const { models, selectedModel, selectModel, fetchModelsForProvider } = useModelStore()

  const { data: providersData, isLoading: providersLoading } = useQuery({
    queryKey: ['providers'],
    queryFn: providersApi.list,
  })

  const { data: modelsData, isLoading: modelsLoading } = useQuery({
    queryKey: ['models', selectedProviderId],
    queryFn: () => providersApi.listModels(selectedProviderId!),
    enabled: !!selectedProviderId,
  })

  useEffect(() => {
    if (providersData) {
      useProviderStore.setState({ providers: providersData })
      if (providersData.length > 0 && !selectedProviderId) {
        selectProvider(providersData[0].id)
      }
    }
  }, [providersData, selectProvider, selectedProviderId])

  useEffect(() => {
    if (modelsData) {
      useModelStore.setState({ models: modelsData })
      if (modelsData.length > 0 && !selectedModel) {
        selectModel(modelsData[0])
      }
    }
  }, [modelsData, selectModel, selectedModel])

  const handleProviderChange = useCallback(async (providerId: number) => {
    selectProvider(providerId)
    useModelStore.setState({ models: [], selectedModel: null })
    await fetchModelsForProvider(providerId)
  }, [selectProvider, fetchModelsForProvider])

  const handleDiscoverModels = async () => {
    if (!selectedProviderId) return
    try {
      await useProviderStore.getState().discoverModels(selectedProviderId)
      await queryClient.invalidateQueries({ queryKey: ['providers'] })
      await queryClient.invalidateQueries({ queryKey: ['models', selectedProviderId] })
      const freshModels = await providersApi.listModels(selectedProviderId)
      useModelStore.setState({ models: freshModels })
      if (freshModels.length > 0) {
        useModelStore.getState().selectModel(freshModels[0])
        toast.success(`Synced ${freshModels.length} models`)
      } else {
        toast.info('No models found for this provider')
      }
    } catch {
      toast.error('Failed to discover models')
    }
  }

  const selectedProvider = providers.find(p => p.id === selectedProviderId)
  const filteredModels = models.filter(model =>
    model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (model.display_name && model.display_name.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const canSend = !!selectedProviderId && !!selectedModel

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Provider & Model</h3>
        <button
          onClick={handleDiscoverModels}
          disabled={!selectedProviderId || providersLoading}
          className="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {providersLoading ? 'Syncing...' : 'Sync Models'}
        </button>
      </div>

      {/* Provider Selector */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Provider</label>
        <select
          value={selectedProviderId || ''}
          onChange={(e) => handleProviderChange(Number(e.target.value))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {providers.map((provider) => (
            <option key={provider.id} value={provider.id}>
              {provider.name} ({provider.type})
            </option>
          ))}
        </select>
        {selectedProvider && (
          <div className="mt-1 flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${
              selectedProvider.health_status === 'active' ? 'bg-green-500' :
              selectedProvider.health_status === 'error' ? 'bg-red-500' :
              selectedProvider.health_status === 'checking' ? 'bg-yellow-500' :
              'bg-gray-500'
            }`} />
            <span className="text-xs text-gray-500 capitalize">{selectedProvider.health_status}</span>
            <span className="text-xs text-gray-400">• {models.length} models</span>
          </div>
        )}
      </div>

      {/* Model Selector */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Model</label>
        {modelsLoading ? (
          <div className="space-y-2">
            <div className="h-9 bg-gray-100 rounded-lg animate-pulse" />
            <div className="h-4 w-24 bg-gray-100 rounded animate-pulse" />
          </div>
        ) : filteredModels.length === 0 ? (
          <div className="text-sm text-gray-500 py-2">
            {selectedProviderId ? 'No models found. Click "Sync Models" to discover.' : 'Select a provider first.'}
          </div>
        ) : (
          <div className="relative">
            <input
              type="text"
              placeholder="Search models..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setIsOpen(true)}
              onBlur={() => setTimeout(() => setIsOpen(false), 150)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {isOpen && searchQuery && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                {filteredModels.map((model) => (
                  <div
                    key={model.id}
                    onClick={() => {
                      selectModel(model)
                      setIsOpen(false)
                      setSearchQuery('')
                    }}
                    className={`px-3 py-2 cursor-pointer hover:bg-blue-50 ${
                      selectedModel?.id === model.id ? 'bg-blue-100' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">{model.display_name || model.name}</div>
                        <div className="text-xs text-gray-500">{model.name}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        {model.supports_streaming !== false && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                            Streaming
                          </span>
                        )}
                        {model.max_tokens && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-50 text-gray-600 border border-gray-200">
                            {model.max_tokens}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {selectedModel && !modelsLoading && (
          <div className="mt-1 flex items-center gap-2 text-xs text-gray-600">
            <span className="font-medium">{selectedModel.display_name || selectedModel.name}</span>
            {selectedModel.supports_streaming !== false && (
              <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                Streaming
              </span>
            )}
            {selectedModel.max_tokens && (
              <span className="px-1.5 py-0.5 rounded bg-gray-50 text-gray-600 border border-gray-200">
                {selectedModel.max_tokens} ctx
              </span>
            )}
          </div>
        )}
      </div>

      {/* Hidden prop for parent to check send readiness */}
      <input type="hidden" data-can-send={canSend ? '1' : '0'} />
    </div>
  )
}

export default ProviderModelSelector
