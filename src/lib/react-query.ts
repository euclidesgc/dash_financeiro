import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query'
import { ApiError } from '@/lib/api-client'
import { meQueryOptions } from '@/lib/auth'

function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401
}

export function createQueryClient(): QueryClient {
  const client = new QueryClient({
    queryCache: new QueryCache({ onError: endSessionOnUnauthorized }),
    mutationCache: new MutationCache({ onError: endSessionOnUnauthorized }),
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (count, error) => !isUnauthorized(error) && count < 3,
      },
    },
  })

  // The only place that reacts to a 401. Asking /api/auth/me again lets the
  // server confirm the session is gone; getMe then resolves null and
  // ProtectedRoute sends the app to the login page. The user query itself
  // never fails with 401, so this cannot loop.
  function endSessionOnUnauthorized(error: unknown): void {
    if (isUnauthorized(error) && client.getQueryData(meQueryOptions.queryKey)) {
      void client.invalidateQueries({ queryKey: meQueryOptions.queryKey, refetchType: 'all' })
    }
  }

  return client
}

export const queryClient = createQueryClient()
