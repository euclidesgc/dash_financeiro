import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { SyncStatus } from '@/features/sync/types/sync-status'

export function runSync(): Promise<SyncStatus> {
  return apiRequest<SyncStatus>('/api/sync/run', { method: 'POST' })
}

export function useRunSync() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: runSync,
    onSuccess: (data) => {
      queryClient.setQueryData(['sync', 'status'], data)
      void queryClient.invalidateQueries({ queryKey: ['accounts', 'balances'] })
    },
    onError: () => void queryClient.invalidateQueries({ queryKey: ['sync', 'status'] }),
  })
}
