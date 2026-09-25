import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'

export function deleteCategory({ key }: { key: string }): Promise<void> {
  return apiRequest<undefined>(`/api/categories/${encodeURIComponent(key)}`, { method: 'DELETE' })
}

export function useDeleteCategory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['categories'] })
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
  })
}
