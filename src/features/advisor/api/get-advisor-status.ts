import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import { advisorKeys } from '@/features/advisor/api/query-keys'
import type { AdvisorStatus } from '@/features/advisor/types/advisor'

export function getAdvisorStatus(): Promise<AdvisorStatus> {
  return apiRequest<AdvisorStatus>('/api/advisor/status')
}

export function advisorStatusQueryOptions() {
  return queryOptions({ queryKey: advisorKeys.status, queryFn: getAdvisorStatus })
}

export function useAdvisorStatus() {
  return useQuery(advisorStatusQueryOptions())
}
