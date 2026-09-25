import { http, HttpResponse, delay } from 'msw'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, within } from '@testing-library/react'

import { MonthPlanCard } from '@/features/expenses/components/month-plan-card'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import type { MonthSignal } from '@/features/expenses/types/ceiling'

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 8, 25, 12))
})

afterEach(() => {
  vi.useRealTimers()
})

function respondWith(signal: Partial<MonthSignal>, balanceCents = -12345): string[] {
  const requested: string[] = []
  const body: MonthSignal = {
    scope: 'month',
    spent_cents: 80000,
    ceiling_cents: 100000,
    signal: 'within',
    remaining_cents: 20000,
    ...signal,
  }
  server.use(
    http.get('/api/transactions/expenses/month-signal', ({ request }) => {
      requested.push(new URL(request.url).search)
      return HttpResponse.json(body)
    }),
    http.get('/api/transactions/expenses/period-result', ({ request }) => {
      requested.push(new URL(request.url).search)
      return HttpResponse.json({
        income_cents: 500000,
        spending_cents: -512345,
        balance_cents: balanceCents,
      })
    }),
  )
  return requested
}

test('asks both endpoints for the whole current month', async () => {
  const requested = respondWith({})
  renderWithProviders(<MonthPlanCard />)

  await screen.findByRole('heading', { name: 'Plano de setembro de 2026' })
  expect(requested).toHaveLength(2)
  for (const search of requested) {
    expect(search).toContain('from=2026-09-01')
    expect(search).toContain('to=2026-09-30')
  }
})

test('shows spent, ceiling, signal, result and what is left', async () => {
  respondWith({})
  renderWithProviders(<MonthPlanCard />)

  const card = await screen.findByRole('region', { name: 'Plano de setembro de 2026' })
  expect(within(card).getByText('Gasto no mês').nextSibling).toHaveTextContent('R$ 800,00')
  expect(within(card).getByText('Dentro')).toBeInTheDocument()
  expect(within(card).getByText('Teto do mês').nextSibling).toHaveTextContent('R$ 1.000,00')
  expect(within(card).getByText('Resultado até hoje').nextSibling).toHaveTextContent(
    '−R$ 123,45',
  )
  expect(within(card).getByText(/Sobram R\$\s200,00 até o teto/)).toBeInTheDocument()
  expect(within(card).getByRole('link', { name: 'Ver o mês em detalhe' })).toHaveAttribute(
    'href',
    '/expenses?month=2026-09',
  )
})

test('shows how much passed the ceiling when over', async () => {
  respondWith({ spent_cents: 110000, signal: 'over', remaining_cents: -10000 })
  renderWithProviders(<MonthPlanCard />)

  expect(await screen.findByText(/Passou R\$\s100,00 do teto/)).toBeInTheDocument()
  expect(screen.getByText('Acima')).toBeInTheDocument()
})

test('without a ceiling, invites to define it on the expenses page', async () => {
  respondWith({ ceiling_cents: null, signal: null, remaining_cents: null })
  renderWithProviders(<MonthPlanCard />)

  expect(await screen.findByText('Sem teto')).toBeInTheDocument()
  expect(screen.getByText(/Sem teto definido/)).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Definir o teto do mês' })).toHaveAttribute(
    'href',
    '/expenses?month=2026-09',
  )
})

test('shows the loading state with role status', async () => {
  server.use(
    http.get('/api/transactions/expenses/month-signal', async () => {
      await delay('infinite')
      return HttpResponse.json({})
    }),
  )
  renderWithProviders(<MonthPlanCard />)

  expect(await screen.findByRole('status')).toHaveTextContent('Carregando o plano do mês…')
})

test('shows the alert and "Tentar de novo" refetches when period-result fails', async () => {
  const user = userEvent.setup()
  respondWith({})
  let attempt = 0
  server.use(
    http.get('/api/transactions/expenses/period-result', () => {
      attempt += 1
      if (attempt === 1) {
        return HttpResponse.json({ detail: 'erro' }, { status: 500 })
      }
      return HttpResponse.json({ income_cents: 0, spending_cents: 0, balance_cents: 0 })
    }),
  )
  renderWithProviders(<MonthPlanCard />)

  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Não foi possível carregar o plano do mês.',
  )
  await user.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  expect(
    await screen.findByRole('heading', { name: 'Plano de setembro de 2026' }),
  ).toBeInTheDocument()
})
