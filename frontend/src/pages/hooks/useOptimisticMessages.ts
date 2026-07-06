import { useCallback, useRef, useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { chatApi } from '../../api/chat'
import { Message, Conversation } from '../../types/chat'
import { getProviderDisplayName, parseProviderError } from '../../utils/providerErrorParser'
import { showError, showWarning } from '../../utils/toast'

export function useOptimisticMessages(conversationId: number | null) {
  const queryClient = useQueryClient()
  const abortControllerRef = useRef<AbortController | null>(null)

  // Reactive isStreaming via cache subscription + local state
  const [isStreaming, setIsStreaming] = useState(false)

  useEffect(() => {
    if (!conversationId) {
      setIsStreaming(false)
      return
    }

    // Compute initial state
    const computeStreaming = () => {
      const messages = queryClient.getQueryData<Message[]>(['messages', conversationId]) || []
      const lastMessage = messages[messages.length - 1]
      // Only consider streaming if status is actively 'generating'.
      // Do NOT use isThinking alone — it can be stale on completed/failed messages.
      return lastMessage?.status === 'generating'
    }
    setIsStreaming(computeStreaming())

    // Subscribe to cache changes for this conversation's messages
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      if (
        event?.query?.queryKey?.[0] === 'messages' &&
        event?.query?.queryKey?.[1] === conversationId
      ) {
        setIsStreaming(computeStreaming())
      }
    })

    return () => {
      unsubscribe()
    }
  }, [conversationId, queryClient])

  const sendMessage = useCallback(async (
    content: string,
    convId: number,
    providerId: number,
    model: string,
    agentId: number | null = null,
    providerOverride?: number,
    modelOverride?: string
  ) => {
    // Cancel any outgoing fetches for this conversation's messages
    await queryClient.cancelQueries({ queryKey: ['messages', convId] })

    const userMessageId = Date.now()
    const tempAssistantId = Date.now() + 1
    
    const userMessage: Message = {
      id: userMessageId,
      conversation_id: convId,
      role: 'user',
      content,
      provider: model.split('/')[0],
      model,
      created_at: new Date().toISOString(),
      status: 'sending',
    }

    const thinkingPlaceholder: Message = {
      id: tempAssistantId,
      conversation_id: convId,
      role: 'assistant',
      content: 'Thinking...',
      provider: model.split('/')[0],
      model,
      created_at: new Date().toISOString(),
      isThinking: true,
      status: 'generating',
    }

    // Optimistically update the UI
    queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => [
      ...old,
      userMessage,
      thinkingPlaceholder
    ])

    // Update conversation sidebar optimistically
    queryClient.setQueryData<Conversation[]>(['conversations'], (old = []) => {
      return old.map(conv => {
        if (conv.id === convId) {
          return {
            ...conv,
            last_message_preview: content.slice(0, 50),
            updated_at: new Date().toISOString(),
          }
        }
        return conv
      })
    })

    // Simulate marking user message as sent
    setTimeout(() => {
      queryClient.setQueryData<Message[]>(['messages', convId], (old = []) =>
        old.map(m => m.id === userMessage.id ? { ...m, status: 'sent' } : m)
      )
    }, 300)

    let firstChunk = true
    let currentContent = ''

    abortControllerRef.current = new AbortController()

    try {
      const requestPayload = {
        conversation_id: convId,
        content,
        provider_id: providerId,
        model,
        stream: true,
        agent_id: agentId || undefined,
        provider_override: providerOverride,
        model_override: modelOverride,
      }

      await chatApi.sendMessage(requestPayload, (chunk) => {
        if (firstChunk) {
          firstChunk = false
          currentContent = chunk
          queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => {
            return old.map(m => m.id === tempAssistantId ? {
              ...m,
              content: chunk,
              isThinking: false,
              status: 'generating' as const
            } : m)
          })
        } else {
          currentContent += chunk
          queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => {
            return old.map(m => m.id === tempAssistantId ? {
              ...m,
              content: currentContent
            } : m)
          })
        }
      }, abortControllerRef.current.signal)

      // Stream completed — update temp message status via setQueryData instead of
      // invalidateQueries, to avoid the refetch race condition that can wipe the cache.
      queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => {
        return old.map(m => m.id === tempAssistantId ? {
          ...m,
          content: currentContent,
          isThinking: false,
          status: 'completed' as const
        } : m)
      })
      
      // Update conversation sidebar optimistically instead of invalidating,
      // to avoid a refetch that could race with the next message's optimistic insert
      queryClient.setQueryData<Conversation[]>(['conversations'], (old = []) => {
        return old.map(conv => {
          if (conv.id === convId) {
            return {
              ...conv,
              last_message_preview: currentContent.slice(0, 50),
              updated_at: new Date().toISOString(),
              message_count: (conv.message_count || 0) + 1,
            }
          }
          return conv
        })
      })

    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Handled by cancelStreaming
        return
      }
      // Handle error
      const providerName = getProviderDisplayName(model.split('/')[0])
      const parsed = parseProviderError(err, providerName)
      const toastType = parsed.severity === 'warning' ? showWarning : showError
      toastType(parsed.title, { description: parsed.description })
      
      queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => 
        old.map(m => m.id === tempAssistantId ? { 
          ...m, 
          content: currentContent || 'Unable to generate a response.', 
          isThinking: false, 
          streamError: parsed.title, 
          status: 'failed' 
        } : m)
      )
      queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => 
        old.map(m => m.id === userMessage.id ? { ...m, status: 'failed' } : m)
      )
    } finally {
      abortControllerRef.current = null
    }
  }, [queryClient])

  const cancelStreaming = useCallback((convId: number) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      
      queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => 
        old.map(m => (m.status === 'generating' || m.isThinking) ? { 
          ...m, 
          status: 'completed',
          isThinking: false
        } : m)
      )
    }
  }, [queryClient])

  const retryMessage = useCallback(async (
    convId: number,
    providerId: number,
    model: string,
    agentId: number | null = null,
    providerOverride?: number,
    modelOverride?: string
  ) => {
    const messages = queryClient.getQueryData<Message[]>(['messages', convId]) || []
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user')
    if (!lastUserMsg) return
    
    // Remove the failed assistant message
    queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => {
      const msgs = [...old]
      if (msgs.length > 0 && msgs[msgs.length - 1].role === 'assistant' && msgs[msgs.length - 1].status === 'failed') {
        msgs.pop()
      }
      return msgs
    })

    await sendMessage(lastUserMsg.content, convId, providerId, model, agentId, providerOverride, modelOverride)
  }, [queryClient, sendMessage])

  return {
    sendMessage,
    cancelStreaming,
    retryMessage,
    isStreaming,
  }
}