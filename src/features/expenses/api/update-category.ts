import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { CategoryUpdateBody, Expense } from '@/features/expenses/types/expense'

export interface UpdateCategoryVariables {
  id: number
  body: CategoryUpdateBody
}

export function updateCategory({ id, body }: UpdateCategoryVariables): Promise<Expense> {
  return apiRequest<Expense>(`/api/transactions/${String(id)}/category`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function useUpdateCategory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updateCategory,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['expenses'] }),
  })
}
