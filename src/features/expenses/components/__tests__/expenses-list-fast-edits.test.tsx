import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { flushSync } from 'react-dom'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { expect, test, vi } from 'vitest'

import { ExpensesList } from '@/features/expenses/components/expenses-list'

function renderExpensesRoute(route: string) {
  const router = createMemoryRouter([{ path: '/expenses', element: <ExpensesList /> }], {
    initialEntries: [route],
  })
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider
        router={router}
        flushSync={(update) => {
          flushSync(update)
        }}
      />
    </QueryClientProvider>,
  )
  return router
}

// Reason: the act scope holds back every non-sync render until it ends, which
// is the window the browser opens between a navigation updating the URL and
// React rendering it. A second edit inside that window must still see the first.
async function editInsideOneRender(first: () => void, firstLands: () => void, second: () => void) {
  await act(async () => {
    first()
    await vi.waitFor(firstLands)
    second()
  })
}

test('an end date typed before the start date renders keeps the start date', async () => {
  const router = renderExpensesRoute('/expenses?month=2026-07')
  await screen.findByRole('list')

  await editInsideOneRender(
    () => {
      fireEvent.change(screen.getByLabelText('De', { exact: true }), {
        target: { value: '2026-07-10' },
      })
    },
    () => {
      expect(router.state.location.search).toContain('from=2026-07-10')
    },
    () => {
      fireEvent.change(screen.getByLabelText('Até', { exact: true }), {
        target: { value: '2026-07-20' },
      })
    },
  )

  expect(router.state.location.search).toBe('?from=2026-07-10&to=2026-07-20')
})

test('a sort chosen before the account filter renders keeps the account', async () => {
  const router = renderExpensesRoute('/expenses?period=all')
  await screen.findByRole('list')
  const accountSelect = screen.getByLabelText('Conta', { exact: true })
  await vi.waitFor(() => {
    expect(accountSelect.querySelectorAll('option').length).toBeGreaterThan(1)
  })
  const accountId = accountSelect.querySelectorAll('option')[1].value

  await editInsideOneRender(
    () => {
      fireEvent.change(accountSelect, { target: { value: accountId } })
    },
    () => {
      expect(router.state.location.search).toContain(`account=${accountId}`)
    },
    () => {
      fireEvent.change(screen.getByLabelText('Ordenar por'), { target: { value: 'amount' } })
    },
  )

  const search = new URLSearchParams(router.state.location.search)
  expect(search.get('account')).toBe(accountId)
  expect(search.get('sort')).toBe('amount')
})
