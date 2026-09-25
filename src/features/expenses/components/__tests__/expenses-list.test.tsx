import { http, HttpResponse, delay } from 'msw'
import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor, within } from '@testing-library/react'
import { useLocation } from 'react-router'

import { ExpensesList } from '@/features/expenses/components/expenses-list'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import { fakeExpenses } from '@/testing/mocks/handlers'
import type { Expense, ExpenseOrder, ExpenseSort } from '@/features/expenses/types/expense'

function LocationProbe(): React.JSX.Element {
  const location = useLocation()
  return <span data-testid="search">{location.search}</span>
}

function filterForSpy(items: Expense[], from: string | null, to: string | null): Expense[] {
  return items.filter((item) => (from === null || item.date >= from) && (to === null || item.date <= to))
}

function sortForSpy(items: Expense[], sort: ExpenseSort, order: ExpenseOrder): Expense[] {
  const direction = order === 'desc' ? -1 : 1
  return [...items].sort((a, b) => {
    let comparison = 0
    if (sort === 'date') {
      comparison = (a.date < b.date ? -1 : a.date > b.date ? 1 : 0) * direction
    } else if (sort === 'amount') {
      comparison = (Math.abs(a.amount_cents) - Math.abs(b.amount_cents)) * direction
    } else {
      if (a.category === null && b.category === null) {
        comparison = 0
      } else if (a.category === null) {
        comparison = 1
      } else if (b.category === null) {
        comparison = -1
      } else {
        comparison = a.category.localeCompare(b.category, 'pt-BR') * direction
      }
    }
    return comparison !== 0 ? comparison : b.id - a.id
  })
}

function spyOnExpensesRequests(): URLSearchParams[] {
  const calls: URLSearchParams[] = []
  server.use(
    http.get('/api/transactions/expenses', ({ request }) => {
      const url = new URL(request.url)
      calls.push(url.searchParams)
      const page = Number.parseInt(url.searchParams.get('page') ?? '1', 10) || 1
      const pageSize = Number.parseInt(url.searchParams.get('page_size') ?? '20', 10) || 20
      const sort = (url.searchParams.get('sort') ?? 'date') as ExpenseSort
      const order = (url.searchParams.get('order') ?? 'desc') as ExpenseOrder
      const from = url.searchParams.get('from')
      const to = url.searchParams.get('to')
      const filtered = filterForSpy(fakeExpenses, from, to)
      const items = sortForSpy(filtered, sort, order)
      return HttpResponse.json({
        items: items.slice((page - 1) * pageSize, page * pageSize),
        page,
        page_size: pageSize,
        total: filtered.length,
        total_cents: filtered.reduce((sum, item) => sum + item.amount_cents, 0),
      })
    }),
  )
  return calls
}

test('shows the loading state', () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  expect(screen.getByRole('status')).toHaveTextContent('Carregando gastos…')
})

test('shows the empty state', async () => {
  server.use(
    http.get('/api/transactions/expenses', () =>
      HttpResponse.json({ items: [], page: 1, page_size: 20, total: 0 }),
    ),
  )

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  expect(await screen.findByText('Nenhum gasto registrado ainda.')).toBeInTheDocument()
  expect(screen.queryByRole('list')).not.toBeInTheDocument()
})

test('shows the error and retries', async () => {
  let attempt = 0
  server.use(
    http.get('/api/transactions/expenses', () => {
      attempt += 1
      if (attempt === 1) {
        return HttpResponse.json({}, { status: 500 })
      }
      return HttpResponse.json({
        items: [
          {
            id: 1,
            date: '2026-08-01',
            description: 'MERCADO DO BAIRRO',
            payee_name: 'Mercado do Bairro',
            account_name: 'Conta corrente',
            account_institution: 'Banco de teste',
            account_type: 'BANK',
            category: 'Compras',
            amount_cents: -8490,
          },
        ],
        page: 1,
        page_size: 20,
        total: 1,
        total_cents: -8490,
      })
    }),
  )

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar os gastos.')

  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  expect(await screen.findByRole('list')).toBeInTheDocument()
})

test('renders the fields of a row', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  await screen.findByRole('list')

  const row = within(screen.getAllByRole('listitem')[0])

  expect(row.getByText('MERCADO DO BAIRRO')).toBeInTheDocument()
  expect(row.getByText('Mercado do Bairro')).toBeInTheDocument()
  expect(row.getByText('Conta corrente · Banco de teste')).toBeInTheDocument()
  expect(row.getByText('01/08/2026')).toBeInTheDocument()
  expect(row.getByText('Compras')).toBeInTheDocument()
  const amount = row.getByText('-R$ 84,90')
  expect(amount).toBeInTheDocument()
  expect(amount).toHaveClass('text-red-700')
})

test('hides the payee when it is null', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  await screen.findByRole('list')

  expect(screen.getAllByText('Mercado do Bairro')).toHaveLength(1)
})

test('shows "Sem categoria" and "Sem descrição" fallbacks', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  await screen.findByRole('list')

  expect(screen.getByText('Sem descrição')).toBeInTheDocument()
  expect(screen.getByText('Sem categoria')).toBeInTheDocument()
})

test('shows twenty rows on the first page', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  await screen.findByRole('list')

  expect(screen.getAllByRole('listitem')).toHaveLength(20)
})

test('reads the page from the URL', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses?page=3' })

  await screen.findByRole('list')

  const items = screen.getAllByRole('listitem')
  expect(items).toHaveLength(5)
  expect(within(items[0]).getByText('GASTO 5')).toBeInTheDocument()
})

test('treats an invalid page as the first', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses?page=abc' })

  await screen.findByRole('list')

  expect(screen.getAllByRole('listitem')).toHaveLength(20)
  expect(screen.getByText('MERCADO DO BAIRRO')).toBeInTheDocument()
})

test('shows the pagination summary', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  expect(await screen.findByText('Página 1 de 3 · 45 gastos · R$ 10.774,90 no período')).toBeInTheDocument()
})

test('hides the pagination when empty', async () => {
  server.use(
    http.get('/api/transactions/expenses', () =>
      HttpResponse.json({ items: [], page: 1, page_size: 20, total: 0 }),
    ),
  )

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  await screen.findByText('Nenhum gasto registrado ainda.')
  expect(screen.queryByRole('navigation', { name: 'Paginação' })).not.toBeInTheDocument()
})

test('"Próxima" moves to page 2 in the URL and in the API', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses' },
  )

  await screen.findByRole('list')

  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }))

  expect(await screen.findByText('Página 2 de 3 · 45 gastos · R$ 10.774,90 no período')).toBeInTheDocument()
  expect(screen.getByTestId('search')).toHaveTextContent('?page=2')
  const items = screen.getAllByRole('listitem')
  expect(within(items[0]).getByText('GASTO 25')).toBeInTheDocument()
})

test('keeps the previous rows while the next page loads', async () => {
  server.use(
    http.get('/api/transactions/expenses', async ({ request }) => {
      const url = new URL(request.url)
      const page = Number.parseInt(url.searchParams.get('page') ?? '1', 10) || 1
      if (page === 2) {
        await delay(50)
      }
      const pageSize = 20
      return HttpResponse.json({
        items: fakeExpenses.slice((page - 1) * pageSize, page * pageSize),
        page,
        page_size: pageSize,
        total: fakeExpenses.length,
        total_cents: fakeExpenses.reduce((sum, item) => sum + item.amount_cents, 0),
      })
    }),
  )

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  await screen.findByRole('list')

  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }))

  expect(screen.queryByRole('status')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Próxima' })).toBeDisabled()

  expect(await screen.findByText('Página 2 de 3 · 45 gastos · R$ 10.774,90 no período')).toBeInTheDocument()
})

test('falls back to the last page when the URL is past the end', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses?page=9' })

  expect(await screen.findByText('Página 3 de 3 · 45 gastos · R$ 10.774,90 no período')).toBeInTheDocument()
})

test('shows the default sorting controls', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses' },
  )

  const combobox = await screen.findByRole('combobox', { name: 'Ordenar por' })
  expect(combobox).toHaveValue('date')
  expect(screen.getByRole('option', { name: 'Data', selected: true })).toBeInTheDocument()

  const button = screen.getByRole('button', { name: 'Inverter direção da ordenação' })
  expect(button).toHaveTextContent('Decrescente')

  expect(screen.getByTestId('search')).toHaveTextContent('')

  await waitFor(() => {
    expect(calls[0]?.get('sort')).toBe('date')
    expect(calls[0]?.get('order')).toBe('desc')
  })
})

test('sorting by amount puts the biggest spending first', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses' },
  )

  await screen.findByRole('list')

  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Ordenar por' }), 'amount')

  expect(screen.getByTestId('search')).toHaveTextContent('?sort=amount')
  expect(screen.getByRole('button', { name: 'Inverter direção da ordenação' })).toHaveTextContent(
    'Decrescente',
  )

  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('sort')).toBe('amount')
    expect(last?.get('order')).toBe('desc')
  })

  await waitFor(() => {
    const items = screen.getAllByRole('listitem')
    expect(within(items[0]).getByText('-R$ 1.200,00')).toBeInTheDocument()
  })
})

test('sorting by category starts ascending', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses' },
  )

  await screen.findByRole('list')

  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Ordenar por' }), 'category')

  expect(screen.getByTestId('search')).toHaveTextContent('?sort=category&order=asc')
  expect(screen.getByRole('button', { name: 'Inverter direção da ordenação' })).toHaveTextContent(
    'Crescente',
  )

  await waitFor(() => {
    const items = screen.getAllByRole('listitem')
    expect(within(items[0]).getByText('Alimentação')).toBeInTheDocument()
  })
})

test('toggling the direction inverts the order', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?sort=category&order=asc' },
  )

  await screen.findByRole('list')

  await userEvent.click(screen.getByRole('button', { name: 'Inverter direção da ordenação' }))

  expect(screen.getByTestId('search')).toHaveTextContent('?sort=category')
  expect(screen.getByRole('button', { name: 'Inverter direção da ordenação' })).toHaveTextContent(
    'Decrescente',
  )

  await waitFor(() => {
    const items = screen.getAllByRole('listitem')
    expect(within(items[0]).getByText('Transporte')).toBeInTheDocument()
  })
})

test('toggling the direction on the default sort writes only the order', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses' },
  )

  await screen.findByRole('list')

  await userEvent.click(screen.getByRole('button', { name: 'Inverter direção da ordenação' }))

  expect(screen.getByTestId('search')).toHaveTextContent('?order=asc')
  expect(screen.getByRole('button', { name: 'Inverter direção da ordenação' })).toHaveTextContent(
    'Crescente',
  )

  await waitFor(() => {
    const items = screen.getAllByRole('listitem')
    expect(within(items[0]).getByText('GASTO 1')).toBeInTheDocument()
  })
})

test('changing the sorting drops the page', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?page=2' },
  )

  await screen.findByRole('list')

  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Ordenar por' }), 'amount')

  expect(screen.getByTestId('search')).toHaveTextContent('?sort=amount')
  expect(await screen.findByText('Página 1 de 3 · 45 gastos · R$ 10.774,90 no período')).toBeInTheDocument()
})

test('pagination keeps the sorting', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?sort=amount' },
  )

  await screen.findByRole('list')

  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }))

  expect(await screen.findByTestId('search')).toHaveTextContent('?sort=amount&page=2')

  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('sort')).toBe('amount')
    expect(last?.get('order')).toBe('desc')
    expect(last?.get('page')).toBe('2')
  })
})

test('falls back to the defaults on unknown sort and order', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses?sort=foo&order=bar' })

  const combobox = await screen.findByRole('combobox', { name: 'Ordenar por' })
  expect(combobox).toHaveValue('date')
  expect(screen.getByRole('button', { name: 'Inverter direção da ordenação' })).toHaveTextContent(
    'Decrescente',
  )

  await waitFor(() => {
    expect(calls[0]?.get('sort')).toBe('date')
    expect(calls[0]?.get('order')).toBe('desc')
  })

  const items = screen.getAllByRole('listitem')
  expect(within(items[0]).getByText('MERCADO DO BAIRRO')).toBeInTheDocument()
})

test('keeps the controls visible in the error state', async () => {
  server.use(
    http.get('/api/transactions/expenses', () => HttpResponse.json({}, { status: 500 })),
  )

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar os gastos.')
  expect(screen.getByRole('combobox', { name: 'Ordenar por' })).toBeInTheDocument()
})

test('keeps the controls visible in the empty state', async () => {
  server.use(
    http.get('/api/transactions/expenses', () =>
      HttpResponse.json({ items: [], page: 1, page_size: 20, total: 0 }),
    ),
  )

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  expect(await screen.findByText('Nenhum gasto registrado ainda.')).toBeInTheDocument()
  expect(screen.getByRole('combobox', { name: 'Ordenar por' })).toBeInTheDocument()
})

test('shows the whole period by default', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  await screen.findByRole('list')

  expect(screen.getByText('Todo o período', { selector: 'span' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Todo o período' })).toBeDisabled()
  expect(screen.getByLabelText('De', { exact: true })).toHaveValue('')
  expect(screen.getByLabelText('Até', { exact: true })).toHaveValue('')

  await waitFor(() => {
    expect(calls[0]?.get('from')).toBeNull()
    expect(calls[0]?.get('to')).toBeNull()
  })

  expect(await screen.findByText(/45 gastos · R\$ .* no período/)).toBeInTheDocument()
})

test('reads the month from the URL', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses?month=2026-07' })

  await screen.findByRole('list')

  await waitFor(() => {
    expect(calls[0]?.get('from')).toBe('2026-07-01')
    expect(calls[0]?.get('to')).toBe('2026-07-31')
  })

  expect(screen.getByText('julho de 2026')).toBeInTheDocument()
  expect(await screen.findByText(/31 gastos/)).toBeInTheDocument()
  expect(screen.getByLabelText('De', { exact: true })).toHaveValue('2026-07-01')
  expect(screen.getByLabelText('Até', { exact: true })).toHaveValue('2026-07-31')
  expect(screen.getByRole('button', { name: 'Todo o período' })).toBeEnabled()
})

test('"Mês anterior" moves one month back', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?month=2026-07' },
  )

  await screen.findByRole('list')

  await userEvent.click(screen.getByRole('button', { name: 'Mês anterior' }))

  expect(screen.getByTestId('search')).toHaveTextContent('?month=2026-06')
  expect(await screen.findByText(/13 gastos/)).toBeInTheDocument()
})

test('"Próximo mês" moves one month forward', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?month=2026-07' },
  )

  await screen.findByRole('list')

  await userEvent.click(screen.getByRole('button', { name: 'Próximo mês' }))

  expect(screen.getByTestId('search')).toHaveTextContent('?month=2026-08')
  expect(await screen.findByText(/1 gasto ·/)).toBeInTheDocument()
  const items = screen.getAllByRole('listitem')
  expect(items).toHaveLength(1)
  expect(within(items[0]).getByText('MERCADO DO BAIRRO')).toBeInTheDocument()
})

test('"Mês anterior" without a month starts from the current month', async () => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 8, 15))

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses' },
  )

  await userEvent.click(await screen.findByRole('button', { name: 'Mês anterior' }))

  expect(screen.getByTestId('search')).toHaveTextContent('?month=2026-08')

  vi.useRealTimers()
})

test('shows the filtered empty state with the controls', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses?month=2026-09' })

  expect(await screen.findByText('Nenhum gasto nesse período.')).toBeInTheDocument()
  expect(screen.queryByText('Nenhum gasto registrado ainda.')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Mês anterior' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Todo o período' })).toBeInTheDocument()
})

test('"Todo o período" clears the month', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?month=2026-07' },
  )

  await screen.findByRole('list')

  await userEvent.click(screen.getByRole('button', { name: 'Todo o período' }))

  expect(screen.getByTestId('search')).toHaveTextContent('')
  expect(await screen.findByText(/45 gastos/)).toBeInTheDocument()
})

test('editing a date switches from month to range', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?month=2026-07' },
  )

  await screen.findByRole('list')

  const fromInput = screen.getByLabelText('De', { exact: true })
  await userEvent.clear(fromInput)
  await userEvent.type(fromInput, '2026-07-10')

  await waitFor(() => {
    expect(screen.getByTestId('search')).toHaveTextContent('?from=2026-07-10&to=2026-07-31')
  })

  const toInput = screen.getByLabelText('Até', { exact: true })
  await userEvent.clear(toInput)
  await userEvent.type(toInput, '2026-07-20')

  await waitFor(() => {
    const search = screen.getByTestId('search').textContent
    expect(search).toContain('from=2026-07-10')
    expect(search).toContain('to=2026-07-20')
    expect(search).not.toContain('month=')
  })

  expect(screen.getByText('Período personalizado')).toBeInTheDocument()

  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('from')).toBe('2026-07-10')
    expect(last?.get('to')).toBe('2026-07-20')
  })
})

test('the field just edited wins over an inverted range', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?from=2026-07-10&to=2026-07-20' },
  )

  await screen.findByRole('list')

  const fromInput = screen.getByLabelText('De', { exact: true })
  await userEvent.clear(fromInput)
  await userEvent.type(fromInput, '2026-07-25')

  await waitFor(() => {
    const search = screen.getByTestId('search').textContent
    expect(search).toContain('from=2026-07-25')
    expect(search).not.toContain('to=')
  })
})

test('the month wins when the URL has both formats', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses?month=2026-07&from=2026-01-01' })

  await screen.findByRole('list')

  await waitFor(() => {
    expect(calls[0]?.get('from')).toBe('2026-07-01')
    expect(calls[0]?.get('to')).toBe('2026-07-31')
  })

  expect(screen.getByText('julho de 2026')).toBeInTheDocument()
})

test('changing the period drops the page and keeps the sorting', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?month=2026-07&page=2&sort=amount' },
  )

  await screen.findByRole('list')

  await userEvent.click(screen.getByRole('button', { name: 'Mês anterior' }))

  await waitFor(() => {
    const search = new URLSearchParams(screen.getByTestId('search').textContent)
    expect(search.get('month')).toBe('2026-06')
    expect(search.get('sort')).toBe('amount')
    expect(search.get('page')).toBeNull()
  })
})

test('pagination keeps the period', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?month=2026-07' },
  )

  await screen.findByRole('list')

  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }))

  await waitFor(() => {
    const search = screen.getByTestId('search').textContent
    expect(search).toContain('month=2026-07')
    expect(search).toContain('page=2')
  })

  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('from')).toBe('2026-07-01')
    expect(last?.get('to')).toBe('2026-07-31')
    expect(last?.get('page')).toBe('2')
  })
})

test('falls back to the whole period on an invalid month', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses?month=13' })

  await screen.findByRole('list')

  expect(screen.getByText('Todo o período', { selector: 'span' })).toBeInTheDocument()

  await waitFor(() => {
    expect(calls[0]?.get('from')).toBeNull()
    expect(calls[0]?.get('to')).toBeNull()
  })
})

test('keeps the period controls visible in the error state', async () => {
  server.use(http.get('/api/transactions/expenses', () => HttpResponse.json({}, { status: 500 })))

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar os gastos.')
  expect(screen.getByRole('button', { name: 'Mês anterior' })).toBeInTheDocument()
})
