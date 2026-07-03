import { Agent } from '../../types/agent'
import { useProviderStore } from '../../stores/providerStore'

interface AgentDetailsDrawerProps {
  agent: Agent
  onClose: () => void
}

export function AgentDetailsDrawer({ agent, onClose }: AgentDetailsDrawerProps) {
  const providers = useProviderStore(state => state.providers)
  const provider = providers.find(p => p.id === agent.provider_id)

  const getAgentModelName = (): string | null => {
    if (!agent.preferred_model_id) return null
    for (const p of providers) {
      const model = p.models.find(m => m.id === agent.preferred_model_id)
      if (model) return model.display_name || model.name
    }
    return null
  }

  return (
    <div className="fixed inset-y-0 right-0 z-40 flex">
      <div className="fixed inset-0 bg-black/30" onClick={onClose} />
      <div className="relative w-96 bg-white dark:bg-gray-800 shadow-2xl flex flex-col h-full border-l border-gray-200 dark:border-gray-700 animate-slide-in-right">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className={`text-${agent.color || 'blue'}-600 bg-${agent.color || 'blue'}-100 p-2 rounded-full`}>
              <i className={`icon-${agent.icon || 'bot'} text-xl`} />
            </div>
            <h2 className="text-xl font-bold">{agent.name}</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          <section>
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">General</h3>
            <p className="text-gray-700 dark:text-gray-300 text-sm mb-2">{agent.description || 'No description provided.'}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className={`px-2 py-1 text-xs rounded-full font-medium ${agent.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                {agent.enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </section>

          <section>
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">AI Configuration</h3>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 space-y-2 text-sm">
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-2">
                <span className="text-gray-500">Provider</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{provider?.name || 'Default'}</span>
              </div>
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-2 pt-2">
                <span className="text-gray-500">Model</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{getAgentModelName() || 'Default'}</span>
              </div>
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-2 pt-2">
                <span className="text-gray-500">Temperature</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{agent.temperature}</span>
              </div>
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-2 pt-2">
                <span className="text-gray-500">Top P</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{agent.top_p}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-gray-500">Max Tokens</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{agent.max_tokens || 'Auto'}</span>
              </div>
            </div>
          </section>

          <section>
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">Prompt</h3>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 text-sm text-gray-700 dark:text-gray-300 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
              {agent.prompt_template || 'No system prompt defined.'}
            </div>
          </section>
          
          <section>
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3">Capabilities & Features</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700 dark:text-gray-300">Streaming</span>
                <span className={`px-2 py-0.5 text-xs rounded-md ${agent.streaming ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'}`}>{agent.streaming ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700 dark:text-gray-300">Memory</span>
                <span className={`px-2 py-0.5 text-xs rounded-md ${agent.memory_enabled ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'}`}>{agent.memory_enabled ? 'Yes' : 'No'}</span>
              </div>
              {agent.capabilities && (
                <div className="mt-2">
                  <span className="text-xs text-gray-500 block mb-1">Tags</span>
                  <div className="flex flex-wrap gap-1">
                    {agent.capabilities.split(',').map(cap => (
                      <span key={cap} className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded-full">{cap.trim()}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
