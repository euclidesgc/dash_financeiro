import { keepPreviousData, queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { MonthSignal, MonthSignalQuery } from '@/features/expenses/types/ceiling'

export function getMonthSignal(query: MonthSignalQuery): Promise<MonthSignal> {
  const params = new URLSearchParams()
  if (query.from !== null) {
    params.set('from', query.from)
  }
  if (query.to !== null) {
    params.set('to', query.to)
  }
  return apiRequest<MonthSignal>(
    `/api/transactions/expenses/month-signal?${params.toString()}`,
  )
}

export function monthSignalQueryOptions(query: MonthSignalQuery) {
  return queryOptions({
    queryKey: ['expenses', 'month-signal', query],
    queryFn: () => getMonthSignal(query),
    placeholderData: keepPreviousData,
  })
}

export function useMonthSignal(query: MonthSignalQuery) {
  return useQuery(monthSignalQueryOptions(query))
}
