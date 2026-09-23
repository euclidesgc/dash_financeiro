import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { render, screen } from '@testing-library/react'

import { AccountSelect, accountOptionLabel } from '@/features/expenses/components/account-select'
import { fakeAccounts } from '@/testing/mocks/handlers'
import type { ExpenseAccount } from '@/features/expenses/types/expense'

const accounts: ExpenseAccount[] = fakeAccounts.map((account) => ({
  id: account.id,
  name: account.name,
  institution: account.institution,
  type: account.type as ExpenseAccount['type'],
}))

test('shows only "Todas as contas" disabled while the accounts load', () => {
  render(
    <AccountSelect
      value={null}
      accounts={accounts}
      isPending={true}
      isError={false}
      onChange={vi.fn()}
      onRetry={vi.fn()}
    />,
  )

  const select = screen.getByLabelText('Conta')
  expect(select).toBeDisabled()
  expect(select).toHaveAttribute('aria-busy', 'true')
  expect(screen.getAllByRole('option')).toHaveLength(1)
  expect(screen.getByRole('option', { name: 'Todas as contas' })).toBeInTheDocument()
})

test('lists every account with its kind', () => {
  render(
    <AccountSelect
      value={null}
      accounts={accounts}
      isPending={false}
      isError={false}
      onChange={vi.fn()}
      onRetry={vi.fn()}
    />,
  )

  const options = screen.getAllByRole('option')
  expect(options.map((option) => option.textContent)).toEqual([
    'Todas as contas',
    'Conta corrente · Banco de teste (Conta)',
    'Cartão · Emissor de teste (Cartão)',
  ])
  expect(options[1]).toHaveValue('acc-bank-1')
  expect(options[2]).toHaveValue('acc-credit-1')
})

test('falls back to "Conta sem nome" when name and institution are null', () => {
  const { rerender } = render(
    <AccountSelect
      value={null}
      accounts={[{ id: 'x', name: null, institution: null, type: 'BANK' }]}
      isPending={false}
      isError={false}
      onChange={vi.fn()}
      onRetry={vi.fn()}
    />,
  )

  expect(screen.getByRole('option', { name: 'Conta sem nome (Conta)' })).toBeInTheDocument()

  rerender(
    <AccountSelect
      value={null}
      accounts={[{ id: 'y', name: 'Nubank', institution: null, type: 'CREDIT' }]}
      isPending={false}
      isError={false}
      onChange={vi.fn()}
      onRetry={vi.fn()}
    />,
  )

  expect(screen.getByRole('option', { name: 'Nubank (Cartão)' })).toBeInTheDocument()
})

test('selects the account from the value', () => {
  render(
    <AccountSelect
      value="acc-credit-1"
      accounts={accounts}
      isPending={false}
      isError={false}
      onChange={vi.fn()}
      onRetry={vi.fn()}
    />,
  )

  expect(screen.getByLabelText('Conta')).toHaveValue('acc-credit-1')
})

test('falls back to "Todas as contas" on an unknown value', () => {
  render(
    <AccountSelect
      value="nao-existe"
      accounts={accounts}
      isPending={false}
      isError={false}
      onChange={vi.fn()}
      onRetry={vi.fn()}
    />,
  )

  expect(screen.getByLabelText('Conta')).toHaveValue('')
})

test('choosing an account calls onChange with its id', async () => {
  const onChange = vi.fn()

  render(
    <AccountSelect
      value={null}
      accounts={accounts}
      isPending={false}
      isError={false}
      onChange={onChange}
      onRetry={vi.fn()}
    />,
  )

  await userEvent.selectOptions(screen.getByLabelText('Conta'), 'acc-credit-1')

  expect(onChange).toHaveBeenCalledWith('acc-credit-1')
})

test('choosing "Todas as contas" calls onChange with null', async () => {
  const onChange = vi.fn()

  render(
    <AccountSelect
      value="acc-credit-1"
      accounts={accounts}
      isPending={false}
      isError={false}
      onChange={onChange}
      onRetry={vi.fn()}
    />,
  )

  await userEvent.selectOptions(screen.getByLabelText('Conta'), '')

  expect(onChange).toHaveBeenCalledWith(null)
})

test('shows the error with a retry action and keeps the select usable', async () => {
  const onRetry = vi.fn()

  render(
    <AccountSelect
      value={null}
      accounts={accounts}
      isPending={false}
      isError={true}
      onChange={vi.fn()}
      onRetry={onRetry}
    />,
  )

  expect(screen.getByRole('alert')).toHaveTextContent('Não foi possível carregar as contas.')
  const select = screen.getByLabelText('Conta')
  expect(select).toBeEnabled()
  expect(screen.getAllByRole('option')).toHaveLength(1)

  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  expect(onRetry).toHaveBeenCalledTimes(1)
})

test('accountOptionLabel joins name and institution', () => {
  expect(
    accountOptionLabel({ id: 'a', name: 'Conta corrente', institution: 'Banco de teste', type: 'BANK' }),
  ).toBe('Conta corrente · Banco de teste (Conta)')
  expect(accountOptionLabel({ id: 'b', name: null, institution: 'Banco', type: 'CREDIT' })).toBe(
    'Banco (Cartão)',
  )
  expect(accountOptionLabel({ id: 'c', name: 'Banco', institution: null, type: null })).toBe(
    'Banco (Conta)',
  )
})
