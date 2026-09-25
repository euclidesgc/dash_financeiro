import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { CatalogueCategory } from '@/features/categories/types/category'
import type { CategoryLabelInput } from '@/features/categories/types/category-label-schema'

export function createCategory({ label }: CategoryLabelInput): Promise<CatalogueCategory> {
  return apiRequest<CatalogueCategory>('/api/categories', {
    method: 'POST',
    body: JSON.stringify({ label }),
  })
}

export function useCreateCategory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createCategory,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['categories'] })
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
  })
}
