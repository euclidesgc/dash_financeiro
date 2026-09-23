import { QueryClient } from '@tanstack/react-query'
import { ApiError } from '@/lib/api-client'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (count, error) => !(error instanceof ApiError && error.status === 401) && count < 3,
    },
  },
})
