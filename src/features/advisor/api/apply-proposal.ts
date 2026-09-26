import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import {
  refreshAfterCategoryChange,
  type ProposalActionVariables,
} from '@/features/advisor/api/proposal-cache'
import type { Proposal } from '@/features/advisor/types/advisor'

export function applyProposal({ proposalId }: ProposalActionVariables): Promise<Proposal> {
  return apiRequest<Proposal>(`/api/advisor/proposals/${String(proposalId)}/apply`, {
    method: 'POST',
  })
}

export function useApplyProposal() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: applyProposal,
    onSuccess: (proposal, { conversationId }) => {
      refreshAfterCategoryChange(queryClient, conversationId, proposal)
    },
  })
}
