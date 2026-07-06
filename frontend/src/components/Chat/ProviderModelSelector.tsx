import { useEffect, useCallback, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { providersApi } from '../../api/providers'
import { agentApi } from '../../services/agentApi'
import { useProviderStore } from '../../stores/providerStore'
import { useModelStore } from '../../stores/modelStore'
import { useAgentStore } from '../../stores/agentStore'
import { toast } from 'sonner'
import { ProviderSelector } from './ProviderSelector'
import { ModelSelector } from './ModelSelector'
import { AgentSelector } from './AgentSelector'
import type { Provider } from '../../types/provider'

function ProviderModelSelector() {
    const queryClient = useQueryClient()
    const { providers, selectedProviderId, selectProvider } = useProviderStore()
    const { selectedModelId, selectModel } = useModelStore()
    const { selectedAgentId, selectAgent } = useAgentStore()

    const { data: providersData, isLoading: providersLoading } = useQuery({
        queryKey: ['providers'],
        queryFn: providersApi.list,
    })

    const { data: agentsData, isLoading: agentsLoading } = useQuery({
        queryKey: ['agents'],
        queryFn: agentApi.getAgents,
    })

    const agents = useMemo(() => agentsData || [], [agentsData])

    const modelsData = useMemo(() => {
        const match = providersData?.find(p => p.id === selectedProviderId)
        return match?.models || []
    }, [providersData, selectedProviderId])

    const selectedModel = useMemo(() => {
        if (!selectedProviderId || !selectedModelId) return null
        return modelsData.find(m => m.id === selectedModelId) || null
    }, [modelsData, selectedProviderId, selectedModelId])

    useEffect(() => {
        if (providersData) {
            const activeProviders = providersData.filter(p => p.is_active)
            useProviderStore.setState({ providers: activeProviders })
            
            // Auto-select first provider if none is selected and no agent is overriding
            if (activeProviders.length > 0 && !selectedProviderId && !selectedAgentId) {
                selectProvider(activeProviders[0].id)
            }
        }
    }, [providersData, selectedProviderId, selectedAgentId, selectProvider])

    const handleAgentChange = useCallback((agentId: number | null) => {
        const agent = agents.find(a => a.id === agentId)
        selectAgent(agentId)

        if (!agentId || !agent?.provider_id) {
            useProviderStore.setState({ selectedProviderId: null })
            useModelStore.setState({ selectedModelId: null })
            return
        }

        const provider = providersData?.find(p => p.id === agent.provider_id)
        if (!provider) {
            toast.error('Agent provider not found')
            return
        }

        selectProvider(agent.provider_id)

        const derivedModels = provider.models
        if (agent.preferred_model_id) {
            const foundModel = derivedModels.find(m => m.id === agent.preferred_model_id)
            if (foundModel) {
                selectModel(foundModel.id)
            } else {
                useModelStore.setState({ selectedModelId: null })
                toast.error("This agent's configured model is unavailable for the selected provider.")
            }
        } else if (derivedModels.length > 0) {
            selectModel(derivedModels[0].id)
        } else {
            useModelStore.setState({ selectedModelId: null })
        }
    }, [selectAgent, agents, selectProvider, providersData, selectModel])

    const handleProviderChange = useCallback((providerId: number) => {
        selectProvider(providerId)

        const freshData = queryClient.getQueryData<Provider[]>(['providers']) || providersData
        const match = freshData?.find(p => p.id === providerId)
        const derivedModels = match?.models || []

        // Reset model selection to avoid mismatch with new provider
        useModelStore.setState({ selectedModelId: null })

        if (derivedModels.length > 0) {
            selectModel(derivedModels[0].id)
        }
    }, [selectProvider, selectModel, queryClient, providersData])

    const handleDiscoverModels = async () => {
        if (!selectedProviderId) return
        try {
            await useProviderStore.getState().discoverModels(selectedProviderId)
            await queryClient.invalidateQueries({ queryKey: ['providers'] })
            const freshProviders = await providersApi.list()
            const freshModels = freshProviders.find(p => p.id === selectedProviderId)?.models || []
            if (freshModels.length > 0) {
                useModelStore.getState().selectModel(freshModels[0].id)
                toast.success(`Synced ${freshModels.length} models`)
            } else {
                useModelStore.setState({ selectedModelId: null })
                toast.info('No models found for this provider')
            }
        } catch {
            toast.error('Failed to discover models')
        }
    }

    const handleModelChange = useCallback((modelId: number) => {
      selectModel(modelId)
    }, [selectModel])

    const selectedAgent = agents.find(a => a.id === selectedAgentId)

    const isProviderOverridden = selectedAgent && selectedAgent.provider_id !== undefined && selectedProviderId !== selectedAgent.provider_id
    const isModelOverridden = selectedAgent && selectedAgent.preferred_model_id !== undefined && selectedModelId !== selectedAgent.preferred_model_id

    const canSend = !!selectedProviderId && !!selectedModel
    return (
        <div className="glass-surface rounded-panel p-lg space-y-md">
            <AgentSelector
                agents={agents}
                selectedAgentId={selectedAgentId}
                onAgentChange={handleAgentChange}
                isLoading={agentsLoading}
            />

            <div className="pt-2 border-t border-white/5 flex flex-col space-y-4">
                <div className="relative">
                    {isProviderOverridden && (
                        <span className="absolute -top-2 right-0 badge-warning text-[10px] z-10">
                            Overridden
                        </span>
                    )}
                    <ProviderSelector
                        providers={providers}
                        selectedProviderId={selectedProviderId}
                        onProviderChange={handleProviderChange}
                        onDiscoverModels={handleDiscoverModels}
                        isLoading={providersLoading}
                    />
                </div>

                <div className="relative">
                    {isModelOverridden && (
                        <span className="absolute -top-2 right-0 badge-warning text-[10px] z-10">
                            Overridden
                        </span>
                    )}
                    <ModelSelector
                      models={modelsData}
                      selectedModelId={selectedModelId}
                      onModelSelect={handleModelChange}
                      isLoading={providersLoading}
                    />
                </div>
            </div>
            <input type="hidden" data-can-send={canSend ? '1' : '0'} />
        </div>
    )
}

export default ProviderModelSelector
