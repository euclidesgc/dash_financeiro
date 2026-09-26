import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import { advisorKeys } from '@/features/advisor/api/query-keys'
import type { ConversationsResponse } from '@/features/advisor/types/advisor'

export function getConversations(): Promise<ConversationsResponse> {
  return apiRequest<ConversationsResponse>('/api/advisor/conversations')
}

export function conversationsQueryOptions() {
  return queryOptions({ queryKey: advisorKeys.conversations, queryFn: getConversations })
}

export function useConversations({ enabled }: { enabled: boolean }) {
  return useQuery({ ...conversationsQueryOptions(), enabled })
}
