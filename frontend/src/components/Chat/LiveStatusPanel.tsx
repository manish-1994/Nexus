import { memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Cpu, Activity, Zap, Clock, Radio } from 'lucide-react'
import type { AIStatusState, AIPhase } from '../../pages/hooks/useAIStatus'
import { cn, springs } from '../common/Motion'

interface LiveStatusPanelProps {
  status: AIStatusState
  /** Compact mode renders a single inline row (for the header). */
  compact?: boolean
}

const PHASE_CONFIG: Record<
  AIPhase,
  { label: string; color: string; bg: string; border: string; dotClass: string; progress: number }
> = {
  idle: {
    label: 'Idle',
    color: 'text-text-muted',
    bg: 'bg-white/5',
    border: 'border-white/10',
    dotClass: 'bg-text-muted',
    progress: 0,
  },
  thinking: {
    label: 'Thinking',
    color: 'text-accent',
    bg: 'bg-accent/10',
    border: 'border-accent/30',
    dotClass: 'bg-accent',
    progress: 15,
  },
  planning: {
    label: 'Planning',
    color: 'text-accent',
    bg: 'bg-accent/10',
    border: 'border-accent/30',
    dotClass: 'bg-accent',
    progress: 30,
  },
  researching: {
    label: 'Researching',
    color: 'text-primary-light',
    bg: 'bg-primary/10',
    border: 'border-primary/30',
    dotClass: 'bg-primary-light',
    progress: 45,
  },
  calling_provider: {
    label: 'Calling Provider',
    color: 'text-primary-light',
    bg: 'bg-primary/10',
    border: 'border-primary/30',
    dotClass: 'bg-primary-light',
    progress: 60,
  },
  streaming: {
    label: 'Streaming Response',
    color: 'text-accent',
    bg: 'bg-accent/10',
    border: 'border-accent/30',
    dotClass: 'bg-accent',
    progress: 80,
  },
  completed: {
    label: 'Completed',
    color: 'text-success',
    bg: 'bg-success/10',
    border: 'border-success/30',
    dotClass: 'bg-success',
    progress: 100,
  },
  error: {
    label: 'Error',
    color: 'text-danger',
    bg: 'bg-danger/10',
    border: 'border-danger/30',
    dotClass: 'bg-danger',
    progress: 100,
  },
}

function formatElapsed(seconds: number): string {
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}m ${s}s`
}

export const LiveStatusPanel = memo(function LiveStatusPanel({
  status,
  compact = false,
}: LiveStatusPanelProps) {
  const config = PHASE_CONFIG[status.phase]
  const isActive = status.phase !== 'idle' && status.phase !== 'completed' && status.phase !== 'error'

  if (compact) {
    return (
      <div
        className={cn(
          'inline-flex items-center gap-2 px-2.5 py-1 rounded-button border text-[10px] font-bold uppercase tracking-widest transition-all duration-normal',
          config.bg,
          config.border,
          config.color
        )}
        role="status"
        aria-live="polite"
        aria-label={`AI status: ${config.label}`}
      >
        <span className="relative flex h-2 w-2">
          {isActive && (
            <span
              className={cn('animate-ping absolute inline-flex h-full w-full rounded-full opacity-75', config.dotClass)}
            />
          )}
          <span className={cn('relative inline-flex rounded-full h-2 w-2', config.dotClass)} />
        </span>
        <span>{config.label}</span>
        {status.elapsed > 0 && (
          <span className="text-text-muted/70 font-medium normal-case tracking-normal">
            {formatElapsed(status.elapsed)}
          </span>
        )}
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={springs.smooth}
      className={cn(
        'glass-surface rounded-panel border p-4 transition-all duration-normal',
        config.border
      )}
      role="status"
      aria-live="polite"
      aria-label={`AI status: ${config.label}`}
    >
      {/* Header row: state + elapsed */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div
            className={cn(
              'w-9 h-9 rounded-button border flex items-center justify-center',
              config.bg,
              config.border
            )}
          >
            <Cpu className={cn('w-4 h-4', config.color)} />
          </div>
          <div>
            <div className="text-[9px] font-heading font-bold tracking-widest uppercase text-text-muted">
              System Node
            </div>
            <div className={cn('text-sm font-bold tracking-tight', config.color)}>
              {config.label}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-text-muted">
          <Clock className="w-3 h-3" />
          <span className="tabular-nums">{formatElapsed(status.elapsed)}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 rounded-full bg-white/5 overflow-hidden mb-3">
        <motion.div
          className={cn('h-full rounded-full', config.dotClass)}
          initial={{ width: 0 }}
          animate={{ width: `${config.progress}%` }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        />
      </div>

      {/* Metadata grid */}
      <div className="grid grid-cols-3 gap-2">
        <Metric
          icon={<Radio className="w-3 h-3" />}
          label="Provider"
          value={status.provider ?? '—'}
        />
        <Metric
          icon={<Activity className="w-3 h-3" />}
          label="Model"
          value={status.model ?? '—'}
        />
        <Metric
          icon={<Zap className="w-3 h-3" />}
          label="Tokens"
          value={status.tokens > 0 ? String(status.tokens) : '—'}
        />
      </div>

      {/* Live activity ticker */}
      <AnimatePresence mode="popLayout">
        {status.activity[0] && (
          <motion.div
            key={status.activity[0].id}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={springs.instant}
            className="mt-3 pt-3 border-t border-white/5 overflow-hidden"
          >
            <div className="flex items-center gap-2 text-[10px] font-medium text-text-muted">
              <span className={cn('w-1.5 h-1.5 rounded-full', config.dotClass)} />
              <span className="truncate">{status.activity[0].label}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
})

const Metric = memo(function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="rounded-button bg-white/[0.03] border border-white/5 px-2.5 py-2">
      <div className="flex items-center gap-1 text-[8px] font-bold uppercase tracking-widest text-text-muted mb-0.5">
        {icon}
        {label}
      </div>
      <div className="text-[11px] font-semibold text-text truncate" title={value}>
        {value}
      </div>
    </div>
  )
})
