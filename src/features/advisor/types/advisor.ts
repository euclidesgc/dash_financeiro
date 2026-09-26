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

export type ProposalStatus = 'pending' | 'applied' | 'discarded' | 'undone'

export interface ProposalItem {
  transaction_id: number
  date: string
  description: string | null
  amount_cents: number
  from_category: string | null
  to_category: string
}

export interface Proposal {
  id: number
  status: ProposalStatus
  target_category: string
  created_at: string
  applied_at: string | null
  discarded_at: string | null
  undone_at: string | null
  undo_skipped: number | null
  total_cents: number
  items: ProposalItem[]
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
  created_at: string
  provider: string | null
  tools: string[]
  proposals: Proposal[]
}

export interface ConversationDetail {
  conversation: Conversation
  messages: ChatMessage[]
}

export interface MessagesResponse {
  messages: ChatMessage[]
}
