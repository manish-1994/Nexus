import { apiClient } from './client'
import type { Message, Conversation, ChatRequest } from '../types/chat'
import { showError } from '../utils/toast'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

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
  ): Promise<void> {
    try {
      const response = await fetch(`${API_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      if (!response.body) {
        throw new Error('Response body is null')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let streamDone = false

      while (!streamDone) {
        const { done, value } = await reader.read()
        if (done) {
          streamDone = true
          break
        }

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
            if (parsed.error) {
              throw new Error(parsed.error)
            }
            const content = parsed.content ?? parsed
            if (typeof content === 'string') onChunk?.(content)
          } catch (parseErr) {
            if (parseErr instanceof Error && parseErr.message !== 'Unexpected token') throw parseErr
            if (typeof payload === 'string') onChunk?.(payload)
          }
        }
      }
    } catch (err) {
      showError('Failed to send message', {
        description: err instanceof Error ? err.message : 'Unknown error',
      })
      throw err
    }
  },
}
