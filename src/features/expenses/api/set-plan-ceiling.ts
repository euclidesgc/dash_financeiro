import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { PlanCeiling } from '@/features/expenses/types/ceiling'

export interface SetPlanCeilingVariables {
  monthly_ceiling_cents: number | null
}

export function setPlanCeiling({
  monthly_ceiling_cents,
}: SetPlanCeilingVariables): Promise<PlanCeiling> {
  return apiRequest<PlanCeiling>('/api/plan/ceiling', {
    method: 'PUT',
    body: JSON.stringify({ monthly_ceiling_cents }),
  })
}

export function useSetPlanCeiling() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: setPlanCeiling,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plan'] })
      void queryClient.invalidateQueries({ queryKey: ['expenses'] })
    },
  })
}
