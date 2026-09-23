import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { CatalogueCategory } from '@/features/categories/types/category'

export interface RenameCategoryVariables {
  key: string
  label: string
}

export function renameCategory({ key, label }: RenameCategoryVariables): Promise<CatalogueCategory> {
  return apiRequest<CatalogueCategory>(`/api/categories/${encodeURIComponent(key)}`, {
    method: 'PATCH',
    body: JSON.stringify({ label }),
  })
}

export function useRenameCategory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: renameCategory,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['categories'] })
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
  })
}
