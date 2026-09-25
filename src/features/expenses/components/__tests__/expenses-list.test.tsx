import { http, HttpResponse, delay } from 'msw'
import { afterEach, expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { useLocation } from 'react-router'

import { ExpensesList } from '@/features/expenses/components/expenses-list'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import { fakeExpenses, fakePlan, filterExpenses, foldText, groupByCategory } from '@/testing/mocks/handlers'
import type { Expense, ExpenseOrder, ExpenseSort } from '@/features/expenses/types/expense'

afterEach(() => {
  vi.useRealTimers()
})

function LocationProbe(): React.JSX.Element {
  const location = useLocation()
  return <span data-testid="search">{location.search}</span>
}

function filterForSpy(
  items: Expense[],
  from: string | null,
  to: string | null,
  accountId: string | null,
  term: string | null,
): Expense[] {
  return items.filter(
    (item) =>
      (from === null || item.date >= from) &&
      (to === null || item.date <= to) &&
      (accountId === null || item.account_id === accountId) &&
      (term === null ||
        foldText(item.description ?? '').includes(term) ||
        foldText(item.payee_name ?? '').includes(term)),
  )
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
      const accountId = url.searchParams.get('account_id')
      const rawTerm = url.searchParams.get('q')?.trim() ?? ''
      const term = rawTerm.length >= 2 ? foldText(rawTerm) : null
      const filtered = filterForSpy(fakeExpenses, from, to, accountId, term)
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

function spyOnCategoryTotalsRequests(): URLSearchParams[] {
  const calls: URLSearchParams[] = []
  server.use(
    http.get('/api/transactions/expenses/by-category', ({ request }) => {
      const url = new URL(request.url)
      calls.push(url.searchParams)
      const groups = groupByCategory(filterExpenses(url))
      return HttpResponse.json({
        groups,
        total_cents: groups.reduce((sum, group) => sum + group.total_cents, 0),
      })
    }),
  )
  return calls
}

function categoryRows(): HTMLElement[] {
  return within(screen.getByRole('table')).getAllByRole('row').slice(1)
}

function cellsOf(row: HTMLElement): string[] {
  return within(row)
    .getAllByRole('cell')
    .map((cell) => cell.textContent)
}

test('shows the loading state', () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  expect(screen.getByText('Carregando gastos…')).toBeInTheDocument()
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
            account_id: 'acc-bank-1',
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

  const list = screen.getByRole('list')
  expect(within(list).getByText('Sem descrição')).toBeInTheDocument()
  expect(within(list).getByText('Sem categoria')).toBeInTheDocument()
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

  expect(screen.queryByText('Carregando gastos…')).not.toBeInTheDocument()
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
  const pagination = screen.getByRole('navigation', { name: 'Paginação' })
  expect(await within(pagination).findByText(/13 gastos/)).toBeInTheDocument()
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

  expect(await screen.findByText('Nenhum gasto para esse filtro.')).toBeInTheDocument()
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

test('shows "Todas as contas" by default and calls the API without account_id', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  expect(screen.getByLabelText('Conta')).toHaveValue('')
  expect(await screen.findByText(/45 gastos/)).toBeInTheDocument()

  await waitFor(() => {
    expect(calls[0]?.get('account_id')).toBeNull()
  })
})

test('reads the account from the URL', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses?account=acc-credit-1' })

  await waitFor(() => {
    expect(calls.at(-1)?.get('account_id')).toBe('acc-credit-1')
  })

  const pagination = screen.getByRole('navigation', { name: 'Paginação' })
  expect(await within(pagination).findByText(/13 gastos/)).toBeInTheDocument()
  await waitFor(() => {
    expect(screen.getByLabelText('Conta')).toHaveValue('acc-credit-1')
  })

  const list = screen.getByRole('list')
  const items = within(list).getAllByRole('listitem')
  items.forEach((item) => {
    expect(within(item).getByText(/Cartão · Emissor de teste/)).toBeInTheDocument()
  })
  expect(within(list).queryByText(/Conta corrente · Banco de teste/)).not.toBeInTheDocument()
})

test('choosing an account drops the page and keeps the period and the sorting', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?page=2&sort=amount&month=2026-07' },
  )

  await screen.findByRole('list')
  await waitFor(() => {
    expect(screen.getByLabelText('Conta')).toBeEnabled()
  })

  await userEvent.selectOptions(screen.getByLabelText('Conta'), 'acc-credit-1')

  await waitFor(() => {
    const search = new URLSearchParams(screen.getByTestId('search').textContent)
    expect(search.get('page')).toBeNull()
    expect(search.get('account')).toBe('acc-credit-1')
    expect(search.get('sort')).toBe('amount')
    expect(search.get('month')).toBe('2026-07')
  })

  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('account_id')).toBe('acc-credit-1')
    expect(last?.get('from')).toBe('2026-07-01')
    expect(last?.get('to')).toBe('2026-07-31')
    expect(last?.get('page')).toBe('1')
  })
})

test('choosing "Todas as contas" removes the account from the URL', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?account=acc-credit-1' },
  )

  await screen.findByRole('list')
  await waitFor(() => {
    expect(screen.getByLabelText('Conta')).toHaveValue('acc-credit-1')
  })

  await userEvent.selectOptions(screen.getByLabelText('Conta'), '')

  await waitFor(() => {
    const search = new URLSearchParams(screen.getByTestId('search').textContent)
    expect(search.get('account')).toBeNull()
  })
  expect(await screen.findByText(/45 gastos/)).toBeInTheDocument()
})

test('pagination keeps the account', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?account=acc-bank-1' },
  )

  await screen.findByRole('list')
  await waitFor(() => {
    expect(calls.at(-1)?.get('account_id')).toBe('acc-bank-1')
  })

  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }))

  await waitFor(() => {
    const search = new URLSearchParams(screen.getByTestId('search').textContent)
    expect(search.get('account')).toBe('acc-bank-1')
    expect(search.get('page')).toBe('2')
  })

  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('account_id')).toBe('acc-bank-1')
    expect(last?.get('page')).toBe('2')
  })
})

test('shows the filtered empty state for an account without spending in the month', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses?account=acc-credit-1&month=2026-09' })

  expect(await screen.findByText('Nenhum gasto para esse filtro.')).toBeInTheDocument()
  expect(screen.queryByText('Nenhum gasto registrado ainda.')).not.toBeInTheDocument()
  expect(screen.getByLabelText('Conta')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Todo o período' })).toBeInTheDocument()
})

test('drops an unknown account from the URL once the accounts load', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?account=nao-existe' },
  )

  await waitFor(() => {
    const search = new URLSearchParams(screen.getByTestId('search').textContent)
    expect(search.get('account')).toBeNull()
  })

  await waitFor(() => {
    expect(calls.at(-1)?.get('account_id')).toBeNull()
  })

  expect(await screen.findByText(/45 gastos/)).toBeInTheDocument()
  expect(screen.getByLabelText('Conta')).toHaveValue('')
})

test('keeps the expenses list when the accounts request fails', async () => {
  server.use(http.get('/api/accounts/balances', () => HttpResponse.json({}, { status: 500 })))

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível carregar as contas.')
  expect(within(screen.getByLabelText('Conta')).getAllByRole('option')).toHaveLength(1)
  expect(await screen.findByRole('list')).toBeInTheDocument()
  expect(await screen.findByText(/45 gastos/)).toBeInTheDocument()
  expect(screen.queryByText('Não foi possível carregar os gastos.')).not.toBeInTheDocument()
})

test('keeps the account select visible in the error state', async () => {
  server.use(http.get('/api/transactions/expenses', () => HttpResponse.json({}, { status: 500 })))

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar os gastos.')
  expect(screen.getByLabelText('Conta')).toBeInTheDocument()
})

test('shows an empty "Buscar" field by default and calls the API without q', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  expect(screen.getByLabelText('Buscar')).toHaveValue('')
  expect(screen.queryByRole('button', { name: 'Limpar busca' })).not.toBeInTheDocument()

  await waitFor(() => {
    expect(calls[0]?.get('q')).toBeNull()
  })

  expect(await screen.findByText(/45 gastos/)).toBeInTheDocument()
})

test('reads the search from the URL', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses?q=mercado' })

  await waitFor(() => {
    expect(calls.at(-1)?.get('q')).toBe('mercado')
  })

  expect(screen.getByLabelText('Buscar')).toHaveValue('mercado')
  expect(screen.getByRole('button', { name: 'Limpar busca' })).toBeInTheDocument()
  const pagination = screen.getByRole('navigation', { name: 'Paginação' })
  expect(await within(pagination).findByText(/1 gasto\b/)).toBeInTheDocument()

  const items = screen.getAllByRole('listitem')
  expect(items).toHaveLength(1)
  expect(within(items[0]).getByText('MERCADO DO BAIRRO')).toBeInTheDocument()
})

test('typing writes q to the URL after 300 ms and filters the list', async () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses' },
  )

  fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'acougue' } })

  expect(screen.getByTestId('search')).not.toHaveTextContent('q=')

  vi.advanceTimersByTime(300)

  await vi.waitFor(() => {
    expect(screen.getByTestId('search')).toHaveTextContent('q=acougue')
  })

  await vi.waitFor(() => {
    expect(calls.at(-1)?.get('q')).toBe('acougue')
  })

  await vi.waitFor(() => {
    expect(screen.getAllByRole('listitem')).toHaveLength(1)
  })
  const items = screen.getAllByRole('listitem')
  expect(within(items[0]).getByText('Açougue São Jorge')).toBeInTheDocument()
  expect(within(items[0]).getByText('GASTO 42')).toBeInTheDocument()
})

test('a one-character search does not touch the URL nor the API', async () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses' },
  )

  await vi.waitFor(() => {
    expect(screen.getByText(/45 gastos/)).toBeInTheDocument()
  })
  const callsBefore = calls.length

  fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'a' } })
  vi.advanceTimersByTime(300)

  expect(screen.getByTestId('search')).not.toHaveTextContent('q=')
  expect(calls.length).toBe(callsBefore)
  expect(screen.getByText(/45 gastos/)).toBeInTheDocument()
})

test('Enter commits the search immediately', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses' },
  )

  await screen.findByText(/45 gastos/)

  await userEvent.type(screen.getByLabelText('Buscar'), 'Gasto 4{Enter}')

  await waitFor(() => {
    const search = new URLSearchParams(screen.getByTestId('search').textContent)
    expect(search.get('q')).toBe('Gasto 4')
  })

  await waitFor(() => {
    expect(calls.at(-1)?.get('q')).toBe('Gasto 4')
  })
})

test('searching drops the page and keeps the account and the sorting', async () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?page=2&account=acc-bank-1&sort=amount' },
  )

  fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'gasto' } })
  vi.advanceTimersByTime(300)

  await vi.waitFor(() => {
    const search = new URLSearchParams(screen.getByTestId('search').textContent)
    expect(search.get('page')).toBeNull()
    expect(search.get('q')).toBe('gasto')
    expect(search.get('account')).toBe('acc-bank-1')
    expect(search.get('sort')).toBe('amount')
  })

  await vi.waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('q')).toBe('gasto')
    expect(last?.get('account_id')).toBe('acc-bank-1')
    expect(last?.get('sort')).toBe('amount')
    expect(last?.get('page')).toBe('1')
  })

  vi.useRealTimers()
})

test('clearing the search removes q from the URL', async () => {
  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?q=mercado' },
  )

  await screen.findByRole('button', { name: 'Limpar busca' })

  await userEvent.click(screen.getByRole('button', { name: 'Limpar busca' }))

  expect(screen.getByTestId('search')).not.toHaveTextContent('q=')
  expect(screen.getByLabelText('Buscar')).toHaveValue('')
  expect(await screen.findByText(/45 gastos/)).toBeInTheDocument()
})

test('shows the filtered empty state for a search without results', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses?q=zzzz' })

  expect(await screen.findByText('Nenhum gasto para esse filtro.')).toBeInTheDocument()
  expect(screen.getByLabelText('Buscar')).toHaveValue('zzzz')
  expect(screen.getByLabelText('Conta')).toBeInTheDocument()
  expect(screen.getByRole('combobox', { name: 'Ordenar por' })).toBeInTheDocument()
})

test('pagination keeps the search', async () => {
  const calls = spyOnExpensesRequests()

  renderWithProviders(
    <>
      <ExpensesList />
      <LocationProbe />
    </>,
    { route: '/expenses?q=gasto' },
  )

  expect(await screen.findByText(/43 gastos/)).toBeInTheDocument()

  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }))

  await waitFor(() => {
    const search = new URLSearchParams(screen.getByTestId('search').textContent)
    expect(search.get('q')).toBe('gasto')
    expect(search.get('page')).toBe('2')
  })

  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('q')).toBe('gasto')
    expect(last?.get('page')).toBe('2')
  })
})

test('keeps the search field visible in the error state', async () => {
  server.use(http.get('/api/transactions/expenses', () => HttpResponse.json({}, { status: 500 })))

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar os gastos.')
  expect(screen.getByLabelText('Buscar')).toBeInTheDocument()
})

test('retrying keeps the search', async () => {
  let attempt = 0
  server.use(
    http.get('/api/transactions/expenses', ({ request }) => {
      attempt += 1
      if (attempt === 1) {
        return HttpResponse.json({}, { status: 500 })
      }
      const url = new URL(request.url)
      expect(url.searchParams.get('q')).toBe('mercado')
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
            account_id: 'acc-bank-1',
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

  renderWithProviders(<ExpensesList />, { route: '/expenses?q=mercado' })

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar os gastos.')

  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  const items = await screen.findAllByRole('listitem')
  expect(items).toHaveLength(1)
  expect(within(items[0]).getByText('MERCADO DO BAIRRO')).toBeInTheDocument()
})

test('shows the totals by category above the list', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  await screen.findByRole('heading', { level: 2, name: 'Por categoria' })

  const rows = categoryRows()
  expect(rows).toHaveLength(4)
  const firstCells = within(rows[0]).getAllByRole('cell')
  expect(firstCells[0]).toHaveTextContent('Compras')
  expect(firstCells[1]).toHaveTextContent('42 gastos')
  expect(firstCells[2]).toHaveTextContent('R$ 9.484,90')
  const secondCells = within(rows[1]).getAllByRole('cell')
  expect(secondCells[0]).toHaveTextContent('Alimentação')
  expect(secondCells[1]).toHaveTextContent('1 gasto')
  expect(secondCells[2]).toHaveTextContent('R$ 440,00')
  const thirdCells = within(rows[2]).getAllByRole('cell')
  expect(thirdCells[0]).toHaveTextContent('Sem categoria')
  expect(thirdCells[1]).toHaveTextContent('1 gasto')
  expect(thirdCells[2]).toHaveTextContent('R$ 430,00')
  const fourthCells = within(rows[3]).getAllByRole('cell')
  expect(fourthCells[0]).toHaveTextContent('Transporte')
  expect(fourthCells[1]).toHaveTextContent('1 gasto')
  expect(fourthCells[2]).toHaveTextContent('R$ 420,00')
  expect(screen.queryByRole('button', { name: /Mostrar todas/ })).not.toBeInTheDocument()

  const section = screen.getByRole('table', { name: 'Por categoria' }).closest('section')
  const list = await screen.findByRole('list')
  expect(section).not.toBeNull()
  if (section) {
    expect(
      section.compareDocumentPosition(list) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
  }
  expect(await screen.findAllByRole('listitem')).toHaveLength(20)
})

test('filters the totals by account and sends account_id to by-category', async () => {
  const calls = spyOnCategoryTotalsRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses?account=acc-credit-1' })

  await screen.findByRole('heading', { level: 2, name: 'Por categoria' })

  const rows = categoryRows()
  expect(rows).toHaveLength(1)
  const cells = within(rows[0]).getAllByRole('cell')
  expect(cells[0]).toHaveTextContent('Compras')
  expect(cells[1]).toHaveTextContent('13 gastos')
  expect(cells[2]).toHaveTextContent('R$ 2.730,00')

  await waitFor(() => {
    expect(calls.at(-1)?.get('account_id')).toBe('acc-credit-1')
  })
})

test('hides the totals block for a search without results', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses?q=zzzz' })

  await screen.findByText('Nenhum gasto para esse filtro.')

  expect(screen.queryByRole('heading', { level: 2 })).not.toBeInTheDocument()
  expect(screen.queryByRole('table')).not.toBeInTheDocument()
})

test('keeps the list when by-category fails', async () => {
  server.use(
    http.get('/api/transactions/expenses/by-category', () => HttpResponse.json({}, { status: 500 })),
  )

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar os totais por categoria.')

  expect(await screen.findAllByRole('listitem')).toHaveLength(20)
  expect(screen.queryByText('Não foi possível carregar os gastos.')).not.toBeInTheDocument()
})

test('"Próxima" does not refetch by-category', async () => {
  const categoryCalls = spyOnCategoryTotalsRequests()
  const expensesCalls = spyOnExpensesRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  await screen.findByRole('list')
  await waitFor(() => {
    expect(categoryCalls.length).toBe(1)
  })

  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }))

  await waitFor(() => {
    expect(expensesCalls.at(-1)?.get('page')).toBe('2')
  })

  expect(categoryCalls.length).toBe(1)
})

test('changing the period refetches by-category with from and to', async () => {
  const calls = spyOnCategoryTotalsRequests()

  renderWithProviders(<ExpensesList />, { route: '/expenses?month=2026-08' })

  await screen.findByRole('list')
  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('from')).toBe('2026-08-01')
    expect(last?.get('to')).toBe('2026-08-31')
  })

  await userEvent.click(screen.getByRole('button', { name: 'Todo o período' }))

  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('from')).toBeNull()
    expect(last?.get('to')).toBeNull()
  })
})

test('renders every category badge as a button that is enabled once the catalogue loads', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const rows = await screen.findAllByRole('listitem')
  expect(rows).toHaveLength(20)

  const badge = within(rows[0]).getByRole('button', { name: 'Trocar categoria de MERCADO DO BAIRRO' })
  expect(badge).toHaveTextContent('Compras')
  await waitFor(() => {
    expect(badge).toBeEnabled()
  })

  const list = screen.getByRole('list')
  expect(within(list).queryByRole('combobox')).not.toBeInTheDocument()
})

test('changing the category of an uncategorised row refetches the list and the totals and marks it manual', async () => {
  const user = userEvent.setup()
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const list = await screen.findByRole('list')
  const row = within(list).getByText('Sem categoria').closest('li')
  if (row === null) throw new Error('row not found')

  await user.click(within(row).getByRole('button', { name: 'Trocar categoria de Sem descrição' }))
  await user.selectOptions(
    within(row).getByRole('combobox', { name: 'Categoria de Sem descrição' }),
    'Groceries',
  )

  await waitFor(() => {
    expect(within(row).getByText('Supermercado')).toBeInTheDocument()
  })
  expect(within(row).getByText('manual')).toBeInTheDocument()

  await waitFor(() => {
    const rows = categoryRows()
    expect(rows.some((r) => cellsOf(r)[0] === 'Supermercado')).toBe(true)
  })
  const rows = categoryRows()
  const supermercado = rows.find((r) => cellsOf(r)[0] === 'Supermercado')
  expect(supermercado).toBeDefined()
  if (supermercado) {
    const cells = within(supermercado).getAllByRole('cell')
    expect(cells[0]).toHaveTextContent('Supermercado')
    expect(cells[1]).toHaveTextContent('1 gasto')
    expect(cells[2]).toHaveTextContent('R$ 430,00')
  }
  expect(rows.some((r) => cellsOf(r)[0] === 'Sem categoria')).toBe(false)
  expect(within(list).queryByText('Sem categoria')).not.toBeInTheDocument()
})

test('"Voltar para a automática" restores the row and removes "manual"', async () => {
  const user = userEvent.setup()
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const list = await screen.findByRole('list')
  const row = within(list).getByText('Sem categoria').closest('li')
  if (row === null) throw new Error('row not found')

  await user.click(within(row).getByRole('button', { name: 'Trocar categoria de Sem descrição' }))
  await user.selectOptions(
    within(row).getByRole('combobox', { name: 'Categoria de Sem descrição' }),
    'Groceries',
  )

  await waitFor(() => {
    expect(within(row).getByText('Supermercado')).toBeInTheDocument()
  })

  await user.click(within(row).getByRole('button', { name: 'Trocar categoria de Sem descrição' }))
  await user.selectOptions(
    within(row).getByRole('combobox', { name: 'Categoria de Sem descrição' }),
    '__auto__',
  )

  await waitFor(() => {
    expect(within(row).getByText('Sem categoria')).toBeInTheDocument()
  })
  expect(within(row).queryByText('manual')).not.toBeInTheDocument()

  await waitFor(() => {
    const rows = categoryRows()
    const semCategoria = rows.find((r) => cellsOf(r)[0] === 'Sem categoria')
    expect(semCategoria).toBeDefined()
    if (semCategoria) {
      const cells = within(semCategoria).getAllByRole('cell')
      expect(cells[0]).toHaveTextContent('Sem categoria')
      expect(cells[1]).toHaveTextContent('1 gasto')
      expect(cells[2]).toHaveTextContent('R$ 430,00')
    }
  })
})

test('applying the category to the similar expenses updates the other row and the totals', async () => {
  const user = userEvent.setup()
  fakeExpenses[5].description = 'MERCADO DO BAIRRO'
  fakeExpenses[5].payee_name = 'Mercado do Bairro'

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const list = await screen.findByRole('list')
  const items = within(list).getAllByRole('listitem')
  const row = items[0]

  await user.click(
    within(row).getByRole('button', { name: 'Trocar categoria de MERCADO DO BAIRRO' }),
  )
  await user.selectOptions(
    within(row).getByRole('combobox', { name: 'Categoria de MERCADO DO BAIRRO' }),
    'Groceries',
  )

  await within(row).findByText('Aplicar a 1 gasto parecido')

  await user.click(within(row).getByRole('button', { name: 'Aplicar' }))

  await within(row).findByText('Categoria aplicada a 1 gasto')

  const otherRow = screen.getAllByRole('listitem')[5]
  await waitFor(() => {
    expect(within(otherRow).getByText('Supermercado')).toBeInTheDocument()
  })
  expect(within(otherRow).getByText('manual')).toBeInTheDocument()

  await waitFor(() => {
    const rows = categoryRows()
    const supermercado = rows.find((r) => cellsOf(r)[0] === 'Supermercado')
    expect(supermercado).toBeDefined()
    if (supermercado) {
      const cells = within(supermercado).getAllByRole('cell')
      expect(cells[1]).toHaveTextContent('2 gastos')
      expect(cells[2]).toHaveTextContent('R$ 484,90')
    }
  })
})

test('keeps the list usable when the categories request fails', async () => {
  server.use(http.get('/api/categories', () => HttpResponse.json({}, { status: 500 })))

  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  const rows = await screen.findAllByRole('listitem')
  expect(rows).toHaveLength(20)

  const buttons = screen.getAllByRole('button', { name: /^Trocar categoria de / })
  expect(buttons.length).toBeGreaterThan(0)
  for (const button of buttons) {
    expect(button).toBeDisabled()
  }

  expect(screen.queryByText('Não foi possível carregar os gastos.')).not.toBeInTheDocument()
})

test('shows the signal badges and the summary for a month', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses?month=2026-07' })

  await screen.findByRole('heading', { level: 2, name: 'Por categoria' })

  const rows = categoryRows()
  const compras = rows.find((r) => cellsOf(r)[0]?.includes('Compras'))
  const alimentacao = rows.find((r) => cellsOf(r)[0]?.includes('Alimentação'))
  const transporte = rows.find((r) => cellsOf(r)[0]?.includes('Transporte'))
  expect(compras).toBeDefined()
  expect(alimentacao).toBeDefined()
  expect(transporte).toBeDefined()

  if (compras) {
    expect(cellsOf(compras)[0]).toContain('Acima')
  }
  if (alimentacao) {
    expect(cellsOf(alimentacao)[0]).toContain('Dentro')
  }
  if (transporte) {
    const transporteText = cellsOf(transporte)[0] ?? ''
    expect(transporteText).not.toContain('Dentro')
    expect(transporteText).not.toContain('Atenção')
    expect(transporteText).not.toContain('Acima')
  }

  expect(screen.getByText('1 categoria acima do limite')).toBeInTheDocument()
  expect(screen.queryByText('Sinal só por mês')).not.toBeInTheDocument()
})

test('shows "Sinal só por mês" and no badge for the whole period', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses' })

  await screen.findByRole('heading', { level: 2, name: 'Por categoria' })

  expect(screen.getByText('Sinal só por mês')).toBeInTheDocument()

  for (const row of categoryRows()) {
    const text = cellsOf(row)[0] ?? ''
    expect(text).not.toContain('Dentro')
    expect(text).not.toContain('Atenção')
    expect(text).not.toContain('Acima')
  }
  expect(screen.queryByText(/acima do limite/)).not.toBeInTheDocument()
})

test('shows the month ceiling block with the invitation for a month without ceiling', async () => {
  renderWithProviders(<ExpensesList />, { route: '/expenses?month=2026-08' })

  expect(
    await screen.findByRole('heading', { level: 2, name: 'Teto do mês' }),
  ).toBeInTheDocument()
  expect(screen.getByText('Sem teto definido.', { exact: false })).toBeInTheDocument()
})

test('hides the month ceiling block and does not call month-signal outside a month', async () => {
  const calls: URLSearchParams[] = []
  server.use(
    http.get('/api/transactions/expenses/month-signal', ({ request }) => {
      calls.push(new URL(request.url).searchParams)
      return HttpResponse.json({
        scope: 'none',
        spent_cents: 0,
        ceiling_cents: null,
        signal: null,
        remaining_cents: null,
      })
    }),
  )

  renderWithProviders(<ExpensesList />, { route: '/expenses' })
  await screen.findByRole('heading', { level: 2, name: 'Por categoria' })
  expect(screen.queryByText('Teto do mês')).not.toBeInTheDocument()

  cleanup()

  renderWithProviders(<ExpensesList />, { route: '/expenses?from=2026-08-01&to=2026-08-15' })
  await screen.findByRole('list')
  expect(screen.queryByText('Teto do mês')).not.toBeInTheDocument()

  expect(calls).toHaveLength(0)
})

test('shows the month signal against the fake ceiling', async () => {
  fakePlan.monthly_ceiling_cents = 10000

  renderWithProviders(<ExpensesList />, { route: '/expenses?month=2026-08' })

  expect(
    await screen.findByText('R$ 84,90 de R$ 100,00 · 85%'),
  ).toBeInTheDocument()
  expect(screen.getByText('Atenção', { exact: true })).toBeInTheDocument()
  expect(screen.getByText(/Sobram R\$ 15,10/)).toBeInTheDocument()
})
