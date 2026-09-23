import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { ExpenseAccountsResponse } from '@/features/expenses/types/expense'

export function getAccounts(): Promise<ExpenseAccountsResponse> {
  return apiRequest<ExpenseAccountsResponse>('/api/accounts/balances')
}

export const accountsQueryOptions = queryOptions({
  queryKey: ['expenses', 'accounts'],
  queryFn: getAccounts,
})

export function useExpenseAccounts() {
  return useQuery(accountsQueryOptions)
}
