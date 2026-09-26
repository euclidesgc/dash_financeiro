import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import { advisorKeys } from '@/features/advisor/api/query-keys'
import type {
  Conversation,
  ConversationDetail,
  MessagesResponse,
} from '@/features/advisor/types/advisor'

export interface SendQuestionInput {
  conversationId: number | null
  text: string
}

export interface SendQuestionResult {
  conversationId: number
  messages: MessagesResponse['messages']
}

export function createConversation(): Promise<Conversation> {
  return apiRequest<Conversation>('/api/advisor/conversations', { method: 'POST' })
}

export async function sendQuestion({
  conversationId,
  text,
}: SendQuestionInput): Promise<SendQuestionResult> {
  const id = conversationId ?? (await createConversation()).id
  const response = await apiRequest<MessagesResponse>(
    `/api/advisor/conversations/${String(id)}/messages`,
    { method: 'POST', body: JSON.stringify({ text }) },
  )
  return { conversationId: id, messages: response.messages }
}

export function useSendQuestion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: sendQuestion,
    onSuccess: ({ conversationId, messages }) => {
      queryClient.setQueryData<ConversationDetail>(
        advisorKeys.conversation(conversationId),
        (current) =>
          current
            ? { ...current, messages: [...current.messages, ...messages] }
            : {
                conversation: { id: conversationId, title: '', created_at: '', updated_at: '' },
                messages,
              },
      )
      void queryClient.invalidateQueries({ queryKey: advisorKeys.conversation(conversationId) })
      void queryClient.invalidateQueries({ queryKey: advisorKeys.conversations })
    },
  })
}
