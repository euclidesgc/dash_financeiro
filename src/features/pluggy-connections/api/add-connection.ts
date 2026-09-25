import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { PluggyConnection } from '@/features/pluggy-connections/types/pluggy-connection'
import type { ItemIdInput } from '@/features/pluggy-connections/types/item-id-schema'

export function addConnection({ itemId }: ItemIdInput): Promise<PluggyConnection> {
  return apiRequest<PluggyConnection>('/api/pluggy-connections', {
    method: 'POST',
    body: JSON.stringify({ item_id: itemId }),
  })
}

export function useAddConnection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: addConnection,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['pluggy-connections'] })
    },
  })
}
