import { QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { ErrorBoundary } from '@/components/errors/error-boundary'
import { queryClient } from '@/lib/react-query'

export function AppProvider({ children }: { children: ReactNode }): React.JSX.Element {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ErrorBoundary>
  )
}
