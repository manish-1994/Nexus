import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useProviderStore } from '../../stores/providerStore'
import { useModelStore } from '../../stores/modelStore'
import { Model } from '../../types/provider'

export function useModelSelection() {
  const queryClient = useQueryClient()
  const selectedProviderId = useProviderStore((state) => state.selectedProviderId)
  const selectedModelId = useModelStore((state) => state.selectedModelId)

  const selectedModel = useQuery<Model | null>({
    queryKey: ['model', selectedProviderId, selectedModelId],
    queryFn: async () => {
      if (!selectedProviderId || !selectedModelId) return null
      const providers = queryClient.getQueryData<{ id: number; models: Model[] }[]>(['providers']) || []
      const provider = providers.find(p => p.id === selectedProviderId)
      return provider?.models.find(m => m.id === selectedModelId) || null
    },
    enabled: !!selectedProviderId && !!selectedModelId,
  }).data || null

  const modelName = selectedModel?.name || selectedModel?.display_name || null

  return {
    selectedProviderId,
    selectedModelId,
    selectedModel,
    modelName,
  }
}
