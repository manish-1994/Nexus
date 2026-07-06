import { memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Zap, Gauge, Clock, DollarSign, Radio } from 'lucide-react'
import type { AIStatusState } from '../../pages/hooks/useAIStatus'
import { cn, springs } from '../common/Motion'

interface TokenStreamHUDProps {
  status: AIStatusState
}

/** Rough cost estimate per 1K tokens (USD) — conservative defaults. */
const COST_PER_1K: Record<string, number> = {
  'gpt-4': 0.06,
  'gpt-4o': 0.005,
  'claude-3-5-sonnet': 0.015,
  'claude-3-opus': 0.015,
  'gemini-1.5-pro': 0.007,
  'gemini-2': 0.007,
  default: 0.005,
}

function estimateCost(tokens: number, model?: string | null): number {
  if (!tokens) return 0
  const key = model ? Object.keys(COST_PER_1K).find((k) => model.toLowerCase().includes(k)) : null
  const rate = (key ? COST_PER_1K[key] : COST_PER_1K.default) ?? COST_PER_1K.default
  return (tokens / 1000) * rate
}

function formatCost(cost: number): string {
  if (cost < 0.01) return `$${cost.toFixed(4)}`
  return `$${cost.toFixed(3)}`
}

function formatElapsed(seconds: number): string {
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}m ${s}s`
}

export const TokenStreamHUD = memo(function TokenStreamHUD({ status }: TokenStreamHUDProps) {
  const isStreaming = status.phase === 'streaming'
  const isActive =
    status.phase === 'streaming' ||
    status.phase === 'thinking' ||
    status.phase === 'planning' ||
    status.phase === 'researching' ||
    status.phase === 'calling_provider'

  const cost = estimateCost(status.tokens, status.model)

  return (
    <AnimatePresence>
      {isActive && (
        <motion.div
          initial={{ opacity: 0, y: 8, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 8, scale: 0.98 }}
          transition={springs.smooth}
          className="glass-surface rounded-panel border border-accent/20 px-3 py-2 flex items-center gap-3 flex-wrap"
          role="status"
          aria-live="polite"
          aria-label="Token stream metrics"
        >
          {/* Streaming indicator */}
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2.5 w-2.5">
              {isStreaming && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
              )}
              <span
                className={cn(
                  'relative inline-flex rounded-full h-2.5 w-2.5',
                  isStreaming ? 'bg-accent' : 'bg-accent/50'
                )}
              />
            </span>
            <Radio className={cn('w-3 h-3', isStreaming ? 'text-accent' : 'text-text-muted')} />
          </div>

          {/* Tokens generated */}
          <HudMetric
            icon={<Zap className="w-3 h-3 text-accent" />}
            label="Tokens"
            value={String(status.tokens)}
            highlight={isStreaming}
          />

          {/* Speed */}
          <HudMetric
            icon={<Gauge className="w-3 h-3 text-primary-light" />}
            label="Speed"
            value={status.tokensPerSecond > 0 ? `${status.tokensPerSecond}/s` : '—'}
          />

          {/* Elapsed */}
          <HudMetric
            icon={<Clock className="w-3 h-3 text-warning" />}
            label="Elapsed"
            value={formatElapsed(status.elapsed)}
          />

          {/* Cost */}
          <HudMetric
            icon={<DollarSign className="w-3 h-3 text-success" />}
            label="Cost"
            value={formatCost(cost)}
          />
        </motion.div>
      )}
    </AnimatePresence>
  )
})

const HudMetric = memo(function HudMetric({
  icon,
  label,
  value,
  highlight = false,
}: {
  icon: React.ReactNode
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div className="flex items-center gap-1.5">
      {icon}
      <span className="text-[8px] font-bold uppercase tracking-widest text-text-muted">
        {label}
      </span>
      <span
        className={cn(
          'text-[11px] font-bold tabular-nums',
          highlight ? 'text-accent' : 'text-text'
        )}
      >
        {value}
      </span>
    </div>
  )
})
