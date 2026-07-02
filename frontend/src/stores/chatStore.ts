import { create } from 'zustand'
import { chatApi } from '../api/chat'
import type { Message, Conversation } from '../types/chat'
import { showError, showSuccess, showWarning } from '../utils/toast'
import { parseProviderError, getProviderDisplayName } from '../utils/providerErrorParser'

interface ChatState {
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  streamingContent: string
  error: string | null
  retryData: { conversationId: number; content: string; providerId: number; model: string } | null
  fetchConversations: () => Promise<void>
  fetchMessages: (conversationId: number) => Promise<void>
  sendMessage: (conversationId: number, content: string, providerId: number, model: string) => Promise<void>
  retryMessage: () => Promise<void>
  cancelStreaming: () => void
  setCurrentConversation: (conversation: Conversation | null) => void
  clearError: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: '',
  error: null,
  retryData: null,

  fetchConversations: async () => {
    set({ isLoading: true, error: null })
    try {
      const data = await chatApi.getConversations()
      set({ conversations: data, isLoading: false })
    } catch (err) {
      const message = 'Failed to load conversations'
      showError(message, { description: err instanceof Error ? err.message : undefined })
      set({ error: message, isLoading: false })
    }
  },

  fetchMessages: async (conversationId) => {
    set({ isLoading: true, error: null })
    try {
      const data = await chatApi.getMessages(conversationId)
      set({ messages: data, isLoading: false })
    } catch (err) {
      const message = 'Failed to load messages'
      showError(message, { description: err instanceof Error ? err.message : undefined })
      set({ error: message, isLoading: false })
    }
  },

  sendMessage: async (conversationId, content, providerId, model) => {
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content,
      provider: model.split('/')[0],
      model,
      created_at: new Date().toISOString(),
    }
  
    const thinkingPlaceholder: Message = {
      id: Date.now() + 0.5,
      role: 'assistant',
      content: 'Thinking...',
      provider: model.split('/')[0],
      model,
      created_at: new Date().toISOString(),
      isThinking: true,
    }
  
    set((state) => ({
      messages: [...state.messages, userMessage, thinkingPlaceholder],
      isStreaming: true,
      streamingContent: '',
      error: null,
      retryData: null,
    }))
  
    let firstChunk = true
    try {
      await chatApi.sendMessage({
        conversation_id: conversationId,
        content,
        provider_id: providerId,
        model,
        stream: true,
      }, (chunk) => {
        if (firstChunk) {
          firstChunk = false
          set((state) => ({
            messages: state.messages.map((m) =>
              m.id === thinkingPlaceholder.id
                ? { ...m, content: chunk, isThinking: false }
                : m,
            ),
            streamingContent: chunk,
          }))
        } else {
          set((state) => ({
            streamingContent: state.streamingContent + chunk,
          }))
        }
      })
  
    const finalContent = get().streamingContent
    if (finalContent) {
      set((state) => ({
        messages: state.messages.map((m) =>
          m.id === thinkingPlaceholder.id
            ? { ...m, content: finalContent, isThinking: false, streamError: undefined }
            : m,
        ),
        isStreaming: false,
        streamingContent: '',
      }))
      showSuccess('Message sent')
    }
  } catch (err) {
    const providerName = getProviderDisplayName(model.split('/')[0])
    const parsed = parseProviderError(err, providerName)
    const toastType = parsed.severity === 'warning' ? showWarning : showError
    toastType(parsed.title, { description: parsed.description })
    console.error('[Chat] Provider error:', err)
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === thinkingPlaceholder.id
          ? { ...m, content: 'Unable to generate a response.', isThinking: false, streamError: parsed.title }
          : m,
      ),
      isStreaming: false,
      streamingContent: '',
      error: parsed.title,
      retryData: parsed.canRetry ? { conversationId, content, providerId, model } : null,
    }))
  }
  },

  retryMessage: async () => {
    const { retryData, messages } = get()
    if (!retryData) return
    const { conversationId, providerId, model } = retryData
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user')
    if (!lastUserMsg) return
    set({ retryData: null })
    await get().sendMessage(conversationId, lastUserMsg.content, providerId, model)
  },
  
  cancelStreaming: () => {
    set({ isStreaming: false, streamingContent: '', retryData: null })
  },

  setCurrentConversation: (conversation) => {
    set({ currentConversation: conversation })
  },

  clearError: () => {
    set({ error: null })
  },
}))
