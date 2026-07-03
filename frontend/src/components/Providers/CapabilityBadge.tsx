interface CapabilityBadgeProps {
  capability: string
  supported: boolean
}

const CAPABILITY_COLORS: Record<string, { active: string; inactive: string }> = {
  streaming: { active: 'bg-green-100 text-green-800', inactive: 'bg-gray-100 text-gray-500' },
  vision: { active: 'bg-purple-100 text-purple-800', inactive: 'bg-gray-100 text-gray-500' },
  function_calling: { active: 'bg-blue-100 text-blue-800', inactive: 'bg-gray-100 text-gray-500' },
  reasoning: { active: 'bg-yellow-100 text-yellow-800', inactive: 'bg-gray-100 text-gray-500' },
  embeddings: { active: 'bg-indigo-100 text-indigo-800', inactive: 'bg-gray-100 text-gray-500' },
}

const CAPABILITY_LABELS: Record<string, string> = {
  streaming: 'Streaming',
  vision: 'Vision',
  function_calling: 'Function Calling',
  reasoning: 'Reasoning',
  embeddings: 'Embeddings',
}

export default function CapabilityBadge({ capability, supported }: CapabilityBadgeProps) {
  const colors = CAPABILITY_COLORS[capability] || { active: 'bg-green-100 text-green-800', inactive: 'bg-gray-100 text-gray-500' }
  const label = CAPABILITY_LABELS[capability] || capability

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${supported ? colors.active : colors.inactive}`}>
      {label}
    </span>
  )
}
