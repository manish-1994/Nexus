import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import type { Agent } from '../../types/agent'
import { useProviderStore } from '../../stores/providerStore'
import { springs } from '../common/Motion'

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
    <div className="flex flex-col gap-sm" ref={dropdownRef}>
      <label className="block text-[10px] font-bold text-text-muted uppercase tracking-widest mb-xs font-label">
        Agent Node
      </label>
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          disabled={isLoading || agents.length === 0}
          className="w-full bg-surface/40 text-text border border-white/10 rounded-button py-sm px-md text-xs font-heading tracking-wider focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent/50 text-left flex justify-between items-center transition-all disabled:opacity-50 cursor-pointer"
        >
          <div className="flex items-center gap-sm truncate">
            {selectedAgent ? (
              <>
                <span className="flex-shrink-0 w-6 h-6 rounded-button bg-accent/15 border border-accent/30 text-accent flex items-center justify-center">
                  <i className={`icon-${selectedAgent.icon || 'bot'} text-xs`} />
                </span>
                <span className="font-bold uppercase tracking-wider text-[11px]">{selectedAgent.name}</span>
                {selectedAgent.provider_id && (
                  <span className="ml-sm px-xs py-xs rounded-button text-[8px] font-bold uppercase tracking-widest bg-white/5 text-text-muted/10 text-text-muted border border-white/10">
                    {providers.find(p => p.id === selectedAgent.provider_id)?.name || 'Provider'}
                  </span>
                )}
                {getAgentModelName(selectedAgent) && (
                  <span className="ml-xs px-xs py-xs rounded-button text-[8px] font-bold uppercase tracking-widest bg-accent/10 text-accent-light border border-accent/20">
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
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={springs.smooth}
            className="absolute z-50 w-full mt-xs glass-elevated rounded-panel shadow-glow py-xs text-xs max-h-60 overflow-auto p-xs"
          >
            <button
              type="button"
              className={`w-full text-left px-sm py-sm rounded-button hover:bg-accent/15 hover:text-accent-light text-text transition-all ${!selectedAgentId ? 'bg-accent/25 text-accent-light font-bold' : ''}`}
              onClick={() => {
                onAgentChange(null)
                setIsOpen(false)
              }}
            >
              <div className="font-bold uppercase tracking-wider text-[10px]">Assistant</div>
              <div className="text-[9px] text-text-muted tracking-wide mt-xs">Default generic chat interface</div>
            </button>
            {agents.map((agent) => (
              <button
                key={agent.id}
                type="button"
                className={`w-full text-left px-sm py-sm rounded-button hover:bg-accent/15 hover:text-accent-light flex flex-col gap-xs text-text transition-all ${selectedAgentId === agent.id ? 'bg-accent/25 text-accent-light font-bold' : ''}`}
                onClick={() => {
                  onAgentChange(agent.id)
                  setIsOpen(false)
                }}
                title={agent.description}
              >
                <div className="flex justify-between items-center w-full">
                  <div className="flex items-center gap-sm">
                    <span className="w-6 h-6 rounded-button bg-accent/15 border border-accent/30 text-accent flex items-center justify-center">
                      <i className={`icon-${agent.icon || 'bot'} text-xs`} />
                    </span>
                    <span className="font-bold uppercase tracking-wider text-[10px]">{agent.name}</span>
                  </div>
                  <div className="flex gap-xs">
                    {agent.provider_id && (
                      <span className="px-xs py-xs rounded-button text-[8px] font-bold uppercase tracking-widest bg-text-muted/10 text-text-muted border border-white/10">
                        {providers.find(p => p.id === agent.provider_id)?.name || 'Provider'}
                      </span>
                    )}
                    {getAgentModelName(agent) && (
                      <span className="px-xs py-xs rounded-button text-[8px] font-bold uppercase tracking-widest bg-accent/10 text-accent-light border border-accent/20">
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
          </motion.div>
        )}
      </div>
    </div>
  )
}
