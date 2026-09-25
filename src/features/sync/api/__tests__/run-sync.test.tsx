import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { expect, test } from 'vitest'

import { useRunSync } from '@/features/sync/api/run-sync'
import { fakeSyncStatus } from '@/testing/mocks/handlers'
import { server } from '@/testing/mocks/server'

const bankDataKeys = [
  ['accounts', 'balances'],
  ['expenses', { page: 1 }],
  ['expenses', 'accounts'],
  ['expenses', 'by-category', {}],
  ['expenses', 'period-result', {}],
  ['expenses', 'month-signal', {}],
  ['transactions', 7, 'similar'],
  ['categories'],
  ['pluggy-connections'],
] as const

function renderRunSync() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  for (const key of bankDataKeys) {
    queryClient.setQueryData(key, { before: 'sync' })
  }
  queryClient.setQueryData(['auth', 'me'], { login: 'dono' })

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  const { result } = renderHook(() => useRunSync(), { wrapper })

  return { queryClient, result }
}

test('marks every view built from bank data as stale after a sync', async () => {
  const { queryClient, result } = renderRunSync()

  act(() => {
    result.current.mutate()
  })
  await waitFor(() => {
    expect(result.current.isSuccess).toBe(true)
  })

  for (const key of bankDataKeys) {
    expect(queryClient.getQueryState(key)?.isInvalidated, JSON.stringify(key)).toBe(true)
  }
})

test('keeps the signed-in user and stores the returned sync status', async () => {
  const { queryClient, result } = renderRunSync()

  act(() => {
    result.current.mutate()
  })
  await waitFor(() => {
    expect(result.current.isSuccess).toBe(true)
  })

  expect(queryClient.getQueryState(['auth', 'me'])?.isInvalidated).toBe(false)
  expect(queryClient.getQueryData(['sync', 'status'])).toEqual(fakeSyncStatus)
  expect(queryClient.getQueryState(['sync', 'status'])?.isInvalidated).toBe(false)
})

test.each([409, 503, 500])('leaves the bank data alone when the sync answers %i', async (status) => {
  server.use(http.post('/api/sync/run', () => HttpResponse.json({ detail: 'x' }, { status })))
  const { queryClient, result } = renderRunSync()
  queryClient.setQueryData(['sync', 'status'], fakeSyncStatus)

  act(() => {
    result.current.mutate()
  })
  await waitFor(() => {
    expect(result.current.isError).toBe(true)
  })

  for (const key of bankDataKeys) {
    expect(queryClient.getQueryState(key)?.isInvalidated, JSON.stringify(key)).toBe(false)
  }
  expect(queryClient.getQueryState(['sync', 'status'])?.isInvalidated).toBe(true)
})
