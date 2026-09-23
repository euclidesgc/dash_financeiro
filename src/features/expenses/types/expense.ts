export interface Expense {
  id: number
  date: string
  description: string | null
  payee_name: string | null
  account_name: string | null
  account_institution: string | null
  account_type: 'BANK' | 'CREDIT' | null
  category: string | null
  category_key: string | null
  category_source: 'auto' | 'manual'
  amount_cents: number
  account_id: string | null
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
  account: string | null
  search: string | null
}

export interface CategoryGroup {
  category: string | null
  label: string
  count: number
  total_cents: number
}

export interface CategoryTotalsResponse {
  groups: CategoryGroup[]
  total_cents: number
}

export type CategoryTotalsQuery = Pick<ExpensesQuery, 'from' | 'to' | 'account' | 'search'>

export interface Category {
  key: string
  label: string
}

export interface CategoriesResponse {
  categories: Category[]
}

export type CategoryUpdateBody = { mode: 'manual'; category: string | null } | { mode: 'auto' }

export interface ExpenseAccount {
  id: string
  name: string | null
  institution: string | null
  type: 'BANK' | 'CREDIT' | null
}

export interface ExpenseAccountsResponse {
  accounts: ExpenseAccount[]
}

export type Period =
  | { kind: 'all' }
  | { kind: 'month'; month: string }
  | { kind: 'range'; from: string | null; to: string | null }
