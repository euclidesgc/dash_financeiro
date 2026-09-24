import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { Expense, NotExpenseReason } from '@/features/expenses/types/expense'

export interface SetNotExpenseVariables {
  id: number
  reason: NotExpenseReason
}

export function setNotExpense({ id, reason }: SetNotExpenseVariables): Promise<Expense> {
  return apiRequest<Expense>(`/api/transactions/${String(id)}/not-expense`, {
    method: 'PUT',
    body: JSON.stringify({ reason }),
  })
}

export function useSetNotExpense() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: setNotExpense,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
  })
}
