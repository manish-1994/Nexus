/**
 * Centralized provider error parser.
 * Translates provider-specific errors into user-friendly messages.
 * The rest of the application must never parse provider errors directly.
 */

export interface ParsedProviderError {
  title: string
  description: string
  severity: 'error' | 'warning' | 'info'
  canRetry: boolean
  canSwitchProvider: boolean
  suggestedAction?: string
}

const CREDIT_PATTERNS = [
  /insufficient\s+credits?/i,
  /payment\s+required/i,
  /402\s+payment/i,
  /credit\s+balance/i,
  /billing/i,
  /quota\s+exceeded/i,
  /insufficient_quota/i,
  /resource_exhausted/i,
  /rate\s+limit/i,
  /429/i,
  /too\s+many\s+requests/i,
]

const AUTH_PATTERNS = [
  /invalid\s+api\s+key/i,
  /authentication\s+failed/i,
  /401/i,
  /403/i,
  /unauthorized/i,
  /forbidden/i,
  /invalid\s+credentials/i,
]

const MODEL_PATTERNS = [
  /model\s+not\s+found/i,
  /unknown\s+model/i,
  /invalid\s+model/i,
  /model\s+unavailable/i,
  /no\s+such\s+model/i,
]

const CONTEXT_PATTERNS = [
  /context\s+too\s+large/i,
  /maximum\s+context\s+length/i,
  /token\s+limit/i,
  /prompt\s+too\s+long/i,
]

const PROVIDER_OFFLINE_PATTERNS = [
  /provider\s+unavailable/i,
  /unable\s+to\s+reach/i,
  /connection\s+refused/i,
  /network\s+error/i,
  /econnrefused/i,
  /timeout/i,
  /provider\s+offline/i,
]

function matchesAny(text: string, patterns: RegExp[]): boolean {
  return patterns.some((p) => p.test(text))
}

export function parseProviderError(
  rawError: unknown,
  providerName?: string,
): ParsedProviderError {
  const providerLabel = providerName || 'Provider'
  const text = typeof rawError === 'string' ? rawError : rawError instanceof Error ? rawError.message : JSON.stringify(rawError)

  // Check for credit/quota issues
  if (matchesAny(text, CREDIT_PATTERNS)) {
    return {
      title: `${providerLabel} — Insufficient Credits`,
      description: `Your ${providerLabel} account has insufficient credits or quota exceeded. Please recharge your account or select another provider.`,
      severity: 'warning',
      canRetry: false,
      canSwitchProvider: true,
      suggestedAction: 'switch_provider',
    }
  }

  // Check for auth issues
  if (matchesAny(text, AUTH_PATTERNS)) {
    return {
      title: `${providerLabel} — Authentication Failed`,
      description: `Invalid API Key. Update the provider credentials in Settings.`,
      severity: 'error',
      canRetry: false,
      canSwitchProvider: true,
      suggestedAction: 'update_credentials',
    }
  }

  // Check for model not found
  if (matchesAny(text, MODEL_PATTERNS)) {
    return {
      title: 'Unknown Model',
      description: 'Selected model is unavailable. Refresh the model list or choose another model.',
      severity: 'error',
      canRetry: false,
      canSwitchProvider: true,
      suggestedAction: 'refresh_models',
    }
  }

  // Check for context too large
  if (matchesAny(text, CONTEXT_PATTERNS)) {
    return {
      title: 'Context Too Large',
      description: 'Prompt exceeds model context window. Try shortening your message or clearing the conversation history.',
      severity: 'warning',
      canRetry: false,
      canSwitchProvider: false,
    }
  }

  // Check for provider offline
  if (matchesAny(text, PROVIDER_OFFLINE_PATTERNS)) {
    return {
      title: `${providerLabel} — Provider Unavailable`,
      description: `Unable to reach ${providerLabel}. The provider may be offline or unreachable.`,
      severity: 'error',
      canRetry: true,
      canSwitchProvider: true,
      suggestedAction: 'switch_provider',
    }
  }

  // Generic streaming failure
  return {
    title: 'Streaming Failed',
    description: text || 'An unexpected error occurred during streaming.',
    severity: 'error',
    canRetry: true,
    canSwitchProvider: true,
  }
}

export function getProviderDisplayName(type: string): string {
  const names: Record<string, string> = {
    openrouter: 'OpenRouter',
    groq: 'Groq',
    ollama: 'Ollama',
    gemini: 'Gemini',
    lmstudio: 'LM Studio',
    openai_compatible: 'OpenAI Compatible',
  }
  return names[type] || type
}
