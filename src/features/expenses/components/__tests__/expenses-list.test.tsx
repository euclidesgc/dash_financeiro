import { http, HttpResponse } from 'msw'
import { expect, test } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, within } from '@testing-library/react'

import { ExpensesList } from '@/features/expenses/components/expenses-list'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'

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
