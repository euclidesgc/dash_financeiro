import { queryOptions, useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { Navigate } from 'react-router'
import { paths } from '@/config/paths'
import { ApiError, apiRequest } from '@/lib/api-client'

export interface User {
  login: string
}

export async function getMe(): Promise<User | null> {
  try {
    return await apiRequest<User>('/api/auth/me')
  } catch (error) {
    // A 401 here is the normal answer for "nobody is signed in". Resolving it
    // replaces the cached user; as an error the stale user would survive.
    if (error instanceof ApiError && error.status === 401) {
      return null
    }
    throw error
  }
}

export const meQueryOptions = queryOptions({
  queryKey: ['auth', 'me'],
  queryFn: getMe,
  retry: false,
})

export function useUser() {
  return useQuery(meQueryOptions)
}

export function ProtectedRoute({ children }: { children: ReactNode }): React.JSX.Element {
  const { isPending, error, data } = useUser()

  if (isPending) {
    return (
      <p role="status" className="mt-6 text-gray-600">
        Carregando…
      </p>
    )
  }

  if (error) {
    throw error
  }

  if (!data) {
    return <Navigate to={paths.login} replace />
  }

  return <>{children}</>
}
