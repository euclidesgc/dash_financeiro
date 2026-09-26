import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import {
  refreshAfterCategoryChange,
  type ProposalActionVariables,
} from '@/features/advisor/api/proposal-cache'
import type { Proposal } from '@/features/advisor/types/advisor'

export function undoProposal({ proposalId }: ProposalActionVariables): Promise<Proposal> {
  return apiRequest<Proposal>(`/api/advisor/proposals/${String(proposalId)}/undo`, {
    method: 'POST',
  })
}

export function useUndoProposal() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: undoProposal,
    onSuccess: (proposal, { conversationId }) => {
      refreshAfterCategoryChange(queryClient, conversationId, proposal)
    },
  })
}
