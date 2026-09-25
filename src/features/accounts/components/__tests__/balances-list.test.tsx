import { http, HttpResponse } from 'msw'
import { expect, test } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen } from '@testing-library/react'

import { BalancesList } from '@/features/accounts/components/balances-list'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'

test('shows the loading state', () => {
  renderWithProviders(<BalancesList />)

  expect(screen.getByRole('status')).toHaveTextContent('Carregando saldos…')
})

test('shows the empty state', async () => {
  server.use(http.get('/api/accounts/balances', () => HttpResponse.json({ accounts: [] })))

  renderWithProviders(<BalancesList />)

  expect(
    await screen.findByText(
      'Nenhuma conta trazida do banco ainda. Use “Atualizar agora” para buscar suas contas e cartões.',
    ),
  ).toBeInTheDocument()
})

test('shows the error state and retries', async () => {
  let attempt = 0
  server.use(
    http.get('/api/accounts/balances', () => {
      attempt += 1
      if (attempt === 1) {
        return HttpResponse.json({}, { status: 500 })
      }
      return HttpResponse.json({
        accounts: [
          {
            id: '1',
            name: 'Conta corrente',
            institution: 'Banco de teste',
            type: 'BANK',
            subtype: null,
            balance_cents: 123456,
            updated_at: '2026-09-05T21:36:27.516Z',
          },
        ],
      })
    }),
  )

  renderWithProviders(<BalancesList />)

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar os saldos.')

  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  expect(await screen.findByText('Conta corrente')).toBeInTheDocument()
})

test('renders accounts with the negative balance in red', async () => {
  server.use(
    http.get('/api/accounts/balances', () =>
      HttpResponse.json({
        accounts: [
          {
            id: 'bank-1',
            name: 'Conta corrente',
            institution: 'Banco de teste',
            type: 'BANK',
            subtype: null,
            balance_cents: 123456,
            updated_at: '2026-09-05T21:36:27.516Z',
          },
          {
            id: 'credit-1',
            name: 'Cartão',
            institution: 'Emissor de teste',
            type: 'CREDIT',
            subtype: null,
            balance_cents: -54321,
            updated_at: null,
          },
        ],
      }),
    ),
  )

  renderWithProviders(<BalancesList />)

  const bankRow = (await screen.findByText('Banco de teste')).closest('li')
  const creditRow = screen.getByText('Emissor de teste').closest('li')

  expect(bankRow).not.toBeNull()
  expect(creditRow).not.toBeNull()
  expect(bankRow?.querySelector('.text-gray-900')).not.toBeNull()
  expect(creditRow?.querySelector('.text-red-700')).not.toBeNull()
})

test('shows "Sem data de atualização" when updated_at is null', async () => {
  server.use(
    http.get('/api/accounts/balances', () =>
      HttpResponse.json({
        accounts: [
          {
            id: 'credit-1',
            name: 'Cartão',
            institution: 'Emissor de teste',
            type: 'CREDIT',
            subtype: null,
            balance_cents: -54321,
            updated_at: null,
          },
        ],
      }),
    ),
  )

  renderWithProviders(<BalancesList />)

  expect(await screen.findByText('Sem data de atualização')).toBeInTheDocument()
})

test('shows "Saldo informado pelo banco em" with the formatted date', async () => {
  server.use(
    http.get('/api/accounts/balances', () =>
      HttpResponse.json({
        accounts: [
          {
            id: 'bank-1',
            name: 'Conta corrente',
            institution: 'Banco de teste',
            type: 'BANK',
            subtype: null,
            balance_cents: 123456,
            updated_at: '2026-09-05T21:36:27.516Z',
          },
        ],
      }),
    ),
  )

  renderWithProviders(<BalancesList />)

  expect(await screen.findByText(/Saldo informado pelo banco em 05\/09\/2026/)).toBeInTheDocument()
})
