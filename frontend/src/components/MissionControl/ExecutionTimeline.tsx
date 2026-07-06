import { motion, AnimatePresence } from 'framer-motion';
import type { ExecutionEvent } from '../../types/mission-control';
import {
  CheckCircle2, XCircle, Wrench, Brain,
  Search, Code, BarChart3, Database, Sparkles,
  Loader2, Hourglass
} from 'lucide-react';

const AGENT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  planner: Brain,
  research: Search,
  coder: Code,
  analyst: BarChart3,
  memory: Database,
  tool: Wrench,
};

const STATUS_CONFIG = {
  idle: { color: '#64748B', bg: 'rgba(100,116,139,0.1)', text: 'Standby', icon: Hourglass },
  waiting: { color: '#94A3B8', bg: 'rgba(148,163,184,0.1)', text: 'Waiting', icon: Hourglass },
  running: { color: '#00D4FF', bg: 'rgba(0,212,255,0.15)', text: 'Running', icon: Loader2 },
  completed: { color: '#00FF95', bg: 'rgba(0,255,149,0.12)', text: 'Completed', icon: CheckCircle2 },
  failed: { color: '#F59E0B', bg: 'rgba(245,158,11,0.15)', text: 'Failed', icon: XCircle },
};

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return '--:--:--';
  }
}

interface ExecutionTimelineProps {
  events: ExecutionEvent[];
  maxItems?: number;
}

export function ExecutionTimeline({ events, maxItems = 20 }: ExecutionTimelineProps) {
  // ── Find active execution ID ──
  const activeExecutionId = events[0]?.execution_id || null;

  // ── Derive current status of each agent role ──
  const agentStatus: Record<string, { state: 'idle' | 'waiting' | 'running' | 'completed' | 'failed'; time?: string }> = {
    planner: { state: 'idle' },
    memory: { state: 'idle' },
    research: { state: 'idle' },
    tool: { state: 'idle' },
    coder: { state: 'idle' },
    analyst: { state: 'idle' },
  };

  if (activeExecutionId) {
    // Set all to waiting initially if an execution is active
    Object.keys(agentStatus).forEach(k => {
      agentStatus[k] = { state: 'waiting' };
    });

    // Process events in chronological order to build final state
    const sortedEvents = [...events]
      .filter(e => e.execution_id === activeExecutionId)
      .reverse();

    sortedEvents.forEach(evt => {
      const role = evt.agent_role;
      if (!role || !agentStatus[role]) return;

      const timeStr = formatTimestamp(evt.timestamp);

      if (evt.type === 'task_started' || evt.type === 'tool_started' || evt.type === 'planning_started') {
        agentStatus[role] = { state: 'running', time: timeStr };
      } else if (evt.type === 'task_completed' || evt.type === 'tool_finished' || evt.type === 'planning_completed') {
        agentStatus[role] = { state: 'completed', time: timeStr };
      } else if (evt.type === 'task_failed' || evt.type === 'tool_failed') {
        agentStatus[role] = { state: 'failed', time: timeStr };
      }
    });
  }

  const recentLogs = events.slice(0, maxItems);

  return (
    <div className="flex flex-col h-full gap-4 font-mono select-none">
      {/* ── Active Pipeline Grid ── */}
      <div className="grid grid-cols-1 gap-2 bg-white/[0.02] border border-white/[0.04] p-3 rounded-xl shrink-0">
        <div className="flex items-center justify-between pb-1.5 border-b border-white/[0.04] text-[8px] text-white/30 uppercase tracking-widest font-bold">
          <span>Cognitive Pipeline</span>
          <span>Status</span>
        </div>

        {Object.entries(agentStatus).map(([role, status]) => {
          const cfg = STATUS_CONFIG[status.state];
          const Icon = cfg.icon;
          const AgentIcon = AGENT_ICONS[role] || Sparkles;

          return (
            <div key={role} className="flex items-center justify-between py-1.5 px-2 rounded-lg border border-white/[0.02] bg-white/[0.01] hover:bg-white/[0.03] transition-colors">
              <div className="flex items-center gap-2 min-w-0">
                <div className="p-1 rounded-md bg-white/[0.03] border border-white/[0.06] text-white/50">
                  <AgentIcon className="w-3.5 h-3.5" />
                </div>
                <div className="min-w-0">
                  <span className="text-[10px] text-white/75 uppercase tracking-wider block truncate">{role}</span>
                  <span className="text-[6.5px] text-white/20 uppercase tracking-widest block">{status.time || 'Standby'}</span>
                </div>
              </div>

              {/* Status bar block indicator */}
              <div className="flex items-center gap-2.5">
                <div className="w-24 h-1.5 bg-white/[0.04] rounded-full overflow-hidden relative border border-white/[0.06]">
                  {status.state === 'running' && (
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: cfg.color }}
                      animate={{ left: ['-100%', '100%'] }}
                      transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                      initial={{ left: '-100%' }}
                    />
                  )}
                  {status.state === 'completed' && (
                    <div className="w-full h-full rounded-full" style={{ background: cfg.color }} />
                  )}
                  {status.state === 'failed' && (
                    <motion.div
                      className="w-full h-full rounded-full"
                      style={{ background: cfg.color }}
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.2, repeat: Infinity }}
                    />
                  )}
                </div>

                <div
                  className="flex items-center gap-1 px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider min-w-[76px] justify-center"
                  style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}25` }}
                >
                  {status.state === 'running' && (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                    >
                      <Icon className="w-2.5 h-2.5" />
                    </motion.div>
                  )}
                  {status.state !== 'running' && <Icon className="w-2.5 h-2.5" />}
                  <span>{cfg.text}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Recent Event Stream Logs ── */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="text-[8px] text-white/25 uppercase tracking-widest font-bold pb-2 shrink-0">Recent OS Telemetry</div>
        <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
          <AnimatePresence initial={false}>
            {recentLogs.length === 0 ? (
              <motion.p
                className="text-[9px] text-white/20 italic text-center py-6 border border-dashed border-white/[0.04] rounded-lg"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                Telemetry offline. Awaiting connection...
              </motion.p>
            ) : (
              recentLogs.map((event) => {
                const isCompleted = event.type.includes('complete') || event.type.includes('finished');
                const isFailed = event.type.includes('fail') || event.type.includes('error');
                const statusColor = isCompleted ? 'text-success' : isFailed ? 'text-warning' : 'text-accent';

                return (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                    className="flex items-start justify-between gap-3 p-2 rounded-lg border border-white/[0.03] bg-white/[0.01]"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="w-1.5 h-1.5 rounded-full bg-white/20 shrink-0" />
                        <span className={`text-[9px] font-bold uppercase tracking-wider ${statusColor}`}>
                          {event.type.replace(/_/g, ' ')}
                        </span>
                        {event.agent_role && (
                          <span className="text-[7.5px] bg-white/[0.04] border border-white/[0.08] px-1 rounded text-white/50 uppercase tracking-widest">
                            {event.agent_role}
                          </span>
                        )}
                      </div>
                      {event.task_id && (
                        <p className="text-[7.5px] text-white/25 truncate mt-1">
                          TSK: {event.task_id}
                        </p>
                      )}
                    </div>
                    <span className="text-[7.5px] text-white/20 font-mono flex-shrink-0 mt-0.5">
                      {formatTimestamp(event.timestamp)}
                    </span>
                  </motion.div>
                );
              })
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}