import { queryOptions, useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { Navigate } from 'react-router'
import { paths } from '@/config/paths'
import { Button } from '@/components/ui/button'
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
})

export function useUser() {
  return useQuery(meQueryOptions)
}

export function ProtectedRoute({ children }: { children: ReactNode }): React.JSX.Element {
  const { isPending, isError, isFetching, data, refetch } = useUser()

  if (isPending) {
    return (
      <p role="status" className="mt-6 text-gray-600">
        Carregando…
      </p>
    )
  }

  if (isError) {
    return (
      <main className="mx-auto max-w-2xl p-8">
        <div role="alert" className="mt-6 rounded-md border border-red-200 bg-red-50 p-4">
          <p className="text-red-800">Não foi possível confirmar a sua sessão.</p>
          <div className="mt-4">
            <Button
              variant="danger"
              disabled={isFetching}
              onClick={() => {
                void refetch()
              }}
            >
              Tentar de novo
            </Button>
          </div>
        </div>
      </main>
    )
  }

  if (!data) {
    return <Navigate to={paths.login} replace />
  }

  return <>{children}</>
}
