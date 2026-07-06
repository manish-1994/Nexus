import { useState, useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { Message } from '../../types/chat'

/**
 * AI execution phases — mirrors the lifecycle of a request through the runtime.
 * The phase drives the LiveStatusPanel, TokenStreamHUD, and ResponseTimeline.
 */
export type AIPhase =
  | 'idle'
  | 'thinking'
  | 'planning'
  | 'researching'
  | 'calling_provider'
  | 'streaming'
  | 'completed'
  | 'error'

export interface AIActivityEvent {
  id: string
  label: string
  timestamp: number
  phase: AIPhase
}

export interface AIStatusState {
  phase: AIPhase
  /** Elapsed seconds since the current execution started (0 when idle). */
  elapsed: number
  /** Tokens generated in the current/last streaming response. */
  tokens: number
  /** Tokens per second (rolling estimate) for the HUD. */
  tokensPerSecond: number
  /** Provider name for the active execution. */
  provider: string | null
  /** Model name for the active execution. */
  model: string | null
  /** Activity log entries (most recent first). */
  activity: AIActivityEvent[]
  /** Timestamp the current execution started (ms epoch). */
  startedAt: number | null
  /** Timestamp the current execution completed (ms epoch). */
  completedAt: number | null
}

const INITIAL_STATE: AIStatusState = {
  phase: 'idle',
  elapsed: 0,
  tokens: 0,
  tokensPerSecond: 0,
  provider: null,
  model: null,
  activity: [],
  startedAt: null,
  completedAt: null,
}

let eventCounter = 0
const makeEvent = (label: string, phase: AIPhase): AIActivityEvent => ({
  id: `evt-${Date.now()}-${++eventCounter}`,
  label,
  timestamp: Date.now(),
  phase,
})

/**
 * Derives the AI phase from the latest message in a conversation.
 * - A message with `isThinking` → 'thinking' (then progresses to 'planning'/'researching' via elapsed heuristics).
 * - A message with `status === 'generating'` and content → 'streaming'.
 * - A message with `status === 'generating'` and no content → 'calling_provider'.
 * - A message with `streamError` → 'error'.
 * - A completed message → 'completed' (briefly, then 'idle').
 */
function derivePhase(messages: Message[]): {
  phase: AIPhase
  tokens: number
  provider: string | null
  model: string | null
} {
  if (!messages.length) {
    return { phase: 'idle', tokens: 0, provider: null, model: null }
  }

  // Find the last assistant message (the active/completed response).
  const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant')
  if (!lastAssistant) {
    return { phase: 'idle', tokens: 0, provider: null, model: null }
  }

  if (lastAssistant.streamError) {
    return {
      phase: 'error',
      tokens: lastAssistant.tokens_used ?? 0,
      provider: lastAssistant.provider ?? null,
      model: lastAssistant.model ?? null,
    }
  }

  if (lastAssistant.isThinking) {
    return {
      phase: 'thinking',
      tokens: 0,
      provider: lastAssistant.provider ?? null,
      model: lastAssistant.model ?? null,
    }
  }

  if (lastAssistant.status === 'generating') {
    const hasContent = !!(lastAssistant.content && lastAssistant.content.trim().length > 0)
    return {
      phase: hasContent ? 'streaming' : 'calling_provider',
      tokens: lastAssistant.tokens_used ?? estimateTokens(lastAssistant.content),
      provider: lastAssistant.provider ?? null,
      model: lastAssistant.model ?? null,
    }
  }

  if (lastAssistant.status === 'completed' || lastAssistant.status === 'sent') {
    return {
      phase: 'completed',
      tokens: lastAssistant.tokens_used ?? estimateTokens(lastAssistant.content),
      provider: lastAssistant.provider ?? null,
      model: lastAssistant.model ?? null,
    }
  }

  return { phase: 'idle', tokens: 0, provider: null, model: null }
}

/** Rough token estimate (~4 chars/token) when the backend hasn't reported yet. */
function estimateTokens(content?: string): number {
  if (!content) return 0
  return Math.max(1, Math.floor(content.length / 4))
}

/**
 * Tracks the AI execution status for a given conversation by observing the
 * React Query message cache. No polling — purely reactive to cache updates.
 */
export function useAIStatus(conversationId: number | null): AIStatusState & {
  reset: () => void
} {
  const queryClient = useQueryClient()
  const [state, setState] = useState<AIStatusState>(INITIAL_STATE)
  const stateRef = useRef(state)
  stateRef.current = state

  // Track previous phase to emit activity-log transitions.
  const prevPhaseRef = useRef<AIPhase>('idle')
  // Track token count for speed calculation.
  const lastTokenCheckRef = useRef<{ tokens: number; time: number } | null>(null)
  // Elapsed timer handle.
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const pushActivity = useCallback((label: string, phase: AIPhase) => {
    setState((prev) => ({
      ...prev,
      activity: [makeEvent(label, phase), ...prev.activity].slice(0, 50),
    }))
  }, [])

  const reset = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    prevPhaseRef.current = 'idle'
    lastTokenCheckRef.current = null
    setState(INITIAL_STATE)
  }, [])

  // Subscribe to React Query cache changes for this conversation's messages.
  useEffect(() => {
    if (!conversationId) {
      reset()
      return
    }

    const queryKey = ['messages', conversationId]

    const computeFromCache = () => {
      const messages = queryClient.getQueryData<Message[]>(queryKey) || []
      const derived = derivePhase(messages)
      return derived
    }

    const applyDerived = () => {
      const derived = computeFromCache()
      setState((prev) => {
        const prevPhase = prev.phase
        const nextPhase = derived.phase

        // Compute tokens-per-second rolling estimate.
        let tokensPerSecond = prev.tokensPerSecond
        if (nextPhase === 'streaming' && derived.tokens > 0) {
          const now = Date.now()
          const last = lastTokenCheckRef.current
          if (last && now - last.time > 200) {
            const dt = (now - last.time) / 1000
            if (dt > 0) {
              const speed = (derived.tokens - last.tokens) / dt
              tokensPerSecond = speed > 0 ? Math.round(speed) : prev.tokensPerSecond
            }
            lastTokenCheckRef.current = { tokens: derived.tokens, time: now }
          } else if (!last) {
            lastTokenCheckRef.current = { tokens: derived.tokens, time: now }
          }
        }

        // Phase transition → emit activity events.
        let activity = prev.activity
        let startedAt = prev.startedAt
        let completedAt = prev.completedAt

        if (nextPhase !== prevPhase) {
          const newEvents: AIActivityEvent[] = []
          if (prevPhase === 'idle' && nextPhase === 'thinking') {
            startedAt = Date.now()
            completedAt = null
            newEvents.push(makeEvent('Request received', 'thinking'))
            newEvents.push(makeEvent('Context loaded', 'thinking'))
          } else if (nextPhase === 'calling_provider' && prevPhase === 'thinking') {
            newEvents.push(makeEvent('Provider selected', 'calling_provider'))
            newEvents.push(makeEvent('Calling provider API', 'calling_provider'))
          } else if (nextPhase === 'streaming' && prevPhase === 'calling_provider') {
            newEvents.push(makeEvent('Streaming started', 'streaming'))
          } else if (nextPhase === 'streaming' && prevPhase === 'thinking') {
            // Sometimes we jump straight from thinking to streaming.
            newEvents.push(makeEvent('Provider selected', 'calling_provider'))
            newEvents.push(makeEvent('Streaming started', 'streaming'))
          } else if (nextPhase === 'completed') {
            completedAt = Date.now()
            newEvents.push(makeEvent('Streaming finished', 'completed'))
          } else if (nextPhase === 'error') {
            newEvents.push(makeEvent('Execution failed', 'error'))
          } else if (nextPhase === 'idle' && prevPhase !== 'idle') {
            startedAt = null
            completedAt = null
          }
          if (newEvents.length) {
            activity = [...newEvents.reverse(), ...prev.activity].slice(0, 50)
          }
          prevPhaseRef.current = nextPhase
        }

        return {
          ...prev,
          phase: nextPhase,
          tokens: derived.tokens,
          tokensPerSecond,
          provider: derived.provider ?? prev.provider,
          model: derived.model ?? prev.model,
          activity,
          startedAt,
          completedAt,
        }
      })
    }

    // Initial compute.
    applyDerived()

    // Subscribe to cache changes for this query key.
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      if (event.query.queryKey[0] === 'messages' && event.query.queryKey[1] === conversationId) {
        applyDerived()
      }
    })

    return () => {
      unsubscribe()
    }
  }, [conversationId, queryClient, pushActivity, reset])

  // Elapsed timer — ticks every 100ms while an execution is active.
  useEffect(() => {
    const isActive =
      state.phase === 'thinking' ||
      state.phase === 'planning' ||
      state.phase === 'researching' ||
      state.phase === 'calling_provider' ||
      state.phase === 'streaming'

    if (!isActive) {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
      return
    }

    if (!timerRef.current && state.startedAt) {
      timerRef.current = setInterval(() => {
        setState((prev) => {
          if (!prev.startedAt) return prev
          return { ...prev, elapsed: (Date.now() - prev.startedAt) / 1000 }
        })
      }, 100)
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [state.phase, state.startedAt])

  // Auto-transition: thinking → planning → researching (heuristic by elapsed time).
  useEffect(() => {
    if (state.phase !== 'thinking' || !state.startedAt) return
    const planningTimeout = setTimeout(() => {
      setState((prev) => {
        if (prev.phase !== 'thinking') return prev
        prevPhaseRef.current = 'planning'
        return {
          ...prev,
          phase: 'planning',
          activity: [makeEvent('Planning response structure', 'planning'), ...prev.activity].slice(0, 50),
        }
      })
    }, 1200)

    const researchingTimeout = setTimeout(() => {
      setState((prev) => {
        if (prev.phase !== 'planning') return prev
        prevPhaseRef.current = 'researching'
        return {
          ...prev,
          phase: 'researching',
          activity: [makeEvent('Researching context', 'researching'), ...prev.activity].slice(0, 50),
        }
      })
    }, 2400)

    return () => {
      clearTimeout(planningTimeout)
      clearTimeout(researchingTimeout)
    }
  }, [state.phase, state.startedAt])

  // Auto-return to idle a few seconds after completion/error.
  useEffect(() => {
    if (state.phase !== 'completed' && state.phase !== 'error') return
    const timeout = setTimeout(() => {
      setState((prev) => {
        if (prev.phase !== 'completed' && prev.phase !== 'error') return prev
        prevPhaseRef.current = 'idle'
        return { ...prev, phase: 'idle', tokensPerSecond: 0 }
      })
    }, state.phase === 'error' ? 8000 : 4000)

    return () => clearTimeout(timeout)
  }, [state.phase])

  return { ...state, reset }
}
