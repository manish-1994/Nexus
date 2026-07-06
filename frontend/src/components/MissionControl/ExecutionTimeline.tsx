import { motion, AnimatePresence } from 'framer-motion';
import { springs } from '../../styles/motion';
import type { ExecutionEvent } from '../../types/mission-control';
import {
  Play, CheckCircle2, XCircle, Wrench, Brain,
  Search, Code, BarChart3, Database, Sparkles,
  Activity, StopCircle,
} from 'lucide-react';

// ── Event Type → Icon & Color ──
const EVENT_STYLE: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  execution_started: { icon: Play, color: 'rgba(0, 229, 255, 0.8)', label: 'Execution Started' },
  execution_completed: { icon: CheckCircle2, color: 'rgba(0, 255, 149, 0.8)', label: 'Completed' },
  execution_failed: { icon: XCircle, color: 'rgba(255, 77, 103, 0.8)', label: 'Failed' },
  execution_cancelled: { icon: StopCircle, color: 'rgba(148, 163, 184, 0.6)', label: 'Cancelled' },
  task_started: { icon: Play, color: 'rgba(59, 130, 246, 0.8)', label: 'Task Started' },
  task_completed: { icon: CheckCircle2, color: 'rgba(0, 255, 149, 0.7)', label: 'Task Complete' },
  task_failed: { icon: XCircle, color: 'rgba(255, 77, 103, 0.7)', label: 'Task Failed' },
  tool_started: { icon: Wrench, color: 'rgba(168, 85, 247, 0.7)', label: 'Tool Started' },
  tool_finished: { icon: CheckCircle2, color: 'rgba(168, 85, 247, 0.7)', label: 'Tool Finished' },
  streaming_started: { icon: Activity, color: 'rgba(59, 130, 246, 0.8)', label: 'Streaming' },
  streaming_completed: { icon: CheckCircle2, color: 'rgba(0, 255, 149, 0.7)', label: 'Stream Done' },
  planning_started: { icon: Brain, color: 'rgba(168, 85, 247, 0.7)', label: 'Planning' },
  planning_completed: { icon: CheckCircle2, color: 'rgba(168, 85, 247, 0.7)', label: 'Plan Ready' },
  failover_triggered: { icon: Activity, color: 'rgba(245, 158, 11, 0.7)', label: 'Failover' },
  retry_attempted: { icon: Activity, color: 'rgba(245, 158, 11, 0.7)', label: 'Retry' },
};

const AGENT_ICONS: Record<string, React.ElementType> = {
  planner: Brain,
  research: Search,
  coder: Code,
  analyst: BarChart3,
  memory: Database,
  tool: Wrench,
};

function getEventStyle(type: string) {
  return EVENT_STYLE[type] ?? { icon: Sparkles, color: 'rgba(148, 163, 184, 0.6)', label: type };
}

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return '--:--:--';
  }
}

// ── Props ──
interface ExecutionTimelineProps {
  events: ExecutionEvent[];
  maxItems?: number;
  activeExecutionId?: string | null;
}

export function ExecutionTimeline({ events, maxItems = 20 }: ExecutionTimelineProps) {
  const displayEvents = events.slice(0, maxItems);

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-[10px] font-bold text-text-muted tracking-widest uppercase mb-3 flex items-center gap-2">
        <Activity className="w-3.5 h-3.5 text-accent" />
        Execution Timeline
      </h2>

      <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
        <AnimatePresence initial={false}>
          {displayEvents.length === 0 ? (
            <motion.p
              className="text-[10px] text-text-muted italic text-center py-8"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              No events yet. Waiting for execution...
            </motion.p>
          ) : (
            displayEvents.map((event) => {
              const style = getEventStyle(event.type);
              const Icon = style.icon;
              const AgentIcon = event.agent_role ? AGENT_ICONS[event.agent_role] : null;

              return (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: 16 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -16 }}
                  transition={springs.smooth}
                  className="flex items-start gap-2 p-2 rounded border border-white/5 bg-surface/20"
                >
                  {/* Icon */}
                  <div
                    className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                    style={{ background: `${style.color}20`, border: `1px solid ${style.color}40` }}
                  >
                    <Icon className="w-3 h-3" style={{ color: style.color }} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: style.color }}>
                        {style.label}
                      </span>
                      {AgentIcon && (
                        <AgentIcon className="w-3 h-3 text-text-muted" />
                      )}
                      {event.agent_role && (
                        <span className="text-[8px] text-text-muted uppercase tracking-wider">
                          {event.agent_role}
                        </span>
                      )}
                    </div>
                    {event.task_id && (
                      <p className="text-[8px] text-text-muted truncate mt-0.5">
                        Task: {event.task_id}
                      </p>
                    )}
                  </div>

                  {/* Timestamp */}
                  <span className="text-[8px] text-text-muted font-mono flex-shrink-0">
                    {formatTimestamp(event.timestamp)}
                  </span>
                </motion.div>
              );
            })
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}