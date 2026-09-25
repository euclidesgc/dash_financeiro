import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { SimilarCountResponse } from '@/features/expenses/types/expense'

export function getSimilarCount(id: number): Promise<SimilarCountResponse> {
  return apiRequest<SimilarCountResponse>(`/api/transactions/${String(id)}/similar`)
}

export function similarCountQueryOptions(id: number) {
  return queryOptions({
    queryKey: ['transactions', id, 'similar'],
    queryFn: () => getSimilarCount(id),
    // Reason: the count changes with every apply and every sync, and the key stays outside
    // the ['expenses'] prefix so invalidating the list does not refetch counts of closed offers.
    staleTime: 0,
    gcTime: 0,
  })
}

export function useSimilarCount(id: number) {
  return useQuery(similarCountQueryOptions(id))
}
