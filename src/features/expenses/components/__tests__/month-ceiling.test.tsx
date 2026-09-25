import { http, HttpResponse, delay } from 'msw'
import { expect, test } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor, within } from '@testing-library/react'

import { MonthCeiling } from '@/features/expenses/components/month-ceiling'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import type { MonthSignal, MonthSignalQuery } from '@/features/expenses/types/ceiling'

const MONTH: MonthSignalQuery = { from: '2026-08-01', to: '2026-08-31' }

function respondWith(signal: Partial<MonthSignal>, ceiling?: number | null): void {
  const body: MonthSignal = {
    scope: 'month',
    spent_cents: 10500,
    ceiling_cents: 10000,
    signal: 'over',
    remaining_cents: -500,
    ...signal,
  }
  server.use(
    http.get('/api/transactions/expenses/month-signal', () => HttpResponse.json(body)),
    http.get('/api/plan/ceiling', () =>
      HttpResponse.json({
        monthly_ceiling_cents: ceiling !== undefined ? ceiling : (body.ceiling_cents ?? 10000),
      }),
    ),
  )
}

test('shows the loading state with role status', async () => {
  server.use(
    http.get('/api/transactions/expenses/month-signal', async () => {
      await delay('infinite')
      return HttpResponse.json({})
    }),
  )
  renderWithProviders(<MonthCeiling query={MONTH} />)

  expect(await screen.findByRole('status')).toHaveTextContent('Carregando teto do mês…')
})

test('shows the alert and "Tentar de novo" refetches when month-signal fails', async () => {
  const user = userEvent.setup()
  let attempt = 0
  server.use(
    http.get('/api/transactions/expenses/month-signal', () => {
      attempt += 1
      if (attempt === 1) {
        return HttpResponse.json({}, { status: 500 })
      }
      return HttpResponse.json({
        scope: 'month',
        spent_cents: 10500,
        ceiling_cents: 10000,
        signal: 'over',
        remaining_cents: -500,
      })
    }),
    http.get('/api/plan/ceiling', () => HttpResponse.json({ monthly_ceiling_cents: 10000 })),
  )
  renderWithProviders(<MonthCeiling query={MONTH} />)

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar o teto do mês.')

  await user.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  expect(await screen.findByText('R$ 105,00 de R$ 100,00 · 105%')).toBeInTheDocument()
})

test('shows the alert when the plan ceiling fails', async () => {
  server.use(
    http.get('/api/transactions/expenses/month-signal', () =>
      HttpResponse.json({
        scope: 'month',
        spent_cents: 10500,
        ceiling_cents: 10000,
        signal: 'over',
        remaining_cents: -500,
      }),
    ),
    http.get('/api/plan/ceiling', () => HttpResponse.json({}, { status: 500 })),
  )
  renderWithProviders(<MonthCeiling query={MONTH} />)

  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Não foi possível carregar o teto do mês.',
  )
})

test('renders nothing when the scope is none', async () => {
  respondWith({ scope: 'none', signal: null, remaining_cents: null })
  const { container } = renderWithProviders(<MonthCeiling query={MONTH} />)

  await waitFor(() => {
    expect(container).not.toHaveTextContent('Teto do mês')
  })
})

test('shows "Acima" and "Passou" over the ceiling', async () => {
  respondWith({})
  renderWithProviders(<MonthCeiling query={MONTH} />)

  expect(await screen.findByText('R$ 105,00 de R$ 100,00 · 105%')).toBeInTheDocument()
  expect(screen.getByText('Acima', { exact: true })).toBeInTheDocument()
  expect(screen.getByText(/Passou R\$ 5,00/)).toBeInTheDocument()
})

test('shows "Dentro" and "Sobram" within the ceiling', async () => {
  respondWith({ ceiling_cents: 20000, signal: 'within', remaining_cents: 9500 })
  renderWithProviders(<MonthCeiling query={MONTH} />)

  expect(await screen.findByText('R$ 105,00 de R$ 200,00 · 53%')).toBeInTheDocument()
  expect(screen.getByText('Dentro', { exact: true })).toBeInTheDocument()
  expect(screen.getByText(/Sobram R\$ 95,00/)).toBeInTheDocument()
})

test('shows "Atenção" near the ceiling', async () => {
  respondWith({ ceiling_cents: 12000, signal: 'warning', remaining_cents: 1500 })
  renderWithProviders(<MonthCeiling query={MONTH} />)

  expect(await screen.findByText(/88%/)).toBeInTheDocument()
  expect(screen.getByText('Atenção', { exact: true })).toBeInTheDocument()
  expect(screen.getByText(/Sobram R\$ 15,00/)).toBeInTheDocument()
})

test('shows "Sobram R$ 0,00" at the exact ceiling', async () => {
  respondWith({ ceiling_cents: 10500, signal: 'warning', remaining_cents: 0 })
  renderWithProviders(<MonthCeiling query={MONTH} />)

  expect(await screen.findByText(/Sobram R\$ 0,00/)).toBeInTheDocument()
})

test('without a ceiling shows the invitation with the form open and focused, no badge and no percentage', async () => {
  respondWith({ ceiling_cents: null, signal: null, remaining_cents: null }, null)
  renderWithProviders(<MonthCeiling query={MONTH} />)

  expect(
    await screen.findByText('Sem teto definido. Defina um teto para saber se o mês cabe no plano.'),
  ).toBeInTheDocument()
  const field = screen.getByLabelText('Teto mensal (R$)')
  expect(field).toHaveFocus()
  expect(field).toHaveValue('')
  expect(screen.queryByText('Dentro', { exact: true })).not.toBeInTheDocument()
  expect(screen.queryByText('Atenção', { exact: true })).not.toBeInTheDocument()
  expect(screen.queryByText('Acima', { exact: true })).not.toBeInTheDocument()
  expect(screen.queryByText('%')).not.toBeInTheDocument()
})

test('"Cancelar" without a ceiling hides the form and "Definir teto" reopens it', async () => {
  const user = userEvent.setup()
  respondWith({ ceiling_cents: null, signal: null, remaining_cents: null }, null)
  renderWithProviders(<MonthCeiling query={MONTH} />)

  await screen.findByLabelText('Teto mensal (R$)')

  await user.click(screen.getByRole('button', { name: 'Cancelar' }))

  expect(screen.queryByLabelText('Teto mensal (R$)')).not.toBeInTheDocument()
  expect(
    screen.getByText('Sem teto definido. Defina um teto para saber se o mês cabe no plano.'),
  ).toBeInTheDocument()
  const reopen = screen.getByRole('button', { name: 'Definir teto do mês' })
  expect(reopen).toBeInTheDocument()

  await user.click(reopen)

  expect(screen.getByLabelText('Teto mensal (R$)')).toHaveFocus()
})

test('"Alterar teto" opens the form with the current value and "Cancelar" restores the panel', async () => {
  const user = userEvent.setup()
  respondWith({})
  renderWithProviders(<MonthCeiling query={MONTH} />)

  await screen.findByText('R$ 105,00 de R$ 100,00 · 105%')

  await user.click(screen.getByRole('button', { name: 'Alterar teto do mês' }))

  const field = screen.getByLabelText('Teto mensal (R$)')
  expect(field).toHaveValue('100,00')
  expect(screen.queryByText('105%')).not.toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Cancelar' }))

  expect(await screen.findByText('R$ 105,00 de R$ 100,00 · 105%')).toBeInTheDocument()
  expect(screen.queryByLabelText('Teto mensal (R$)')).not.toBeInTheDocument()
})

test('saving shows the numbers of the new response', async () => {
  const user = userEvent.setup()
  let saved = false
  server.use(
    http.put('/api/plan/ceiling', async ({ request }) => {
      const body = (await request.json()) as { monthly_ceiling_cents: number | null }
      saved = true
      return HttpResponse.json({ monthly_ceiling_cents: body.monthly_ceiling_cents })
    }),
    http.get('/api/transactions/expenses/month-signal', () =>
      saved
        ? HttpResponse.json({
            scope: 'month',
            spent_cents: 10500,
            ceiling_cents: 20000,
            signal: 'within',
            remaining_cents: 9500,
          })
        : HttpResponse.json({
            scope: 'month',
            spent_cents: 10500,
            ceiling_cents: 10000,
            signal: 'over',
            remaining_cents: -500,
          }),
    ),
    http.get('/api/plan/ceiling', () =>
      HttpResponse.json({ monthly_ceiling_cents: saved ? 20000 : 10000 }),
    ),
  )
  renderWithProviders(<MonthCeiling query={MONTH} />)

  await screen.findByText('R$ 105,00 de R$ 100,00 · 105%')

  await user.click(screen.getByRole('button', { name: 'Alterar teto do mês' }))
  const field = screen.getByLabelText('Teto mensal (R$)')
  await user.clear(field)
  await user.type(field, '200{Enter}')

  expect(await screen.findByText('R$ 105,00 de R$ 200,00 · 53%')).toBeInTheDocument()
  expect(within(screen.getByRole('region')).getByText('Dentro', { exact: true })).toBeInTheDocument()
  expect(screen.getByText(/Sobram R\$ 95,00/)).toBeInTheDocument()
})

test('with a ceiling already set the button says "Alterar teto"', async () => {
  respondWith({})
  renderWithProviders(<MonthCeiling query={MONTH} />)

  await screen.findByText('R$ 105,00 de R$ 100,00 · 105%')

  expect(screen.getByRole('button', { name: 'Alterar teto do mês' })).toHaveTextContent(
    'Alterar teto',
  )
})
