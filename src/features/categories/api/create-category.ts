import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import { categoriesQueryKey } from '@/hooks/use-categories'
import type { Category } from '@/types/category'
import type { CategoryLabelInput } from '@/features/categories/types/category-label-schema'

export function createCategory({ label }: CategoryLabelInput): Promise<Category> {
  return apiRequest<Category>('/api/categories', {
    method: 'POST',
    body: JSON.stringify({ label }),
  })
}

export function useCreateCategory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createCategory,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: categoriesQueryKey })
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
  })
}
