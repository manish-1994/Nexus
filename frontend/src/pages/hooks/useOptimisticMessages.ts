import { useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { chatApi } from '../../api/chat'
import { Message, Conversation } from '../../types/chat'
import { getProviderDisplayName, parseProviderError } from '../../utils/providerErrorParser'
import { showError, showWarning } from '../../utils/toast'

export function useOptimisticMessages(conversationId: number | null) {
  const queryClient = useQueryClient()
  const abortControllerRef = useRef<AbortController | null>(null)

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
      await chatApi.sendMessage({
        conversation_id: convId,
        content,
        provider_id: providerId,
        model,
        stream: true,
        agent_id: agentId || undefined,
        provider_override: providerOverride,
        model_override: modelOverride,
      }, (chunk) => {
        if (firstChunk) {
          firstChunk = false
          currentContent = chunk
          queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => 
            old.map(m => m.id === tempAssistantId ? { 
              ...m, 
              content: chunk, 
              isThinking: false, 
              status: 'generating' 
            } : m)
          )
        } else {
          currentContent += chunk
          queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => 
            old.map(m => m.id === tempAssistantId ? { 
              ...m, 
              content: currentContent 
            } : m)
          )
        }
      }, abortControllerRef.current.signal)

      // Stream completed
      queryClient.setQueryData<Message[]>(['messages', convId], (old = []) => 
        old.map(m => m.id === tempAssistantId ? { 
          ...m, 
          status: 'completed' 
        } : m)
      )
      
      // Invalidate query to get real IDs from the backend
      queryClient.invalidateQueries({ queryKey: ['messages', convId] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })

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

  const messages = (conversationId ? queryClient.getQueryData<Message[]>(['messages', conversationId]) : []) || []
  const lastMessage = messages[messages.length - 1]
  const isStreaming = lastMessage?.status === 'generating' || lastMessage?.isThinking === true

  return {
    sendMessage,
    cancelStreaming,
    retryMessage,
    isStreaming,
  }
}
