import { http, HttpResponse, delay } from 'msw'
import { expect, test } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor } from '@testing-library/react'

import { PeriodResult } from '@/features/expenses/components/period-result'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import type { PeriodResultQuery, PeriodResultResponse } from '@/features/expenses/types/expense'

const QUERY: PeriodResultQuery = { from: '2026-09-01', to: '2026-09-30', account: null, search: null }

function respondWith(body: PeriodResultResponse): void {
  server.use(http.get('/api/transactions/expenses/period-result', () => HttpResponse.json(body)))
}

test('shows the loading state with role status', async () => {
  server.use(
    http.get('/api/transactions/expenses/period-result', async () => {
      await delay('infinite')
      return HttpResponse.json({})
    }),
  )
  renderWithProviders(<PeriodResult query={QUERY} />)

  expect(await screen.findByRole('status')).toHaveTextContent('Carregando resultado do período…')
})

test('shows the alert and "Tentar de novo" refetches', async () => {
  const user = userEvent.setup()
  let attempt = 0
  server.use(
    http.get('/api/transactions/expenses/period-result', () => {
      attempt += 1
      if (attempt === 1) {
        return HttpResponse.json({}, { status: 500 })
      }
      return HttpResponse.json({ income_cents: 600000, spending_cents: -23490, balance_cents: 576510 })
    }),
  )
  renderWithProviders(<PeriodResult query={QUERY} />)

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar o resultado do período.')

  await user.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  expect(await screen.findByText('R$ 6.000,00')).toBeInTheDocument()
})

test('shows "Entradas", "Gastos" and "Saldo" with the colour of each sign', async () => {
  respondWith({ income_cents: 600000, spending_cents: -23490, balance_cents: 576510 })
  renderWithProviders(<PeriodResult query={QUERY} />)

  const region = await screen.findByRole('region', { name: 'Resultado do período' })
  const terms = region.querySelectorAll('dt')
  expect(Array.from(terms).map((term) => term.textContent)).toEqual(['Entradas', 'Gastos', 'Saldo'])

  expect(screen.getByText('R$ 6.000,00')).toHaveClass('text-green-700')
  expect(screen.getByText('R$ 234,90')).toHaveClass('text-red-700')
  expect(screen.getByText('R$ 5.765,10')).toHaveClass('text-green-700')
})

test('shows a negative balance in red with the minus sign', async () => {
  respondWith({ income_cents: 0, spending_cents: -23490, balance_cents: -23490 })
  renderWithProviders(<PeriodResult query={QUERY} />)

  await screen.findByRole('region', { name: 'Resultado do período' })

  expect(screen.getByText('−R$ 234,90')).toHaveClass('text-red-700')
  expect(screen.getByText('R$ 0,00')).toHaveClass('text-green-700')
})

test('shows a zero balance in the neutral colour', async () => {
  respondWith({ income_cents: 10000, spending_cents: -10000, balance_cents: 0 })
  renderWithProviders(<PeriodResult query={QUERY} />)

  await screen.findByRole('region', { name: 'Resultado do período' })

  expect(screen.getByText('R$ 0,00')).toHaveClass('text-gray-900')
})

test('sends from, to, account_id and q to the API', async () => {
  const calls: URLSearchParams[] = []
  server.use(
    http.get('/api/transactions/expenses/period-result', ({ request }) => {
      const url = new URL(request.url)
      calls.push(url.searchParams)
      return HttpResponse.json({ income_cents: 0, spending_cents: 0, balance_cents: 0 })
    }),
  )

  const query: PeriodResultQuery = {
    from: '2026-09-01',
    to: '2026-09-30',
    account: 'acc-bank-1',
    search: 'sal',
  }
  renderWithProviders(<PeriodResult query={query} />)

  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('from')).toBe('2026-09-01')
    expect(last?.get('to')).toBe('2026-09-30')
    expect(last?.get('account_id')).toBe('acc-bank-1')
    expect(last?.get('q')).toBe('sal')
  })

  renderWithProviders(<PeriodResult query={QUERY} />)

  await waitFor(() => {
    const last = calls.at(-1)
    expect(last?.get('account_id')).toBeNull()
    expect(last?.get('q')).toBeNull()
  })
})
