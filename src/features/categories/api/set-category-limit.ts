import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { CatalogueCategory } from '@/features/categories/types/category'

export interface SetCategoryLimitVariables {
  key: string
  monthly_limit_cents: number | null
}

export function setCategoryLimit({
  key,
  monthly_limit_cents,
}: SetCategoryLimitVariables): Promise<CatalogueCategory> {
  return apiRequest<CatalogueCategory>(`/api/categories/${encodeURIComponent(key)}/limit`, {
    method: 'PUT',
    body: JSON.stringify({ monthly_limit_cents }),
  })
}

export function useSetCategoryLimit() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: setCategoryLimit,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['categories'] })
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
  })
}
