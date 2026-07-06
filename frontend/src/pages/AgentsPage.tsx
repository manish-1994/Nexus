import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Agent } from '../types/agent';
import { agentApi } from '../services/agentApi';
import { AgentTestConsole } from '../components/Agents/AgentTestConsole';
import { AgentCreateWizard } from '../components/Agents/AgentCreateWizard';
import { AgentDetailsDrawer } from '../components/Agents/AgentDetailsDrawer';
import { AgentEditDrawer } from '../components/Agents/AgentEditDrawer';
import { useProviderStore } from '../stores/providerStore';
import { toast } from 'sonner';
import { Provider } from '../types/provider';
import { MotionCard, InteractiveCard3D } from '../components/common/Motion';
import { Bot, Cpu, Zap, Activity, Edit2, Copy, Trash2, CheckCircle2, Play } from 'lucide-react';
import { motion } from 'framer-motion';

const getAgentModelName = (agent: Agent, providers: Provider[]): string | null => {
  if (!agent.preferred_model_id) return null;
  for (const provider of providers) {
    const model = provider.models.find(m => m.id === agent.preferred_model_id);
    if (model) return model.display_name || model.name;
  }
  return null;
}

export default function AgentsPage() {
  const queryClient = useQueryClient();
  const [testingAgent, setTestingAgent] = useState<Agent | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  const providers = useProviderStore(state => state.providers);

  const { data: agents = [], isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: agentApi.getAgents,
  });

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this agent?')) return;
    try {
      await agentApi.deleteAgent(id);
      toast.success('Agent deleted');
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      if (selectedAgent?.id === id) setSelectedAgent(null);
    } catch {
      toast.error('Failed to delete agent');
    }
  };

  const handleDuplicate = async (e: React.MouseEvent, agent: Agent) => {
    e.stopPropagation();
    try {
      const agentData = (({ id: _id, ...rest }: Agent) => rest)(agent);
      await agentApi.createAgent({
        ...agentData,
        name: `${agent.name} (Copy)`
      });
      toast.success('Agent duplicated');
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    } catch {
      toast.error('Failed to duplicate agent');
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-8 max-w-7xl mx-auto"
    >
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-text tracking-wider uppercase drop-shadow-md">Active Modules</h1>
          <p className="text-text-muted mt-2 text-sm tracking-wide">Manage autonomous agent configurations</p>
        </div>
        <button 
          className="bg-accent hover:bg-accent-light text-white px-6 py-2.5 rounded-button font-bold tracking-widest uppercase text-[11px] shadow-glow-sm transition-all"
          onClick={() => setShowCreateWizard(true)}
        >
          Deploy Agent
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[0, 1, 2].map(i => (
            <MotionCard key={i} className="p-6 animate-pulse">
              <div className="flex items-center space-x-4 mb-4">
                <div className="w-12 h-12 bg-white/5 rounded-full" />
                <div className="flex-1">
                  <div className="h-4 bg-white/10 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-white/5 rounded w-1/2" />
                </div>
              </div>
              <div className="space-y-3 mb-6">
                <div className="h-3 bg-white/5 rounded" />
                <div className="h-3 bg-white/5 rounded w-5/6" />
              </div>
              <div className="flex justify-between pt-4 border-t border-white/5">
                <div className="h-4 bg-white/10 rounded w-20" />
                <div className="h-4 bg-white/10 rounded w-16" />
              </div>
            </MotionCard>
          ))}
        </div>
      ) : agents.length === 0 ? (
        <div className="text-center py-24 glass-surface rounded-card border border-white/5">
          <Bot className="w-20 h-20 text-text-muted/30 mx-auto mb-6 drop-shadow-md" />
          <h3 className="text-xl font-bold text-text tracking-widest uppercase mb-2">No Active Agents</h3>
          <p className="text-text-muted mb-8 tracking-wide">Initialize a new cognitive module to begin.</p>
          <button
            onClick={() => setShowCreateWizard(true)}
            className="px-6 py-2.5 bg-accent/20 border border-accent/40 text-accent-light font-bold tracking-widest uppercase text-[11px] rounded-button hover:bg-accent/30 hover:shadow-glow transition-all"
          >
            Deploy Module
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map(agent => (
          <InteractiveCard3D
            key={agent.id}
            className="p-6 cursor-pointer group flex flex-col h-full border border-white/5 hover:border-accent/30 hover:shadow-glow transition-all"
            onClick={() => setSelectedAgent(agent)}
          >
            <div className="flex items-center space-x-4 mb-5">
              <div className="w-12 h-12 rounded-button bg-accent/10 border border-accent/20 flex items-center justify-center shadow-[inset_0_0_15px_rgba(59,130,246,0.1)]">
                <Bot className="w-6 h-6 text-accent drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-base tracking-wide text-text truncate drop-shadow-md">{agent.name}</h3>
                <div className="flex items-center space-x-2 mt-1">
                  <span className={`flex items-center space-x-1 px-1.5 py-0.5 rounded-button text-[9px] font-bold uppercase tracking-wider ${agent.enabled ? 'bg-success/10 text-success border border-success/20' : 'bg-white/5 text-text-muted border border-white/10'}`}>
                    {agent.enabled ? <Activity className="w-3 h-3" /> : null}
                    <span>{agent.enabled ? 'Online' : 'Offline'}</span>
                  </span>
                  <span className="text-[10px] text-text-muted font-medium truncate uppercase tracking-wider">
                    {providers.find(p => p.id === agent.provider_id)?.name || 'Default Provider'}
                  </span>
                </div>
              </div>
            </div>
       
            <p className="text-text-muted text-xs mb-5 h-8 overflow-hidden line-clamp-2 leading-relaxed tracking-wide">
              {agent.description || 'No description provided.'}
            </p>
       
            <div className="flex gap-2 flex-wrap mb-6 mt-auto">
              {getAgentModelName(agent, providers) && (
                <span className="flex items-center space-x-1 px-2 py-1 text-[9px] font-bold uppercase tracking-wider bg-white/5 text-text border border-white/10 rounded-button">
                  <Cpu className="w-3 h-3 text-text-muted" />
                  <span>{getAgentModelName(agent, providers)}</span>
                </span>
              )}
              {agent.streaming && (
                <span className="flex items-center space-x-1 px-2 py-1 text-[9px] font-bold uppercase tracking-wider bg-secondary/10 text-secondary border border-secondary/20 rounded-button">
                  <Zap className="w-3 h-3" />
                  <span>Stream</span>
                </span>
              )}
              {agent.memory_enabled && (
                <span className="flex items-center space-x-1 px-2 py-1 text-[9px] font-bold uppercase tracking-wider bg-accent/10 text-accent border border-accent/20 rounded-button">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Memory</span>
                </span>
              )}
            </div>
       
            <div className="flex justify-between items-center pt-4 border-t border-white/5 opacity-60 group-hover:opacity-100 transition-opacity">
              <div className="flex space-x-1">
                <button
                  onClick={(e) => { e.stopPropagation(); setEditingAgent(agent); }}
                  className="p-2 text-text-muted hover:text-accent hover:bg-accent/10 rounded-button transition-colors"
                  title="Configure"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => handleDuplicate(e, agent)}
                  className="p-2 text-text-muted hover:text-success hover:bg-success/10 rounded-button transition-colors"
                  title="Duplicate"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => handleDelete(e, agent.id)}
                  className="p-2 text-text-muted hover:text-danger hover:bg-danger/10 rounded-button transition-colors"
                  title="Terminate"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); setTestingAgent(agent) }}
                className="flex items-center space-x-1 px-3 py-1.5 text-[10px] uppercase tracking-widest font-bold bg-white/5 border border-white/10 rounded-button hover:bg-accent hover:border-accent hover:text-white transition-all hover:shadow-glow text-text-muted"
              >
                <Play className="w-3 h-3" />
                <span>Test</span>
              </button>
            </div>
          </InteractiveCard3D>
        ))}
        </div>
      )}
      
      {testingAgent && (
        <AgentTestConsole
          agent={testingAgent}
          onClose={() => setTestingAgent(null)}
        />
      )}

      {showCreateWizard && (
        <AgentCreateWizard onClose={() => setShowCreateWizard(false)} />
      )}

      {selectedAgent && (
        <AgentDetailsDrawer
          agent={selectedAgent}
          onClose={() => setSelectedAgent(null)}
        />
      )}
      
      {editingAgent && (
        <AgentEditDrawer
          agent={editingAgent}
          onClose={() => setEditingAgent(null)}
        />
      )}
    </motion.div>
  );
}