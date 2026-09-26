export type AdvisorProvider = 'anthropic' | 'gemini'

export interface AdvisorStatus {
  available: boolean
  provider: AdvisorProvider | null
  model: string | null
  message: string | null
}

export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export interface ConversationsResponse {
  conversations: Conversation[]
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
  created_at: string
  provider: string | null
  tools: string[]
}

export interface ConversationDetail {
  conversation: Conversation
  messages: ChatMessage[]
}

export interface MessagesResponse {
  messages: ChatMessage[]
}
