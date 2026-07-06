import { memo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Activity, Inbox } from 'lucide-react'
import type { AIStatusState, AIPhase } from '../../pages/hooks/useAIStatus'
import { cn, springs } from '../common/Motion'

interface AIActivityLogProps {
  status: AIStatusState
  defaultCollapsed?: boolean
}

const PHASE_DOT: Record<AIPhase, string> = {
  idle: 'bg-text-muted',
  thinking: 'bg-accent',
  planning: 'bg-accent',
  researching: 'bg-primary-light',
  calling_provider: 'bg-primary-light',
  streaming: 'bg-accent',
  completed: 'bg-success',
  error: 'bg-danger',
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export const AIActivityLog = memo(function AIActivityLog({
  status,
  defaultCollapsed = true,
}: AIActivityLogProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed)

  if (status.activity.length === 0 && status.phase === 'idle') return null

  return (
    <div className="glass-surface rounded-panel border border-white/5 overflow-hidden">
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-white/[0.03] transition-colors duration-normal focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/30 rounded-button"
        aria-expanded={!collapsed}
        aria-label="Toggle activity log"
      >
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-accent" />
          <span className="text-[9px] font-heading font-bold tracking-widest uppercase text-text-muted">
            Activity Log
          </span>
          {status.activity.length > 0 && (
            <span className="text-[8px] font-bold text-text-muted/60 tabular-nums">
              {status.activity.length}
            </span>
          )}
        </div>
        <ChevronDown
          className={cn(
            'w-3.5 h-3.5 text-text-muted transition-transform duration-slow',
            collapsed ? '' : 'rotate-180'
          )}
        />
      </button>

      <AnimatePresence initial={false}>
        {!collapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={springs.smooth}
            className="overflow-hidden"
          >
            <div className="px-3 py-3 pt-1 max-h-64 overflow-y-auto">
              {status.activity.length === 0 ? (
                <div className="flex items-center gap-2 text-[10px] text-text-muted italic py-2">
                  <Inbox className="w-3 h-3" />
                  No activity recorded
                </div>
              ) : (
                <div className="relative">
                  {/* Vertical line */}
                  <div className="absolute left-[3px] top-2 bottom-2 w-px bg-white/10" />

                  <div className="space-y-2.5">
                    {status.activity.map((evt) => (
                      <motion.div
                        key={evt.id}
                        initial={{ opacity: 0, x: -6 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={springs.instant}
                        className="relative flex items-start gap-2.5 pl-0"
                      >
                        <span
                          className={cn(
                            'relative z-10 w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0',
                            PHASE_DOT[evt.phase]
                          )}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="text-[10px] font-medium text-text leading-tight">
                            {evt.label}
                          </div>
                          <div className="text-[8px] font-bold uppercase tracking-widest text-text-muted/70 tabular-nums">
                            {formatTime(evt.timestamp)}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
})
