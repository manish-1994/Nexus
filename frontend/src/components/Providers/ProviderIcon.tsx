import { ProviderType } from '../../types/provider'

interface ProviderIconProps {
  type: ProviderType
  className?: string
}

function ProviderIcon({ type, className = 'w-5 h-5' }: ProviderIconProps) {
  const iconMap: Record<ProviderType, string> = {
    openai_compatible: '🔌',
    openai: '✨',
    anthropic: '🧠',
    gemini: '💎',
    groq: '⚡',
    openrouter: '🔀',
    ollama: '🦙',
    lmstudio: '🖥️',
    nvidia_nim: '🎮',
    azure_openai: '☁️',
    mistral: '🌊',
    together_ai: '🤝',
    deepseek: '🔍',
    cohere: '🔗',
    xai: '❌',
    perplexity: '❓',
    custom: '⚙️',
  }

  return (
    <span className={`inline-flex items-center justify-center ${className}`} title={type}>
      {iconMap[type] || '🤖'}
    </span>
  )
}

export default ProviderIcon
