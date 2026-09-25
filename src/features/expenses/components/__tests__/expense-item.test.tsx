import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen } from '@testing-library/react'

import { ExpenseItem } from '@/features/expenses/components/expense-item'
import { renderWithProviders } from '@/testing/test-utils'
import type { Expense } from '@/features/expenses/types/expense'

const EXPENSE: Expense = {
  id: 44,
  date: '2026-09-01',
  description: 'POSTO CENTRAL',
  payee_name: null,
  account_name: 'Conta de teste',
  account_institution: 'Banco de teste',
  account_type: 'BANK',
  account_id: 'acc-bank-1',
  category: 'Casa',
  category_key: 'Housing',
  category_source: 'auto',
  amount_cents: -15000,
  not_expense_reason: null,
}

test('opens the not-expense reason picker below the row, outside the description line', async () => {
  renderWithProviders(
    <ul>
      <ExpenseItem
        expense={EXPENSE}
        categories={[]}
        categoriesReady={false}
        view="expenses"
        onExcluded={vi.fn()}
      />
    </ul>,
  )

  await userEvent.click(screen.getByRole('button', { name: 'Marcar POSTO CENTRAL como não-gasto' }))

  const select = screen.getByRole('combobox', { name: 'Motivo' })
  const row = screen.getByText('POSTO CENTRAL').parentElement?.parentElement
  expect(row).toBeDefined()
  expect(row).not.toContainElement(select)
  expect(screen.getByRole('listitem')).toContainElement(select)
})
