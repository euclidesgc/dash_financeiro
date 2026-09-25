import { keepPreviousData, queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { ExpensesQuery, ExpensesResponse } from '@/features/expenses/types/expense'

export const PAGE_SIZE = 20

export function getExpenses(query: ExpensesQuery): Promise<ExpensesResponse> {
  const params = new URLSearchParams({
    page: String(query.page),
    page_size: String(PAGE_SIZE),
    sort: query.sort,
    order: query.order,
  })
  if (query.from !== null) {
    params.set('from', query.from)
  }
  if (query.to !== null) {
    params.set('to', query.to)
  }
  if (query.account !== null) {
    params.set('account_id', query.account)
  }
  if (query.search !== null) {
    params.set('q', query.search)
  }
  return apiRequest<ExpensesResponse>(`/api/transactions/expenses?${params.toString()}`)
}

export function expensesQueryOptions(query: ExpensesQuery) {
  return queryOptions({
    queryKey: ['expenses', query],
    queryFn: () => getExpenses(query),
    placeholderData: keepPreviousData,
  })
}

export function useExpenses(query: ExpensesQuery) {
  return useQuery(expensesQueryOptions(query))
}
