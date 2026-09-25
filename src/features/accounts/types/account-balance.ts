export type AccountType = 'BANK' | 'CREDIT'

export interface AccountBalance {
  id: string
  name: string | null
  institution: string | null
  type: AccountType | null
  subtype: string | null
  balance_cents: number
  updated_at: string | null
}

export interface BalancesResponse {
  accounts: AccountBalance[]
}
