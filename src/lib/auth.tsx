import { queryOptions, useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { Navigate } from 'react-router'
import { paths } from '@/config/paths'
import { ApiError, apiRequest } from '@/lib/api-client'

export interface User {
  login: string
}

export function getMe(): Promise<User> {
  return apiRequest<User>('/api/auth/me')
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
  const { isPending, error } = useUser()

  if (isPending) {
    return (
      <p role="status" className="mt-6 text-gray-600">
        Carregando…
      </p>
    )
  }

  if (error) {
    if (error instanceof ApiError && error.status === 401) {
      return <Navigate to={paths.login} replace />
    }
    throw error
  }

  return <>{children}</>
}
