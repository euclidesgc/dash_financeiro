import { expect, test } from 'vitest'
import { z } from 'zod'

import type { Expense } from '@/features/expenses/types/expense'
import contract from '@/testing/contracts/expense-views.json'
import { fakeExpenses, matchesView } from '@/testing/mocks/handlers'

const VIEWS = ['expenses', 'income', 'excluded'] as const
type View = (typeof VIEWS)[number]

const contractSchema = z.object({
  cases: z.array(
    z.object({
      name: z.string(),
      amount_cents: z.number().int(),
      not_expense_reason: z.enum(['own_transfer', 'refund', 'other']).nullable(),
      views: z.array(z.enum(VIEWS)),
    }),
  ),
})

const { cases } = contractSchema.parse(contract)

test.each(cases)('the mock places $name in the same views as the API', (contractCase) => {
  const placed = VIEWS.filter((view) => matchesView(contractCase, view))

  expect(placed).toEqual(contractCase.views)
})

test('the mock period result adds income and spending from the same views', async () => {
  const [template] = fakeExpenses
  const rows: Expense[] = cases.map((contractCase, index) => ({
    ...template,
    id: 1000 + index,
    date: '2026-08-01',
    amount_cents: contractCase.amount_cents,
    not_expense_reason: contractCase.not_expense_reason,
  }))
  fakeExpenses.splice(0, fakeExpenses.length, ...rows)
  const expected = (view: View) =>
    cases
      .filter((contractCase) => contractCase.views.includes(view))
      .reduce((sum, contractCase) => sum + contractCase.amount_cents, 0)

  const response = await fetch('/api/transactions/expenses/period-result')
  const body: unknown = await response.json()

  expect(body).toEqual({
    income_cents: expected('income'),
    spending_cents: expected('expenses'),
    balance_cents: expected('income') + expected('expenses'),
  })
})
