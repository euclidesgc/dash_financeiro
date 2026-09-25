import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { SyncStatus } from '@/features/sync/types/sync-status'

export function getSyncStatus(): Promise<SyncStatus> {
  return apiRequest<SyncStatus>('/api/sync/status')
}

export const syncStatusQueryOptions = queryOptions({
  queryKey: ['sync', 'status'],
  queryFn: getSyncStatus,
  refetchInterval: (query) => (query.state.data?.running ? 5_000 : false),
})

export function useSyncStatus() {
  return useQuery(syncStatusQueryOptions)
}
