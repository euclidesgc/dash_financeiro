import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { PlanCeiling } from '@/features/expenses/types/ceiling'

export function getPlanCeiling(): Promise<PlanCeiling> {
  return apiRequest<PlanCeiling>('/api/plan/ceiling')
}

export function planCeilingQueryOptions() {
  return queryOptions({
    queryKey: ['plan', 'ceiling'],
    queryFn: getPlanCeiling,
  })
}

export function usePlanCeiling() {
  return useQuery(planCeilingQueryOptions())
}
