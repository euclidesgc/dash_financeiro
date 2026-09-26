import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import {
  replaceProposal,
  type ProposalActionVariables,
} from '@/features/advisor/api/proposal-cache'
import type { Proposal } from '@/features/advisor/types/advisor'

export function discardProposal({ proposalId }: ProposalActionVariables): Promise<Proposal> {
  return apiRequest<Proposal>(`/api/advisor/proposals/${String(proposalId)}/discard`, {
    method: 'POST',
  })
}

export function useDiscardProposal() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: discardProposal,
    onSuccess: (proposal, { conversationId }) => {
      replaceProposal(queryClient, conversationId, proposal)
    },
  })
}
