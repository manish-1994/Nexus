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
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-96 glass-elevated shadow-elevated flex flex-col h-full border-l border-white/10 animate-slide-in-right rounded-dialog">
        <div className="flex items-center justify-between p-lg border-b border-white/5">
          <div className="flex items-center gap-md">
            <div className="bg-accent/15 p-sm rounded-button">
              <span className="text-accent-light text-xl">{agent.icon === 'bot' ? '🤖' : agent.icon === 'code' ? '💻' : agent.icon === 'brain' ? '🧠' : '🤖'}</span>
            </div>
            <h2 className="text-xl font-bold text-text font-heading">{agent.name}</h2>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none rounded-button p-xs">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-lg space-y-lg">
          <section>
            <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-sm">General</h3>
            <p className="text-text text-sm mb-sm">{agent.description || 'No description provided.'}</p>
            <div className="flex items-center gap-sm mt-sm">
              <span className={agent.enabled ? 'badge-success' : 'badge-neutral'}>
                {agent.enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </section>

          <section>
            <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-sm">AI Configuration</h3>
            <div className="bg-surface/40 rounded-input p-md space-y-sm text-sm">
              <div className="flex justify-between border-b border-white/5 pb-sm">
                <span className="text-text-muted">Provider</span>
                <span className="font-medium text-text">{provider?.name || 'Default'}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-sm pt-sm">
                <span className="text-text-muted">Model</span>
                <span className="font-medium text-text">{getAgentModelName() || 'Default'}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-sm pt-sm">
                <span className="text-text-muted">Temperature</span>
                <span className="font-medium text-text">{agent.temperature}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-sm pt-sm">
                <span className="text-text-muted">Top P</span>
                <span className="font-medium text-text">{agent.top_p}</span>
              </div>
              <div className="flex justify-between pt-sm">
                <span className="text-text-muted">Max Tokens</span>
                <span className="font-medium text-text">{agent.max_tokens || 'Auto'}</span>
              </div>
            </div>
          </section>

          <section>
            <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-sm">Prompt</h3>
            <div className="bg-surface/40 rounded-input p-md text-sm text-text font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
              {agent.prompt_template || 'No system prompt defined.'}
            </div>
          </section>
          
          <section>
            <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-sm">Capabilities & Features</h3>
            <div className="space-y-sm">
              <div className="flex items-center justify-between">
                <span className="text-sm text-text">Streaming</span>
                <span className={agent.streaming ? 'badge-accent' : 'badge-neutral'}>{agent.streaming ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-text">Memory</span>
                <span className={agent.memory_enabled ? 'badge-accent' : 'badge-neutral'}>{agent.memory_enabled ? 'Yes' : 'No'}</span>
              </div>
              {agent.capabilities && (
                <div className="mt-sm">
                  <span className="text-xs text-text-muted block mb-xs">Tags</span>
                  <div className="flex flex-wrap gap-xs">
                    {agent.capabilities.split(',').map(cap => (
                      <span key={cap} className="px-xs py-xs text-xs bg-white/5 rounded-button text-text-muted">{cap.trim()}</span>
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
