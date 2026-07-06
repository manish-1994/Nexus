import { motion, AnimatePresence } from 'framer-motion';
import { springs } from '../../styles/motion';
import {
  Activity,
  Clock,
  Cpu,
  Layers,
  ListTodo,
  RefreshCw,
  AlertTriangle,
  Zap,
  BrainCircuit,
  Timer,
  Hash,
  BarChart3,
  CheckCircle2,
} from 'lucide-react';
import type { ActiveExecution, AgentHealth } from '../../types/mission-control';

interface MissionStatusPanelProps {
  execution: ActiveExecution | null;
  agentHealth: Record<string, AgentHealth> | null;
  className?: string;
}

interface StatusRowProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subValue?: string;
  accent?: 'cyan' | 'green' | 'amber' | 'red' | 'purple' | 'blue';
  animate?: boolean;
}

const ACCENT_COLORS: Record<string, string> = {
  cyan: 'text-cyan-400',
  green: 'text-emerald-400',
  amber: 'text-amber-400',
  red: 'text-red-400',
  purple: 'text-purple-400',
  blue: 'text-blue-400',
};

const ACCENT_BG: Record<string, string> = {
  cyan: 'bg-cyan-400/10 border-cyan-400/20',
  green: 'bg-emerald-400/10 border-emerald-400/20',
  amber: 'bg-amber-400/10 border-amber-400/20',
  red: 'bg-red-400/10 border-red-400/20',
  purple: 'bg-purple-400/10 border-purple-400/20',
  blue: 'bg-blue-400/10 border-blue-400/20',
};

function StatusRow({ icon, label, value, subValue, accent = 'cyan', animate = false }: StatusRowProps) {
  return (
    <motion.div
      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border ${ACCENT_BG[accent]} backdrop-blur-sm`}
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={springs.gentle}
    >
      <div className={`${ACCENT_COLORS[accent]} flex-shrink-0`}>
        {animate ? (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          >
            {icon}
          </motion.div>
        ) : (
          icon
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[10px] uppercase tracking-widest text-white/40 font-mono">{label}</div>
        <div className="text-sm font-mono text-white/90 truncate">{value || '—'}</div>
        {subValue && (
          <div className="text-[10px] text-white/40 font-mono mt-0.5">{subValue}</div>
        )}
      </div>
    </motion.div>
  );
}

function formatElapsed(ms: number | undefined): string {
  if (!ms) return '—';
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  if (hours > 0) return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

function formatTimestamp(iso: string | undefined): string {
  if (!iso) return '—';
  const date = new Date(iso);
  return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function MissionStatusPanel({ execution, agentHealth, className = '' }: MissionStatusPanelProps) {
  const hasExecution = execution !== null;
  const state = execution?.state || 'idle';

  const stateAccent: Record<string, string> = {
    idle: 'blue',
    thinking: 'purple',
    planning: 'purple',
    researching: 'cyan',
    calling_provider: 'cyan',
    streaming: 'cyan',
    completed: 'green',
    failed: 'red',
    cancelled: 'amber',
  };

  const stateLabel: Record<string, string> = {
    idle: 'IDLE',
    thinking: 'THINKING',
    planning: 'PLANNING',
    researching: 'RESEARCHING',
    calling_provider: 'CALLING PROVIDER',
    streaming: 'STREAMING',
    completed: 'COMPLETED',
    failed: 'FAILED',
    cancelled: 'CANCELLED',
  };

  const accent = stateAccent[state] || 'blue';

  return (
    <motion.div
      className={`flex flex-col gap-3 ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.2, ...springs.gentle }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-1">
        <BrainCircuit className="w-4 h-4 text-cyan-400" />
        <span className="text-xs font-mono uppercase tracking-[0.15em] text-cyan-400/80">
          Mission Status
        </span>
        {hasExecution && (
          <motion.div
            className={`ml-auto w-2 h-2 rounded-full ${
              state === 'completed'
                ? 'bg-emerald-400'
                : state === 'failed'
                ? 'bg-red-400'
                : state === 'cancelled'
                ? 'bg-amber-400'
                : 'bg-cyan-400'
            }`}
            animate={
              state !== 'completed' && state !== 'failed' && state !== 'cancelled' && state !== 'idle'
                ? { scale: [1, 1.4, 1], opacity: [1, 0.6, 1] }
                : {}
            }
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          />
        )}
      </div>

      {/* Execution State Banner */}
      <AnimatePresence mode="wait">
        <motion.div
          key={state}
          className={`px-3 py-2 rounded-lg border text-center ${ACCENT_BG[accent]}`}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={springs.smooth}
        >
          <div className={`text-xs font-mono font-bold tracking-[0.2em] ${ACCENT_COLORS[accent]}`}>
            {stateLabel[state] || state.toUpperCase()}
          </div>
          {execution?.execution_id && (
            <div className="text-[9px] text-white/30 font-mono mt-0.5 truncate">
              {execution.execution_id}
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Status Rows */}
      <div className="space-y-1.5">
        <StatusRow
          icon={<Activity className="w-3.5 h-3.5" />}
          label="Current Task"
          value={execution?.current_task || '—'}
          accent={hasExecution ? 'cyan' : 'blue'}
          animate={hasExecution && state !== 'completed' && state !== 'failed' && state !== 'idle'}
        />

        <StatusRow
          icon={<Clock className="w-3.5 h-3.5" />}
          label="Execution Time"
          value={formatElapsed(execution?.elapsed_ms)}
          subValue={execution?.started_at ? `Since ${formatTimestamp(execution.started_at)}` : undefined}
          accent="blue"
        />

        <StatusRow
          icon={<Cpu className="w-3.5 h-3.5" />}
          label="Active Agent"
          value={execution?.current_agent || '—'}
          accent={hasExecution ? 'purple' : 'blue'}
        />

        <StatusRow
          icon={<ListTodo className="w-3.5 h-3.5" />}
          label="Running Tasks"
          value={execution?.running_tasks?.length || 0}
          accent="cyan"
        />

        <StatusRow
          icon={<Layers className="w-3.5 h-3.5" />}
          label="Queued Tasks"
          value={execution?.pending_tasks?.length || 0}
          accent="blue"
        />

        <StatusRow
          icon={<CheckCircle2 className="w-3.5 h-3.5" />}
          label="Completed Tasks"
          value={execution?.completed_tasks?.length || 0}
          accent="green"
        />

        <StatusRow
          icon={<RefreshCw className="w-3.5 h-3.5" />}
          label="Retries"
          value={execution?.retry_count || 0}
          accent={execution?.retry_count && execution.retry_count > 0 ? 'amber' : 'blue'}
        />

        <StatusRow
          icon={<AlertTriangle className="w-3.5 h-3.5" />}
          label="Fallbacks"
          value={execution?.fallback_used ? 'Yes' : 'No'}
          accent={execution?.fallback_used ? 'amber' : 'blue'}
        />

        <StatusRow
          icon={<Zap className="w-3.5 h-3.5" />}
          label="Provider"
          value={execution?.provider_used || '—'}
          accent="purple"
        />

        <StatusRow
          icon={<BarChart3 className="w-3.5 h-3.5" />}
          label="Model"
          value={execution?.model_used || '—'}
          accent="purple"
        />

        <StatusRow
          icon={<Hash className="w-3.5 h-3.5" />}
          label="Token Count"
          value={execution?.token_count?.toLocaleString() || '0'}
          accent="blue"
        />

        <StatusRow
          icon={<Timer className="w-3.5 h-3.5" />}
          label="Total Latency"
          value={execution?.total_latency_ms ? `${execution.total_latency_ms}ms` : '—'}
          accent="blue"
        />
      </div>

      {/* Agent Health Summary */}
      {agentHealth && Object.keys(agentHealth).length > 0 && (
        <div className="mt-2">
          <div className="text-[10px] uppercase tracking-widest text-white/30 font-mono px-1 mb-2">
            Agent Health
          </div>
          <div className="space-y-1">
            {Object.entries(agentHealth).map(([role, health]) => (
              <motion.div
                key={role}
                className="flex items-center gap-2 px-2 py-1.5 rounded"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={springs.instant}
              >
                <div
                  className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                    health.status === 'available'
                      ? 'bg-emerald-400'
                      : health.status === 'registered'
                      ? 'bg-amber-400'
                      : health.status === 'unhealthy'
                      ? 'bg-red-400'
                      : 'bg-white/20'
                  }`}
                />
                <span className="text-[10px] font-mono text-white/50 capitalize flex-1">{role}</span>
                <span className="text-[9px] font-mono text-white/30">
                  {health.latency_ms ? `${health.latency_ms}ms` : '—'}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!hasExecution && (
        <motion.div
          className="flex flex-col items-center justify-center py-6 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
            <Activity className="w-5 h-5 text-white/20" />
          </div>
          <div className="text-xs font-mono text-white/30">Awaiting Execution</div>
          <div className="text-[10px] text-white/15 mt-1 max-w-[180px]">
            Send a message in Chat to see live execution data
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

export default MissionStatusPanel;