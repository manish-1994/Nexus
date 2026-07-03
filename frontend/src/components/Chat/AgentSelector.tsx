import { useState, useRef, useEffect } from 'react'
import type { Agent } from '../../types/agent'
import { useProviderStore } from '../../stores/providerStore'

interface AgentSelectorProps {
  agents: Agent[]
  selectedAgentId: number | null
  onAgentChange: (agentId: number | null) => void
  isLoading?: boolean
}

export function AgentSelector({ agents, selectedAgentId, onAgentChange, isLoading }: AgentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const providers = useProviderStore(state => state.providers)

  const selectedAgent = agents.find(a => a.id === selectedAgentId)

  const getAgentModelName = (agent: Agent): string | null => {
    if (!agent.preferred_model_id) return null
    for (const provider of providers) {
      const model = provider.models.find(m => m.id === agent.preferred_model_id)
      if (model) return model.display_name || model.name
    }
    return null
  }

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="flex flex-col gap-1.5" ref={dropdownRef}>
      <label className="block text-[10px] font-bold text-text-muted uppercase tracking-widest mb-1.5 font-label">
        Agent Node
      </label>
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          disabled={isLoading || agents.length === 0}
          className="w-full bg-elevated/40 text-text border border-white/10 rounded-xl py-2.5 px-4 text-xs font-heading tracking-wider focus:outline-none focus:ring-1 focus:ring-accent/30 focus:border-accent-light/50 text-left flex justify-between items-center transition-all disabled:opacity-50 cursor-pointer"
        >
          <div className="flex items-center gap-2 truncate">
            {selectedAgent ? (
              <>
                <span className="flex-shrink-0 w-6 h-6 rounded-lg bg-accent/15 border border-accent/30 text-accent flex items-center justify-center">
                  <i className={`icon-${selectedAgent.icon || 'bot'} text-xs`} />
                </span>
                <span className="font-bold uppercase tracking-wider text-[11px]">{selectedAgent.name}</span>
                {selectedAgent.provider_id && (
                  <span className="ml-2 px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-widest bg-white/5 text-text-muted border border-white/10">
                    {providers.find(p => p.id === selectedAgent.provider_id)?.name || 'Provider'}
                  </span>
                )}
                {getAgentModelName(selectedAgent) && (
                  <span className="ml-1 px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-widest bg-accent/10 text-accent-light border border-accent/20">
                    {getAgentModelName(selectedAgent)}
                  </span>
                )}
              </>
            ) : (
              <span className="text-text-muted/60 font-bold uppercase tracking-wider text-[10px]">Assistant</span>
            )}
          </div>
          <span className="text-text-muted">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </span>
        </button>

        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-surface border border-white/10 rounded-xl shadow-glass py-1 text-xs max-h-60 overflow-auto p-1">
            <button
              type="button"
              className={`w-full text-left px-3 py-2 rounded-lg hover:bg-accent/15 hover:text-accent-light text-text transition-all ${!selectedAgentId ? 'bg-accent/25 text-accent-light font-bold' : ''}`}
              onClick={() => {
                onAgentChange(null)
                setIsOpen(false)
              }}
            >
              <div className="font-bold uppercase tracking-wider text-[10px]">Assistant</div>
              <div className="text-[9px] text-text-muted tracking-wide mt-0.5">Default generic chat interface</div>
            </button>
            {agents.map((agent) => (
              <button
                key={agent.id}
                type="button"
                className={`w-full text-left px-3 py-2 rounded-lg hover:bg-accent/15 hover:text-accent-light flex flex-col gap-1 text-text transition-all ${selectedAgentId === agent.id ? 'bg-accent/25 text-accent-light font-bold' : ''}`}
                onClick={() => {
                  onAgentChange(agent.id)
                  setIsOpen(false)
                }}
                title={agent.description}
              >
                <div className="flex justify-between items-center w-full">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg bg-accent/15 border border-accent/30 text-accent flex items-center justify-center">
                      <i className={`icon-${agent.icon || 'bot'} text-xs`} />
                    </span>
                    <span className="font-bold uppercase tracking-wider text-[10px]">{agent.name}</span>
                  </div>
                  <div className="flex gap-1.5">
                    {agent.provider_id && (
                      <span className="px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-widest bg-white/5 text-text-muted border border-white/10">
                        {providers.find(p => p.id === agent.provider_id)?.name || 'Provider'}
                      </span>
                    )}
                    {getAgentModelName(agent) && (
                      <span className="px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-widest bg-accent/10 text-accent-light border border-accent/20">
                        {getAgentModelName(agent)}
                      </span>
                    )}
                  </div>
                </div>
                {agent.description && (
                  <div className="text-[9px] text-text-muted/70 pl-8 truncate w-full tracking-wide">
                    {agent.description}
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
