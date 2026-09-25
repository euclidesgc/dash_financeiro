import type { CategorySignal, ExpensesQuery } from '@/features/expenses/types/expense'

export interface PlanCeiling {
  monthly_ceiling_cents: number | null
}

export interface MonthSignal {
  scope: 'month' | 'none'
  spent_cents: number
  ceiling_cents: number | null
  signal: CategorySignal | null
  remaining_cents: number | null
}

export type MonthSignalQuery = Pick<ExpensesQuery, 'from' | 'to'>
