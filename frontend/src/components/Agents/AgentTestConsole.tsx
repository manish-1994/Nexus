import { useState, useRef, useEffect } from 'react'
import { agentApi } from '../../services/agentApi'
import { Agent, AgentTestResponse } from '../../types/agent'
import { useProviderStore } from '../../stores/providerStore'
import { toast } from 'sonner'

interface AgentTestConsoleProps {
  agent: Agent
  onClose: () => void
}

export function AgentTestConsole({ agent, onClose }: AgentTestConsoleProps) {
  const [message, setMessage] = useState('Hello, this is a test.')
  const [isTesting, setIsTesting] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [result, setResult] = useState<AgentTestResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [streamedResponse, setStreamedResponse] = useState('')
  const [useStreaming, setUseStreaming] = useState(true)
  const providers = useProviderStore(state => state.providers)
  const streamAbortRef = useRef<boolean>(false)

  useEffect(() => {
    return () => {
      streamAbortRef.current = true
    }
  }, [])

  const handleTest = async () => {
    if (!message.trim()) {
      toast.error('Please enter a test message')
      return
    }

    setIsTesting(true)
    setError(null)
    setResult(null)
    setStreamedResponse('')
    streamAbortRef.current = false

    try {
      if (useStreaming) {
        setIsStreaming(true)
        let fullResponse = ''
        for await (const chunk of agentApi.testAgentStream(agent.id, {
          message,
          provider_id: agent.provider_id,
          model: agent.preferred_model_id ? String(agent.preferred_model_id) : undefined,
        })) {
          if (streamAbortRef.current) break
          fullResponse += chunk
          setStreamedResponse(fullResponse)
        }
        setResult({
          status: 'success',
          response: fullResponse,
          provider_id: agent.provider_id,
          model: agent.preferred_model_id ? String(agent.preferred_model_id) : undefined,
        })
      } else {
        const response = await agentApi.testAgent(agent.id, message)
        setResult(response)
        if (response.error) {
          setError(response.error)
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        const axiosError = err as { response?: { data?: { detail?: string } } }
        setError(axiosError.response?.data?.detail || err.message || 'Test failed')
      } else {
        setError('Test failed')
      }
    } finally {
      setIsTesting(false)
      setIsStreaming(false)
    }
  }

  const handleStopStreaming = () => {
    streamAbortRef.current = true
    setIsStreaming(false)
    setIsTesting(false)
  }

  const provider = providers.find(p => p.id === result?.provider_id)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-md bg-black/50">
      <div className="glass-elevated rounded-dialog shadow-elevated w-full max-w-2xl flex flex-col overflow-hidden">
        <div className="p-lg border-b border-white/5 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-text font-heading">
            Test Console: {agent.name}
          </h2>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text transition-colors duration-fast"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-lg space-y-md flex-1 overflow-y-auto">
          <div>
            <label className="block text-sm font-medium text-text mb-xs">
              Test Message
            </label>
            <textarea
              className="input-standard w-full resize-none"
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={isTesting}
            />
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={useStreaming}
                onChange={(e) => setUseStreaming(e.target.checked)}
                className="accent-accent"
              />
              <span className="text-sm font-medium text-text">Live Streaming</span>
            </label>

            <button
              onClick={handleTest}
              disabled={isTesting || !message.trim()}
              className="px-md py-sm bg-accent hover:bg-accent-dark text-white font-medium rounded-button disabled:opacity-50 transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
            >
              {isTesting ? (isStreaming ? 'Streaming...' : 'Running...') : 'Run Test'}
            </button>

            {isStreaming && (
              <button
                onClick={handleStopStreaming}
                className="px-md py-sm bg-danger hover:bg-danger/80 text-white font-medium rounded-button transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-danger/30 focus-visible:outline-none"
              >
                Stop
              </button>
            )}
          </div>

          {error && (
            <div className="p-sm bg-danger/10 text-danger text-sm rounded-input border border-danger/30">
              {error}
            </div>
          )}

          {(result || streamedResponse) && (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-md text-xs text-text-muted bg-surface/40 p-sm rounded-input">
                <div>
                  Provider:{' '}
                  <span className="font-medium text-text">
                    {provider?.name || result?.provider_id || 'Default'}
                  </span>
                </div>
                <div>
                  Model:{' '}
                  <span className="font-medium text-text">
                    {result?.model || 'Default'}
                  </span>
                </div>
                {result?.latency_ms && (
                  <div>
                    Latency:{' '}
                    <span className="font-medium text-text">
                      {result.latency_ms}ms
                    </span>
                  </div>
                )}
                {result?.tokens_used !== undefined && result.tokens_used !== null && (
                  <div>
                    Tokens:{' '}
                    <span className="font-medium text-text">
                      {result.tokens_used}
                    </span>
                  </div>
                )}
              </div>

              <div>
                <h3 className="text-sm font-medium text-text mb-sm">Response</h3>
                <div className="p-md bg-surface/40 rounded-input text-sm text-text whitespace-pre-wrap max-h-96 overflow-y-auto">
                  {streamedResponse || result?.response}
                  {isStreaming && (
                    <span className="streaming-cursor" />
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
