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
}
