import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import { categoriesQueryKey } from '@/hooks/use-categories'
import type { Category } from '@/types/category'

export interface SetCategoryLimitVariables {
  key: string
  monthly_limit_cents: number | null
}

export function setCategoryLimit({
  key,
  monthly_limit_cents,
}: SetCategoryLimitVariables): Promise<Category> {
  return apiRequest<Category>(`/api/categories/${encodeURIComponent(key)}/limit`, {
    method: 'PUT',
    body: JSON.stringify({ monthly_limit_cents }),
  })
}

export function useSetCategoryLimit() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: setCategoryLimit,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: categoriesQueryKey })
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
  })
}
