import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { ApplyToSimilarResponse } from '@/features/expenses/types/expense'

export interface ApplyToSimilarVariables {
  id: number
  category: string | null
}

export function applyCategoryToSimilar({
  id,
  category,
}: ApplyToSimilarVariables): Promise<ApplyToSimilarResponse> {
  return apiRequest<ApplyToSimilarResponse>(
    `/api/transactions/${String(id)}/category/apply-to-similar`,
    {
      method: 'POST',
      body: JSON.stringify({ category }),
    },
  )
}

export function useApplyCategoryToSimilar() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: applyCategoryToSimilar,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
      void queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
  })
}
