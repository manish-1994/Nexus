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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-2xl flex flex-col overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Test Console: {agent.name}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4 space-y-4 flex-1 overflow-y-auto">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Test Message
            </label>
            <textarea
              className="w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 dark:text-white resize-none"
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
                className="rounded"
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Live Streaming</span>
            </label>

            <button
              onClick={handleTest}
              disabled={isTesting || !message.trim()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg disabled:opacity-50 transition-colors"
            >
              {isTesting ? (isStreaming ? 'Streaming...' : 'Running...') : 'Run Test'}
            </button>

            {isStreaming && (
              <button
                onClick={handleStopStreaming}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
              >
                Stop
              </button>
            )}
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-sm rounded-lg border border-red-200 dark:border-red-800">
              {error}
            </div>
          )}

          {(result || streamedResponse) && (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 p-2 rounded-lg">
                <div>
                  Provider:{' '}
                  <span className="font-medium text-gray-900 dark:text-gray-200">
                    {provider?.name || result?.provider_id || 'Default'}
                  </span>
                </div>
                <div>
                  Model:{' '}
                  <span className="font-medium text-gray-900 dark:text-gray-200">
                    {result?.model || 'Default'}
                  </span>
                </div>
                {result?.latency_ms && (
                  <div>
                    Latency:{' '}
                    <span className="font-medium text-gray-900 dark:text-gray-200">
                      {result.latency_ms}ms
                    </span>
                  </div>
                )}
                {result?.tokens_used !== undefined && result.tokens_used !== null && (
                  <div>
                    Tokens:{' '}
                    <span className="font-medium text-gray-900 dark:text-gray-200">
                      {result.tokens_used}
                    </span>
                  </div>
                )}
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Response</h3>
                <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap max-h-96 overflow-y-auto">
                  {streamedResponse || result?.response}
                  {isStreaming && (
                    <span className="inline-block w-2 h-4 ml-1 bg-blue-600 animate-pulse" />
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
