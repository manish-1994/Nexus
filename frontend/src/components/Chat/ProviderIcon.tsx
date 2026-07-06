import { memo } from 'react'
import {
  Bot,
  Sparkles,
  Atom,
  Boxes,
  Server,
  Cloud,
  Brain,
  Cpu,
  Network,
  Waves,
  Zap,
  Search,
  Settings,
} from 'lucide-react'

interface ProviderIconProps {
  type?: string | null
  name?: string | null
  className?: string
}

/** Maps a provider type/name to a representative lucide icon. */
function resolveIcon(type?: string | null, name?: string | null): React.ComponentType<{ className?: string }> {
  const key = (type || name || '').toLowerCase()
  if (key.includes('openai')) return Sparkles
  if (key.includes('anthropic') || key.includes('claude')) return Bot
  if (key.includes('gemini') || key.includes('google')) return Sparkles
  if (key.includes('groq')) return Atom
  if (key.includes('openrouter')) return Network
  if (key.includes('ollama')) return Boxes
  if (key.includes('lmstudio') || key.includes('lm_studio')) return Server
  if (key.includes('nvidia')) return Cpu
  if (key.includes('azure')) return Cloud
  if (key.includes('mistral')) return Waves
  if (key.includes('together')) return Brain
  if (key.includes('deepseek')) return Zap
  if (key.includes('cohere')) return Network
  if (key.includes('xai') || key.includes('grok')) return Sparkles
  if (key.includes('perplexity')) return Search
  if (key.includes('custom')) return Settings
  return Cpu
}

export const ProviderIcon = memo(function ProviderIcon({
  type,
  name,
  className = 'w-3 h-3',
}: ProviderIconProps) {
  const Icon = resolveIcon(type, name)
  return <Icon className={className} />
})
