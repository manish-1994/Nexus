import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import ProviderModelSelector from './ProviderModelSelector';
import { LiveStatusPanel } from './LiveStatusPanel';
import { TokenStreamHUD } from './TokenStreamHUD';
import { ProviderIcon } from './ProviderIcon';
import { useAgentStore } from '../../stores/agentStore';
import { useProviderStore } from '../../stores/providerStore';
import { useModelSelection } from '../../pages/hooks/useModelSelection';
import { useAIStatus } from '../../pages/hooks/useAIStatus';
import { agentApi } from '../../services/agentApi';
import { springs } from '../common/Motion';
import { Cpu, ChevronDown, Activity, Shield, Wifi, WifiOff } from 'lucide-react';

interface ConversationHeaderProps {
  conversationId: number | null;
}

export function ConversationHeader({ conversationId }: ConversationHeaderProps) {
  const [showSettings, setShowSettings] = useState(false);
  const { selectedAgentId } = useAgentStore();
  const { providers, selectedProviderId } = useProviderStore();
  const { selectedModel } = useModelSelection();
  const status = useAIStatus(conversationId);

  const { data: agentsData } = useQuery({
    queryKey: ['agents'],
    queryFn: agentApi.getAgents,
  });

  const selectedAgent = agentsData?.find(a => a.id === selectedAgentId);
  const agentName = selectedAgent ? selectedAgent.name : (selectedAgentId ? `AGENT #${selectedAgentId}` : 'NEURAL CORE (DEFAULT)');
  const selectedProvider = providers.find(p => p.id === selectedProviderId);
  const isStreaming = status.phase === 'streaming' || status.phase === 'thinking' || status.phase === 'planning' || status.phase === 'researching' || status.phase === 'calling_provider';

  return (
    <div className="border-b border-white/5 bg-surface/30 backdrop-blur-md z-10">
      <div
        className="flex items-center justify-between px-6 py-3 cursor-pointer hover:bg-white/[0.03] transition-colors duration-normal"
        onClick={() => setShowSettings(!showSettings)}
      >
        <div className="flex items-center gap-3 min-w-0">
          {/* Agent avatar with live status ring */}
          <div className="relative w-9 h-9 flex-shrink-0">
            <div className={`w-9 h-9 rounded-button bg-accent/15 border flex items-center justify-center shadow-glow-sm transition-all duration-normal ${
              isStreaming ? 'border-accent/60' : 'border-accent/30'
            }`}>
              <Cpu className="w-4 h-4 text-accent" />
            </div>
            {isStreaming && (
              <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-accent border border-background" />
              </span>
            )}
          </div>

          {/* Agent name + live status */}
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-heading text-xs font-bold text-text tracking-widest uppercase whitespace-nowrap">
                {agentName}
              </span>
              <LiveStatusPanel status={status} compact />
            </div>
            {/* Connection indicator */}
            <div className="flex items-center gap-1.5 mt-0.5">
              {isStreaming ? (
                <span className="flex items-center gap-1 text-[8px] font-bold uppercase tracking-widest text-accent">
                  <Wifi className="w-2.5 h-2.5" />
                  Connected · Streaming
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[8px] font-bold uppercase tracking-widest text-text-muted">
                  <WifiOff className="w-2.5 h-2.5" />
                  Idle
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Right: model/provider pills + toggle */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="hidden md:flex items-center gap-1.5">
            <span className="px-2 py-0.5 rounded-button text-[9px] font-bold uppercase tracking-widest bg-accent/10 text-accent-light border border-accent/20 flex items-center gap-1 whitespace-nowrap">
              <Activity className="w-2.5 h-2.5" />
              {selectedModel?.name || 'No Model'}
            </span>
            <span className="px-2 py-0.5 rounded-button text-[9px] font-bold uppercase tracking-widest bg-primary/10 text-primary-light border border-primary/20 flex items-center gap-1 whitespace-nowrap">
              {selectedProvider ? (
                <ProviderIcon name={selectedProvider.name} type={selectedProvider.type} className="w-2.5 h-2.5" />
              ) : (
                <Shield className="w-2.5 h-2.5" />
              )}
              {selectedProvider?.name || 'Provider'}
            </span>
          </div>
          <button
            className="p-1 text-text-muted hover:text-text transition-colors duration-normal flex-shrink-0"
            aria-label="Toggle settings"
          >
            <ChevronDown className={`w-4 h-4 transition-transform duration-slow ${showSettings ? 'rotate-180 text-accent' : ''}`} />
          </button>
        </div>
      </div>

      {/* Token Stream HUD — appears below header when active */}
      <AnimatePresence>
        {isStreaming && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={springs.smooth}
            className="overflow-hidden px-6"
          >
            <div className="pb-2">
              <TokenStreamHUD status={status} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence initial={false}>
        {showSettings && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={springs.smooth}
            className="overflow-hidden"
          >
            <div className="px-6 py-4 border-t border-white/5 bg-surface-elevated/40">
              <ProviderModelSelector />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
