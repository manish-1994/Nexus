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
}

export interface Conversation {
  id: number
  title: string
  user_id?: string
  created_at: string
  updated_at: string
  messages?: Message[]
}

export interface ChatRequest {
  conversation_id: number
  content: string
  provider_id: number
  model: string
  stream?: boolean
}

export interface ChatState {
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  error: string | null
}
