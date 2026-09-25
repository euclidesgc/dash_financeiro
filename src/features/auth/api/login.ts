import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { LoginInput } from '@/features/auth/types/login-schema'

export async function login(input: LoginInput): Promise<void> {
  await apiRequest('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function useLogin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: login,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['auth', 'me'] }),
  })
}
