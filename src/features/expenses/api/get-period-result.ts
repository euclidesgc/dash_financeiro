import { keepPreviousData, queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { PeriodResultQuery, PeriodResultResponse } from '@/features/expenses/types/expense'

export function getPeriodResult(query: PeriodResultQuery): Promise<PeriodResultResponse> {
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
  return apiRequest<PeriodResultResponse>(
    `/api/transactions/expenses/period-result?${params.toString()}`,
  )
}

export function periodResultQueryOptions(query: PeriodResultQuery) {
  return queryOptions({
    queryKey: ['expenses', 'period-result', query],
    queryFn: () => getPeriodResult(query),
    placeholderData: keepPreviousData,
  })
}

export function usePeriodResult(query: PeriodResultQuery) {
  return useQuery(periodResultQueryOptions(query))
}
