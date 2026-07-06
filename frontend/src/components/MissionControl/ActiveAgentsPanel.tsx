import { motion } from 'framer-motion';
import { springs } from '../../styles/motion';
import {
  Brain,
  Search,
  Code,
  BarChart3,
  Database,
  Wrench,
  Cpu,
  Zap,
  Activity,
  Clock,
  Layers,
} from 'lucide-react';
import type { AgentConfig, AgentHealth } from '../../types/mission-control';

interface ActiveAgentsPanelProps {
  agents: AgentConfig[];
  agentHealth: Record<string, AgentHealth> | null;
  activeAgentRole?: string | null;
  className?: string;
}

const AGENT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  planner: Brain,
  research: Search,
  coder: Code,
  analyst: BarChart3,
  memory: Database,
  tool: Wrench,
};

const AGENT_COLORS: Record<string, { accent: string; bg: string; border: string; glow: string }> = {
  planner: {
    accent: 'text-purple-400',
    bg: 'bg-purple-400/5',
    border: 'border-purple-400/15',
    glow: 'shadow-purple-400/10',
  },
  research: {
    accent: 'text-cyan-400',
    bg: 'bg-cyan-400/5',
    border: 'border-cyan-400/15',
    glow: 'shadow-cyan-400/10',
  },
  coder: {
    accent: 'text-emerald-400',
    bg: 'bg-emerald-400/5',
    border: 'border-emerald-400/15',
    glow: 'shadow-emerald-400/10',
  },
  analyst: {
    accent: 'text-amber-400',
    bg: 'bg-amber-400/5',
    border: 'border-amber-400/15',
    glow: 'shadow-amber-400/10',
  },
  memory: {
    accent: 'text-blue-400',
    bg: 'bg-blue-400/5',
    border: 'border-blue-400/15',
    glow: 'shadow-blue-400/10',
  },
  tool: {
    accent: 'text-rose-400',
    bg: 'bg-rose-400/5',
    border: 'border-rose-400/15',
    glow: 'shadow-rose-400/10',
  },
};

const DEFAULT_COLOR = {
  accent: 'text-white/60',
  bg: 'bg-white/5',
  border: 'border-white/10',
  glow: 'shadow-white/5',
};

function getAgentColor(role: string) {
  return AGENT_COLORS[role] || DEFAULT_COLOR;
}

function getAgentIcon(role: string) {
  const Icon = AGENT_ICONS[role] || Cpu;
  return Icon;
}

function AgentCard({
  config,
  health,
  isActive,
}: {
  config: AgentConfig;
  health: AgentHealth | undefined;
  isActive: boolean;
}) {
  const colors = getAgentColor(config.role);
  const Icon = getAgentIcon(config.role);
  const status = health?.status || 'unknown';

  const statusDotMap: Record<string, string> = {
    available: 'bg-emerald-400',
    registered: 'bg-amber-400',
    unhealthy: 'bg-red-400',
    unknown: 'bg-white/20',
  };

  const statusLabelMap: Record<string, string> = {
    available: 'Available',
    registered: 'Registered',
    unhealthy: 'Unhealthy',
    unknown: 'Unknown',
  };

  const statusDot = statusDotMap[status] || statusDotMap.unknown;
  const statusLabel = statusLabelMap[status] || statusLabelMap.unknown;

  return (
    <motion.div
      className={`relative rounded-lg border ${colors.border} ${colors.bg} ${colors.glow} p-3 backdrop-blur-sm overflow-hidden`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={springs.gentle}
      whileHover={{ scale: 1.02, transition: springs.instant }}
    >
      {/* Active indicator */}
      {isActive && (
        <motion.div
          className="absolute inset-0 rounded-lg"
          animate={{ opacity: [0.05, 0.12, 0.05] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          style={{ background: `var(--active-glow, ${colors.accent.replace('text-', '')})` }}
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-2.5 mb-2.5 relative z-10">
        <div className={`w-8 h-8 rounded-lg ${colors.bg} border ${colors.border} flex items-center justify-center`}>
          <Icon className={`w-4 h-4 ${colors.accent}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-mono font-semibold text-white/90 truncate capitalize">
            {config.name}
          </div>
          <div className="text-[9px] font-mono text-white/30 uppercase tracking-wider">
            {config.role}
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <div className={`w-2 h-2 rounded-full ${statusDot}`} />
          <span className="text-[9px] font-mono text-white/40">{statusLabel}</span>
        </div>
      </div>

      {/* Capabilities */}
      <div className="flex flex-wrap gap-1 mb-2.5 relative z-10">
        {config.capabilities.slice(0, 4).map((cap) => (
          <span
            key={cap}
            className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-white/50 border border-white/5"
          >
            {cap}
          </span>
        ))}
        {config.capabilities.length > 4 && (
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-white/30">
            +{config.capabilities.length - 4}
          </span>
        )}
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-3 text-[9px] font-mono text-white/40 relative z-10">
        <div className="flex items-center gap-1">
          <Zap className="w-3 h-3" />
          <span>{config.preferred_provider || 'default'}</span>
        </div>
        <div className="flex items-center gap-1">
          <Cpu className="w-3 h-3" />
          <span className="truncate max-w-[80px]">{config.preferred_model || 'default'}</span>
        </div>
        {health?.latency_ms !== undefined && (
          <div className="flex items-center gap-1 ml-auto">
            <Clock className="w-3 h-3" />
            <span>{health.latency_ms}ms</span>
          </div>
        )}
      </div>

      {/* Tools count */}
      {config.tools && config.tools.length > 0 && (
        <div className="flex items-center gap-1 mt-2 text-[9px] font-mono text-white/30 relative z-10">
          <Wrench className="w-3 h-3" />
          <span>{config.tools.length} tool{config.tools.length !== 1 ? 's' : ''}</span>
          <span className="text-white/15">
            ({config.tools.slice(0, 3).join(', ')}{config.tools.length > 3 ? '...' : ''})
          </span>
        </div>
      )}
    </motion.div>
  );
}

export function ActiveAgentsPanel({
  agents,
  agentHealth,
  activeAgentRole,
  className = '',
}: ActiveAgentsPanelProps) {
  const builtInAgents = agents.filter((a) =>
    ['planner', 'research', 'coder', 'analyst', 'memory', 'tool'].includes(a.role)
  );
  const customAgents = agents.filter(
    (a) => !['planner', 'research', 'coder', 'analyst', 'memory', 'tool'].includes(a.role)
  );

  return (
    <motion.div
      className={`flex flex-col gap-3 ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3, ...springs.gentle }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-1">
        <Layers className="w-4 h-4 text-cyan-400" />
        <span className="text-xs font-mono uppercase tracking-[0.15em] text-cyan-400/80">
          Active Agents
        </span>
        <span className="ml-auto text-[10px] font-mono text-white/30">
          {agents.length} registered
        </span>
      </div>

      {/* Built-in Agents */}
      {builtInAgents.length > 0 && (
        <div>
          <div className="text-[9px] uppercase tracking-widest text-white/25 font-mono px-1 mb-2">
            Core Agents
          </div>
          <div className="space-y-2">
            {builtInAgents.map((agent) => (
              <AgentCard
                key={agent.role}
                config={agent}
                health={agentHealth?.[agent.role]}
                isActive={activeAgentRole === agent.role}
              />
            ))}
          </div>
        </div>
      )}

      {/* Custom Agents */}
      {customAgents.length > 0 && (
        <div className="mt-1">
          <div className="text-[9px] uppercase tracking-widest text-white/25 font-mono px-1 mb-2">
            Custom Agents
          </div>
          <div className="space-y-2">
            {customAgents.map((agent) => (
              <AgentCard
                key={agent.role}
                config={agent}
                health={agentHealth?.[agent.role]}
                isActive={activeAgentRole === agent.role}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {agents.length === 0 && (
        <motion.div
          className="flex flex-col items-center justify-center py-8 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mb-2">
            <Activity className="w-4 h-4 text-white/20" />
          </div>
          <div className="text-xs font-mono text-white/30">No Agents Registered</div>
          <div className="text-[10px] text-white/15 mt-1">
            Agent registry is empty
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

export default ActiveAgentsPanel;