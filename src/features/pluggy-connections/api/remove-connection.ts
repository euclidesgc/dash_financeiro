import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'

export function removeConnection({ itemId }: { itemId: string }): Promise<void> {
  return apiRequest<undefined>(`/api/pluggy-connections/${encodeURIComponent(itemId)}`, {
    method: 'DELETE',
  })
}

export function useRemoveConnection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: removeConnection,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['pluggy-connections'] })
    },
  })
}
