import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { SyncStatus } from '@/features/sync/types/sync-status'

const UNCHANGED_BY_SYNC = new Set<unknown>(['auth', 'sync'])

export function runSync(): Promise<SyncStatus> {
  return apiRequest<SyncStatus>('/api/sync/run', { method: 'POST' })
}

export function useRunSync() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: runSync,
    onSuccess: (data) => {
      queryClient.setQueryData(['sync', 'status'], data)
      // A sync rewrites transactions, accounts and connections, so every view
      // may be stale; listing the few keys it cannot touch keeps new screens
      // covered without anyone remembering this file.
      void queryClient.invalidateQueries({
        predicate: (query) => !UNCHANGED_BY_SYNC.has(query.queryKey[0]),
      })
    },
    onError: () => void queryClient.invalidateQueries({ queryKey: ['sync', 'status'] }),
  })
}
