import type { QueryClient } from '@tanstack/react-query'
import { categoriesQueryKey } from '@/hooks/use-categories'
import { advisorKeys } from '@/features/advisor/api/query-keys'
import type { ConversationDetail, Proposal } from '@/features/advisor/types/advisor'

export interface ProposalActionVariables {
  conversationId: number
  proposalId: number
}

export function replaceProposal(
  queryClient: QueryClient,
  conversationId: number,
  proposal: Proposal,
): void {
  queryClient.setQueryData<ConversationDetail>(advisorKeys.conversation(conversationId), (current) =>
    current
      ? {
          ...current,
          messages: current.messages.map((message) => ({
            ...message,
            proposals: message.proposals.map((item) => (item.id === proposal.id ? proposal : item)),
          })),
        }
      : current,
  )
}

export function refreshAfterCategoryChange(
  queryClient: QueryClient,
  conversationId: number,
  proposal: Proposal,
): void {
  replaceProposal(queryClient, conversationId, proposal)
  void queryClient.invalidateQueries({ queryKey: ['expenses'] })
  void queryClient.invalidateQueries({ queryKey: categoriesQueryKey })
}
