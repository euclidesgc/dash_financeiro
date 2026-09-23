import { keepPreviousData, queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { ExpensesResponse } from '@/features/expenses/types/expense'

export const PAGE_SIZE = 20

export function getExpenses(page: number): Promise<ExpensesResponse> {
  return apiRequest<ExpensesResponse>(
    `/api/transactions/expenses?page=${String(page)}&page_size=${String(PAGE_SIZE)}`,
  )
}

export function expensesQueryOptions(page: number) {
  return queryOptions({
    queryKey: ['expenses', { page }],
    queryFn: () => getExpenses(page),
    placeholderData: keepPreviousData,
  })
}

export function useExpenses(page: number) {
  return useQuery(expensesQueryOptions(page))
}
