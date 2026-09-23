import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { BalancesResponse } from '@/features/accounts/types/account-balance'

export function getBalances(): Promise<BalancesResponse> {
  return apiRequest<BalancesResponse>('/api/accounts/balances')
}

export const balancesQueryOptions = queryOptions({
  queryKey: ['accounts', 'balances'],
  queryFn: getBalances,
})

export function useBalances() {
  return useQuery(balancesQueryOptions)
}
