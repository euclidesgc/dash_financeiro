export interface Expense {
  id: number
  date: string
  description: string | null
  payee_name: string | null
  account_name: string | null
  account_institution: string | null
  account_type: 'BANK' | 'CREDIT' | null
  category: string | null
  amount_cents: number
}

export interface ExpensesResponse {
  items: Expense[]
  page: number
  page_size: number
  total: number
  total_cents: number
}

export type ExpenseSort = 'date' | 'amount' | 'category'
export type ExpenseOrder = 'asc' | 'desc'

export interface ExpensesQuery {
  page: number
  sort: ExpenseSort
  order: ExpenseOrder
  from: string | null
  to: string | null
}

export type Period =
  | { kind: 'all' }
  | { kind: 'month'; month: string }
  | { kind: 'range'; from: string | null; to: string | null }
