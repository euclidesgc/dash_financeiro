import { http, HttpResponse } from 'msw'
import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor, within } from '@testing-library/react'

import { NotExpenseControl } from '@/features/expenses/components/not-expense-control'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import type { Expense, ExpenseView, NotExpenseReason } from '@/features/expenses/types/expense'

const BASE: Expense = {
  id: 44,
  date: '2026-08-01',
  description: 'GASTO 44',
  payee_name: null,
  account_name: 'Conta corrente',
  account_institution: 'Banco de teste',
  account_type: 'BANK',
  account_id: 'acc-bank-1',
  category: 'Compras',
  category_key: 'Shopping',
  category_source: 'auto',
  amount_cents: -4400,
  not_expense_reason: null,
}

interface PutCall {
  id: string
  body: { reason: NotExpenseReason }
}

function spyOnPut(): PutCall[] {
  const calls: PutCall[] = []
  server.use(
    http.put('/api/transactions/:id/not-expense', async ({ params, request }) => {
      const body = (await request.json()) as { reason: NotExpenseReason }
      calls.push({ id: params.id as string, body })
      return HttpResponse.json({ ...BASE, not_expense_reason: body.reason })
    }),
  )
  return calls
}

function spyOnPendingPut(): { calls: PutCall[]; release: () => void } {
  const calls: PutCall[] = []
  let resolvePromise: () => void = () => {
    /* replaced below */
  }
  const promise = new Promise<void>((resolve) => {
    resolvePromise = resolve
  })
  server.use(
    http.put('/api/transactions/:id/not-expense', async ({ params, request }) => {
      const body = (await request.json()) as { reason: NotExpenseReason }
      calls.push({ id: params.id as string, body })
      await promise
      return HttpResponse.json({ ...BASE, not_expense_reason: body.reason })
    }),
  )
  return { calls, release: resolvePromise }
}

interface DeleteCall {
  id: string
}

function spyOnDelete(): DeleteCall[] {
  const calls: DeleteCall[] = []
  server.use(
    http.delete('/api/transactions/:id/not-expense', ({ params }) => {
      calls.push({ id: params.id as string })
      return HttpResponse.json({ ...BASE, not_expense_reason: null })
    }),
  )
  return calls
}

function renderControl(
  view: ExpenseView,
  onExcluded = vi.fn(),
  expense: Expense = BASE,
) {
  return {
    onExcluded,
    ...renderWithProviders(
      <NotExpenseControl expense={expense} view={view} onExcluded={onExcluded} />,
    ),
  }
}

test('shows "Não é gasto" and no combobox when closed', () => {
  renderControl('expenses')

  const button = screen.getByRole('button', { name: 'Marcar GASTO 44 como não-gasto' })
  expect(button).toHaveTextContent('Não é gasto')
  expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
})

test('uses "Sem descrição" in the accessible name when the description is null', () => {
  renderControl('expenses', vi.fn(), { ...BASE, description: null })

  expect(
    screen.getByRole('button', { name: 'Marcar Sem descrição como não-gasto' }),
  ).toBeInTheDocument()
})

test('opens the reason select with focus and "Transferência entre minhas contas" selected', async () => {
  renderControl('expenses')

  await userEvent.click(screen.getByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }))

  const combobox = screen.getByRole('combobox', { name: 'Motivo' })
  expect(combobox).toHaveFocus()
  expect(combobox).toHaveValue('own_transfer')
  const options = within(combobox).getAllByRole('option')
  expect(options.map((option) => option.textContent)).toEqual([
    'Transferência entre minhas contas',
    'Estorno',
    'Outro',
  ])
  expect(screen.getByRole('button', { name: 'Confirmar' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Cancelar' })).toBeInTheDocument()
  expect(
    screen.queryByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }),
  ).not.toBeInTheDocument()
})

test('"Cancelar" closes without calling the API', async () => {
  const calls = spyOnPut()
  renderControl('expenses')

  await userEvent.click(screen.getByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }))
  await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

  expect(calls.length).toBe(0)
  expect(
    screen.getByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }),
  ).toBeInTheDocument()
})

test('Escape closes without calling the API', async () => {
  const calls = spyOnPut()
  renderControl('expenses')

  await userEvent.click(screen.getByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }))
  await userEvent.type(screen.getByRole('combobox', { name: 'Motivo' }), '{Escape}')

  expect(calls.length).toBe(0)
  expect(
    screen.getByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }),
  ).toBeInTheDocument()
})

test('"Confirmar" with "Estorno" sends PUT with reason refund, shows "Salvando…" and calls onExcluded', async () => {
  const onExcluded = vi.fn()
  const { calls, release } = spyOnPendingPut()
  renderControl('expenses', onExcluded)

  await userEvent.click(screen.getByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }))
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Motivo' }), 'refund')
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

  const savingButton = screen.getByRole('button', { name: 'Salvando…' })
  expect(savingButton).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Cancelar' })).toBeDisabled()

  release()

  await waitFor(() => {
    expect(calls).toEqual([{ id: '44', body: { reason: 'refund' } }])
  })
  await waitFor(() => {
    expect(onExcluded).toHaveBeenCalledTimes(1)
  })
  expect(onExcluded).toHaveBeenCalledWith({ id: 44, description: 'GASTO 44' })
  expect(
    await screen.findByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }),
  ).toBeInTheDocument()
})

test('clicking "Confirmar" twice while pending sends one call', async () => {
  const { calls, release } = spyOnPendingPut()
  renderControl('expenses')

  await userEvent.click(screen.getByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }))
  await userEvent.dblClick(screen.getByRole('button', { name: 'Confirmar' }))

  expect(calls.length).toBe(1)
  release()
})

test('a 500 shows the alert and "Tentar de novo" repeats the same call', async () => {
  const calls: PutCall[] = []
  let first = true
  server.use(
    http.put('/api/transactions/:id/not-expense', async ({ params, request }) => {
      const body = (await request.json()) as { reason: NotExpenseReason }
      calls.push({ id: params.id as string, body })
      if (first) {
        first = false
        return HttpResponse.json({ detail: 'erro' }, { status: 500 })
      }
      return HttpResponse.json({ ...BASE, not_expense_reason: body.reason })
    }),
  )
  const onExcluded = vi.fn()
  renderControl('expenses', onExcluded)

  await userEvent.click(screen.getByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }))
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Motivo' }), 'refund')
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível marcar como não-gasto.')
  expect(screen.getByRole('combobox', { name: 'Motivo' })).toHaveValue('refund')

  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  await waitFor(() => {
    expect(calls.length).toBe(2)
  })
  expect(calls[1]).toEqual({ id: '44', body: { reason: 'refund' } })
  await waitFor(() => {
    expect(onExcluded).toHaveBeenCalledTimes(1)
  })
})

test('saving invalidates the expenses queries', async () => {
  spyOnPut()
  const { queryClient } = renderControl('expenses')
  const spy = vi.spyOn(queryClient, 'invalidateQueries')

  await userEvent.click(screen.getByRole('button', { name: 'Marcar GASTO 44 como não-gasto' }))
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

  await waitFor(() => {
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['expenses'] }))
  })
})

test('in the excluded view shows "Voltar a ser gasto" that sends DELETE', async () => {
  const calls = spyOnDelete()
  const { queryClient } = renderControl('excluded', vi.fn(), {
    ...BASE,
    not_expense_reason: 'refund',
  })
  const spy = vi.spyOn(queryClient, 'invalidateQueries')

  const button = screen.getByRole('button', { name: 'Voltar GASTO 44 a ser gasto' })
  expect(button).toHaveTextContent('Voltar a ser gasto')

  await userEvent.click(button)

  await waitFor(() => {
    expect(calls).toEqual([{ id: '44' }])
  })
  await waitFor(() => {
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['expenses'] }))
  })
})

test('in the excluded view a 500 shows the alert and "Tentar de novo" repeats', async () => {
  const calls: DeleteCall[] = []
  let first = true
  server.use(
    http.delete('/api/transactions/:id/not-expense', ({ params }) => {
      calls.push({ id: params.id as string })
      if (first) {
        first = false
        return HttpResponse.json({ detail: 'erro' }, { status: 500 })
      }
      return HttpResponse.json({ ...BASE, not_expense_reason: null })
    }),
  )
  renderControl('excluded', vi.fn(), { ...BASE, not_expense_reason: 'refund' })

  await userEvent.click(screen.getByRole('button', { name: 'Voltar GASTO 44 a ser gasto' }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível voltar a contar como gasto.')

  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  await waitFor(() => {
    expect(calls.length).toBe(2)
  })
})
