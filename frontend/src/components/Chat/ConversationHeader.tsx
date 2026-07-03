import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import ProviderModelSelector from './ProviderModelSelector';
import { useAgentStore } from '../../stores/agentStore';
import { useProviderStore } from '../../stores/providerStore';
import { useModelSelection } from '../../pages/hooks/useModelSelection';
import { agentApi } from '../../services/agentApi';
import { Cpu, ChevronDown, Activity, Shield, Sparkles } from 'lucide-react';

export function ConversationHeader() {
  const [showSettings, setShowSettings] = useState(false);
  const { selectedAgentId } = useAgentStore();
  const { providers, selectedProviderId } = useProviderStore();
  const { selectedModel } = useModelSelection();

  const { data: agentsData } = useQuery({
    queryKey: ['agents'],
    queryFn: agentApi.getAgents,
  });

  const selectedAgent = agentsData?.find(a => a.id === selectedAgentId);
  const agentName = selectedAgent ? selectedAgent.name : (selectedAgentId ? `AGENT #${selectedAgentId}` : 'NEURAL CORE (DEFAULT)');

  return (
    <div className="flex flex-col border-b border-white/5 bg-surface/30 backdrop-blur-md shadow-glass z-10">
      <div 
        className="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors" 
        onClick={() => setShowSettings(!showSettings)}
      >
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center shadow-[inset_0_0_15px_rgba(59,130,246,0.15)]">
              <Cpu className="w-5 h-5 text-accent drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]" />
            </div>
            <div>
              <span className="font-heading text-xs font-bold text-white tracking-widest uppercase">
                {agentName}
              </span>
              <p className="text-[9px] text-text-muted font-label uppercase tracking-widest mt-0.5">Tactical Module Node</p>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-3">
            <span className="flex items-center space-x-1.5 px-2.5 py-1 bg-white/5 border border-white/10 rounded-lg text-[9px] font-bold text-text-muted tracking-wider uppercase">
              <Activity className="w-3.5 h-3.5 text-accent-light" />
              <span>{selectedModel?.name || 'No Model'}</span>
            </span>
            <span className="flex items-center space-x-1.5 px-2.5 py-1 bg-white/5 border border-white/10 rounded-lg text-[9px] font-bold text-text-muted tracking-wider uppercase">
              <Shield className="w-3.5 h-3.5 text-secondary-light" />
              <span>{providers.find(p => p.id === selectedProviderId)?.name || 'Default Provider'}</span>
            </span>
            <span className="flex items-center space-x-1.5 px-2.5 py-1 bg-success/15 border border-success/30 rounded-lg text-[9px] font-bold text-success tracking-wider uppercase shadow-[0_0_10px_rgba(34,197,94,0.1)] animate-pulse">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Streaming Armed</span>
            </span>
          </div>
        </div>

        <button className="p-2 text-text-muted hover:text-white transition-colors">
          <ChevronDown className={`w-5 h-5 transition-transform duration-300 ${showSettings ? 'rotate-180 text-accent' : ''}`} />
        </button>
      </div>
      
      {showSettings && (
        <div className="px-6 py-4 border-t border-white/5 bg-elevated/40">
          <ProviderModelSelector />
        </div>
      )}
    </div>
  );
}
