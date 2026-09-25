import { keepPreviousData, queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { CategoryTotalsQuery, CategoryTotalsResponse } from '@/features/expenses/types/expense'

export function getCategoryTotals(query: CategoryTotalsQuery): Promise<CategoryTotalsResponse> {
  const params = new URLSearchParams()
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
  return apiRequest<CategoryTotalsResponse>(
    `/api/transactions/expenses/by-category?${params.toString()}`,
  )
}

export function categoryTotalsQueryOptions(query: CategoryTotalsQuery) {
  return queryOptions({
    queryKey: ['expenses', 'by-category', query],
    queryFn: () => getCategoryTotals(query),
    placeholderData: keepPreviousData,
  })
}

export function useCategoryTotals(query: CategoryTotalsQuery) {
  return useQuery(categoryTotalsQueryOptions(query))
}
