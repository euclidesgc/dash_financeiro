import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import { advisorKeys } from '@/features/advisor/api/query-keys'
import type { ConversationDetail } from '@/features/advisor/types/advisor'

export function getConversation(id: number): Promise<ConversationDetail> {
  return apiRequest<ConversationDetail>(`/api/advisor/conversations/${String(id)}`)
}

export function conversationQueryOptions(id: number) {
  return queryOptions({ queryKey: advisorKeys.conversation(id), queryFn: () => getConversation(id) })
}

export function useConversation(id: number | null) {
  return useQuery({ ...conversationQueryOptions(id ?? 0), enabled: id !== null })
}
