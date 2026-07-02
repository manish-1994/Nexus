import { create } from 'zustand'
import { chatApi } from '../api/chat'
import type { Message, Conversation } from '../types/chat'
import { showError, showSuccess } from '../utils/toast'

interface ChatState {
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  streamingContent: string
  error: string | null
  fetchConversations: () => Promise<void>
  fetchMessages: (conversationId: number) => Promise<void>
  sendMessage: (conversationId: number, content: string, providerId: number, model: string) => Promise<void>
  stopStreaming: () => void
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
    set({ isLoading: true, isStreaming: true, streamingContent: '', error: null })

    try {
      await chatApi.sendMessage({
        conversation_id: conversationId,
        content,
        provider_id: providerId,
        model,
        stream: true,
      }, (chunk) => {
        set((state) => ({
          streamingContent: state.streamingContent + chunk,
        }))
      })

      const finalContent = get().streamingContent
      if (finalContent) {
        set((state) => ({
          messages: [
            ...state.messages,
            {
              id: Date.now(),
              role: 'assistant',
              content: finalContent,
              provider: model.split('/')[0],
              model,
              created_at: new Date().toISOString(),
            },
          ],
          isLoading: false,
          isStreaming: false,
          streamingContent: '',
        }))
        showSuccess('Message sent')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to send message'
      showError('Failed to send message', { description: message })
      set({
        error: message,
        isLoading: false,
        isStreaming: false,
        streamingContent: '',
      })
    }
  },

  stopStreaming: () => {
    set({ isStreaming: false, isLoading: false })
  },

  setCurrentConversation: (conversation) => {
    set({ currentConversation: conversation })
  },

  clearError: () => {
    set({ error: null })
  },
}))
