import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import { categoriesQueryKey } from '@/hooks/use-categories'
import type { Category } from '@/types/category'

export interface RenameCategoryVariables {
  key: string
  label: string
}

export function renameCategory({ key, label }: RenameCategoryVariables): Promise<Category> {
  return apiRequest<Category>(`/api/categories/${encodeURIComponent(key)}`, {
    method: 'PATCH',
    body: JSON.stringify({ label }),
  })
}

export function useRenameCategory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: renameCategory,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: categoriesQueryKey })
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
  })
}
