import { http, HttpResponse, delay } from 'msw'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor, within } from '@testing-library/react'

import { CategoryTotals } from '@/features/expenses/components/category-totals'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import type { CategoryGroup, CategoryTotalsQuery } from '@/features/expenses/types/expense'

const ALL: CategoryTotalsQuery = { from: null, to: null, account: null, search: null }

function groupsOf(n: number): CategoryGroup[] {
  return Array.from({ length: n }, (_, index) => {
    const i = index + 1
    return {
      category: `Cat ${String(i)}`,
      label: `Categoria ${String(i)}`,
      count: i,
      total_cents: -1000 * (n - i + 1),
    }
  })
}

function respondWith(groups: CategoryGroup[]): void {
  const total_cents = groups.reduce((sum, group) => sum + group.total_cents, 0)
  server.use(
    http.get('/api/transactions/expenses/by-category', () =>
      HttpResponse.json({ groups, total_cents }),
    ),
  )
}

function dataRows(): HTMLElement[] {
  return within(screen.getByRole('table')).getAllByRole('row').slice(1)
}

function cellsOf(row: HTMLElement): HTMLElement[] {
  return within(row).getAllByRole('cell')
}

let consoleErrorSpy: ReturnType<typeof vi.spyOn>

beforeEach(() => {
  consoleErrorSpy = vi.spyOn(console, 'error')
})

afterEach(() => {
  consoleErrorSpy.mockRestore()
})

test('shows the heading and one row per group in the order received', async () => {
  respondWith([
    { category: 'Compras', label: 'Compras', count: 42, total_cents: -948490 },
    { category: 'Transporte', label: 'Transporte', count: 1, total_cents: -42000 },
  ])

  renderWithProviders(<CategoryTotals query={ALL} />)

  await screen.findByRole('heading', { level: 2, name: 'Por categoria' })
  expect(screen.getByRole('table', { name: 'Por categoria' })).toBeInTheDocument()

  const rows = dataRows()
  expect(rows).toHaveLength(2)

  const firstCells = cellsOf(rows[0])
  expect(firstCells[0]).toHaveTextContent('Compras')
  expect(firstCells[1]).toHaveTextContent('42 gastos')
  expect(firstCells[2]).toHaveTextContent('R$ 9.484,90')

  const secondCells = cellsOf(rows[1])
  expect(secondCells[0]).toHaveTextContent('Transporte')
  expect(secondCells[1]).toHaveTextContent('1 gasto')
  expect(secondCells[2]).toHaveTextContent('R$ 420,00')

  expect(within(screen.getByRole('table')).queryByRole('button')).not.toBeInTheDocument()
  expect(screen.queryAllByRole('listitem')).toHaveLength(0)
})

test('renders nothing when there are no groups', async () => {
  let called = false
  server.use(
    http.get('/api/transactions/expenses/by-category', () => {
      called = true
      return HttpResponse.json({ groups: [], total_cents: 0 })
    }),
  )

  const { container } = renderWithProviders(<CategoryTotals query={ALL} />)

  await waitFor(() => {
    expect(called).toBe(true)
  })

  expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  expect(screen.queryByRole('table')).not.toBeInTheDocument()
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
  expect(container.firstChild).toBeNull()
})

test('shows no button with eight groups', async () => {
  respondWith(groupsOf(8))

  renderWithProviders(<CategoryTotals query={ALL} />)

  await screen.findByRole('table')

  expect(dataRows()).toHaveLength(8)
  expect(screen.queryByRole('button')).not.toBeInTheDocument()
})

test('shows only the eight biggest groups and "Mostrar todas (12)" with twelve', async () => {
  respondWith(groupsOf(12))

  renderWithProviders(<CategoryTotals query={ALL} />)

  await screen.findByRole('table')

  expect(dataRows()).toHaveLength(8)
  const button = screen.getByRole('button', { name: 'Mostrar todas (12)' })
  expect(button).toHaveAttribute('aria-expanded', 'false')
  expect(screen.queryByText('Categoria 9')).not.toBeInTheDocument()
})

test('"Mostrar todas" reveals every group and turns into "Mostrar menos"', async () => {
  respondWith(groupsOf(12))

  renderWithProviders(<CategoryTotals query={ALL} />)

  await userEvent.click(await screen.findByRole('button', { name: 'Mostrar todas (12)' }))

  expect(dataRows()).toHaveLength(12)
  const button = screen.getByRole('button', { name: 'Mostrar menos' })
  expect(button).toHaveAttribute('aria-expanded', 'true')
})

test('"Mostrar menos" hides the extra groups again', async () => {
  respondWith(groupsOf(12))

  renderWithProviders(<CategoryTotals query={ALL} />)

  await userEvent.click(await screen.findByRole('button', { name: 'Mostrar todas (12)' }))
  await userEvent.click(screen.getByRole('button', { name: 'Mostrar menos' }))

  expect(dataRows()).toHaveLength(8)
  expect(screen.getByRole('button', { name: 'Mostrar todas (12)' })).toBeInTheDocument()
})

test('shows the loading state', () => {
  server.use(
    http.get('/api/transactions/expenses/by-category', async () => {
      await delay('infinite')
      return HttpResponse.json({ groups: [], total_cents: 0 })
    }),
  )

  renderWithProviders(<CategoryTotals query={ALL} />)

  const status = screen.getByText('Carregando totais por categoria…')
  expect(status).toHaveAttribute('role', 'status')
  expect(screen.queryByRole('table')).not.toBeInTheDocument()
})

test('shows the error and retries', async () => {
  let attempt = 0
  server.use(
    http.get('/api/transactions/expenses/by-category', () => {
      attempt += 1
      if (attempt === 1) {
        return HttpResponse.json({}, { status: 500 })
      }
      const groups = groupsOf(2)
      return HttpResponse.json({
        groups,
        total_cents: groups.reduce((sum, group) => sum + group.total_cents, 0),
      })
    }),
  )

  renderWithProviders(<CategoryTotals query={ALL} />)

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar os totais por categoria.')
  const retry = screen.getByRole('button', { name: 'Tentar de novo' })

  await userEvent.click(retry)

  const table = await screen.findByRole('table')
  expect(within(table).getAllByRole('row').slice(1)).toHaveLength(2)
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
})

test('uses the label received for the uncategorised group', async () => {
  respondWith([
    { category: null, label: 'Sem categoria', count: 1, total_cents: -43000 },
    { category: 'Não classificado', label: 'Sem categoria', count: 1, total_cents: -100 },
  ])

  renderWithProviders(<CategoryTotals query={ALL} />)

  await screen.findByRole('table')

  const rows = dataRows()
  expect(rows).toHaveLength(2)
  expect(cellsOf(rows[0])[0]).toHaveTextContent('Sem categoria')
  expect(cellsOf(rows[1])[0]).toHaveTextContent('Sem categoria')
  expect(consoleErrorSpy).not.toHaveBeenCalled()
})

test('sends from, to, account_id and q only when they are set', async () => {
  const calls: URLSearchParams[] = []
  server.use(
    http.get('/api/transactions/expenses/by-category', ({ request }) => {
      const url = new URL(request.url)
      calls.push(url.searchParams)
      return HttpResponse.json({ groups: [], total_cents: 0 })
    }),
  )

  const query: CategoryTotalsQuery = {
    from: '2026-08-01',
    to: '2026-08-31',
    account: 'acc-credit-1',
    search: 'mercado',
  }

  const { unmount } = renderWithProviders(<CategoryTotals query={query} />)

  await waitFor(() => {
    expect(calls).toHaveLength(1)
  })
  const first = calls[0]
  expect(first.get('from')).toBe('2026-08-01')
  expect(first.get('to')).toBe('2026-08-31')
  expect(first.get('account_id')).toBe('acc-credit-1')
  expect(first.get('q')).toBe('mercado')
  expect([...first.keys()]).toHaveLength(4)

  unmount()
  renderWithProviders(<CategoryTotals query={ALL} />)

  await waitFor(() => {
    expect(calls).toHaveLength(2)
  })
  expect(calls[1].size).toBe(0)
})
