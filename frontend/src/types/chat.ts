export type MessageStatus = 'sending' | 'sent' | 'generating' | 'completed' | 'failed'

export interface Message {
  id: number
  conversation_id?: number
  role: 'user' | 'assistant' | 'system'
  content: string
  provider?: string
  model?: string
  tokens_used?: number
  created_at: string
  updated_at?: string
  isThinking?: boolean
  streamError?: string
  status?: MessageStatus
}

export interface Conversation {
    id: number
    title: string
    user_id?: string
    created_at: string
    updated_at: string
    messages?: Message[]
    last_message_preview?: string
    provider_name?: string
    model_name?: string
    message_count?: number
}

export interface ChatRequest {
  conversation_id: number
  content: string
  provider_id?: number
  model?: string
  stream?: boolean
  agent_id?: number
  provider_override?: number
  model_override?: string
}

export interface ChatState {
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  error: string | null
}
