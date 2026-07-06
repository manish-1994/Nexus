import { memo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Brain, ListChecks, Search, Radio, FileText, CheckCircle2, AlertCircle } from 'lucide-react'
import type { AIStatusState, AIPhase } from '../../pages/hooks/useAIStatus'
import { cn, springs } from '../common/Motion'

interface ResponseTimelineProps {
  status: AIStatusState
  /** Default collapsed (per spec). */
  defaultCollapsed?: boolean
}

interface TimelineStep {
  phase: AIPhase
  label: string
  icon: React.ReactNode
  color: string
}

const STEPS: TimelineStep[] = [
  { phase: 'thinking', label: 'Thinking', icon: <Brain className="w-3 h-3" />, color: 'text-accent' },
  { phase: 'planning', label: 'Planning', icon: <ListChecks className="w-3 h-3" />, color: 'text-accent' },
  { phase: 'researching', label: 'Researching', icon: <Search className="w-3 h-3" />, color: 'text-primary-light' },
  { phase: 'calling_provider', label: 'Calling Provider', icon: <Radio className="w-3 h-3" />, color: 'text-primary-light' },
  { phase: 'streaming', label: 'Generating', icon: <FileText className="w-3 h-3" />, color: 'text-accent' },
  { phase: 'completed', label: 'Completed', icon: <CheckCircle2 className="w-3 h-3" />, color: 'text-success' },
]

/** Order index for comparing phase progression. */
const PHASE_ORDER: AIPhase[] = [
  'idle',
  'thinking',
  'planning',
  'researching',
  'calling_provider',
  'streaming',
  'completed',
  'error',
]

function phaseIndex(phase: AIPhase): number {
  const idx = PHASE_ORDER.indexOf(phase)
  return idx === -1 ? 0 : idx
}

export const ResponseTimeline = memo(function ResponseTimeline({
  status,
  defaultCollapsed = true,
}: ResponseTimelineProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed)
  const currentIdx = phaseIndex(status.phase)
  const isError = status.phase === 'error'
  const isIdle = status.phase === 'idle'

  // Don't render when there's nothing to show.
  if (isIdle && status.activity.length === 0) return null

  return (
    <div className="glass-surface rounded-panel border border-white/5 overflow-hidden">
      {/* Header — always visible */}
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-white/[0.03] transition-colors duration-normal focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/30 rounded-panel"
        aria-expanded={!collapsed}
        aria-label="Toggle response timeline"
      >
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'w-1.5 h-1.5 rounded-full',
              isError ? 'bg-danger' : status.phase === 'idle' ? 'bg-text-muted' : 'bg-accent'
            )}
          />
          <span className="text-[9px] font-heading font-bold tracking-widest uppercase text-text-muted">
            Response Timeline
          </span>
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
            <div className="px-3 py-3 pt-1">
              {/* Horizontal step indicator */}
              <div className="flex items-center gap-1 mb-3">
                {STEPS.map((step, i) => {
                  const stepIdx = phaseIndex(step.phase)
                  const isDone = currentIdx > stepIdx
                  const isCurrent = status.phase === step.phase
                  return (
                    <div key={step.phase} className="flex items-center gap-1 flex-1">
                      <div
                        className={cn(
                          'flex items-center gap-1 px-1.5 py-1 rounded-button border text-[8px] font-bold uppercase tracking-widest transition-all duration-normal',
                          isCurrent
                            ? 'bg-accent/15 border-accent/40 text-accent'
                            : isDone
                            ? 'bg-success/10 border-success/30 text-success'
                            : isError
                            ? 'bg-white/[0.02] border-white/5 text-text-muted/40'
                            : 'bg-white/[0.02] border-white/5 text-text-muted/60'
                        )}
                      >
                        {step.icon}
                        <span className="hidden sm:inline">{step.label}</span>
                      </div>
                      {i < STEPS.length - 1 && (
                        <div
                          className={cn(
                            'h-px flex-1 min-w-[8px]',
                            isDone ? 'bg-success/40' : 'bg-white/10'
                          )}
                        />
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Error state */}
              {isError && (
                <div className="flex items-center gap-2 px-2 py-1.5 rounded-button bg-danger/10 border border-danger/30">
                  <AlertCircle className="w-3 h-3 text-danger" />
                  <span className="text-[10px] font-medium text-danger">
                    Execution failed — see message for details
                  </span>
                </div>
              )}

              {/* Vertical event log */}
              <div className="space-y-1.5">
                {status.activity.slice(0, 8).map((evt) => (
                  <motion.div
                    key={evt.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={springs.instant}
                    className="flex items-center gap-2 text-[10px]"
                  >
                    <span className="w-1 h-1 rounded-full bg-accent/60 flex-shrink-0" />
                    <span className="text-text-muted tabular-nums">
                      {new Date(evt.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </span>
                    <span className="text-text truncate">{evt.label}</span>
                  </motion.div>
                ))}
                {status.activity.length === 0 && (
                  <div className="text-[10px] text-text-muted italic px-2">
                    No activity recorded yet
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
})
