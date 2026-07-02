import { apiClient } from './client'
import type { Message, Conversation, ChatRequest } from '../types/chat'
import { showError } from '../utils/toast'

export const chatApi = {
  async getConversations(): Promise<Conversation[]> {
    const response = await apiClient.get('/conversations')
    return response.data
  },

  async createConversation(data: { title?: string }): Promise<Conversation> {
    const response = await apiClient.post('/conversations', data)
    return response.data
  },

  async getConversation(id: number): Promise<Conversation> {
    const response = await apiClient.get(`/conversations/${id}`)
    return response.data
  },

  async updateConversation(id: number, data: { title?: string }): Promise<Conversation> {
    const response = await apiClient.put(`/conversations/${id}`, data)
    return response.data
  },

  async deleteConversation(id: number): Promise<void> {
    await apiClient.delete(`/conversations/${id}`)
  },

  async getMessages(conversationId: number): Promise<Message[]> {
    const response = await apiClient.get(`/conversations/${conversationId}/messages`)
    return response.data
  },

  async sendMessage(
    data: ChatRequest,
    onChunk?: (chunk: string) => void
  ): Promise<ReadableStream<Uint8Array> | null> {
    try {
      const response = await apiClient.post('/chat', data, {
        responseType: 'stream',
      })

      if (!response.data) return null

      const reader = response.data.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || !trimmed.startsWith('data: ')) continue
          const payload = trimmed.slice(6)
          if (payload === '[DONE]') continue
          try {
            const parsed = JSON.parse(payload)
            const content = parsed.content ?? parsed
            if (typeof content === 'string') onChunk?.(content)
          } catch {
            if (typeof payload === 'string') onChunk?.(payload)
          }
        }
      }

      return null
    } catch (err) {
      showError('Failed to send message', {
        description: err instanceof Error ? err.message : 'Unknown error',
      })
      throw err
    }
  },
}
