interface CapabilityBadgeProps {
  capability: string
  supported: boolean
}

const CAPABILITY_COLORS: Record<string, { active: string; inactive: string }> = {
  streaming: { active: 'badge-success', inactive: 'badge-neutral' },
  vision: { active: 'badge-secondary', inactive: 'badge-neutral' },
  function_calling: { active: 'badge-accent', inactive: 'badge-neutral' },
  reasoning: { active: 'badge-warning', inactive: 'badge-neutral' },
  embeddings: { active: 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 inline-flex items-center px-2 py-0.5 rounded-button text-xs font-medium', inactive: 'badge-neutral' },
}

const CAPABILITY_LABELS: Record<string, string> = {
  streaming: 'Streaming',
  vision: 'Vision',
  function_calling: 'Function Calling',
  reasoning: 'Reasoning',
  embeddings: 'Embeddings',
}

export default function CapabilityBadge({ capability, supported }: CapabilityBadgeProps) {
  const colors = CAPABILITY_COLORS[capability] || { active: 'badge-success', inactive: 'badge-neutral' }
  const label = CAPABILITY_LABELS[capability] || capability

  return (
    <span className={supported ? colors.active : colors.inactive}>
      {label}
    </span>
  )
}