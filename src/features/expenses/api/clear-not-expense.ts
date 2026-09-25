import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { Expense } from '@/features/expenses/types/expense'

export function clearNotExpense(id: number): Promise<Expense> {
  return apiRequest<Expense>(`/api/transactions/${String(id)}/not-expense`, {
    method: 'DELETE',
  })
}

export function useClearNotExpense() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: clearNotExpense,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
  })
}
