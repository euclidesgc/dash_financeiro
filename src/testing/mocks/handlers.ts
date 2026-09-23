import { http, HttpResponse } from 'msw'
import type { SyncStatus } from '@/features/sync/types/sync-status'
import type { Expense } from '@/features/expenses/types/expense'

export const fakeUser = { login: 'teste' }

export const fakeAccounts = [
  {
    id: 'acc-bank-1',
    name: 'Conta corrente',
    institution: 'Banco de teste',
    type: 'BANK',
    subtype: 'CHECKING_ACCOUNT',
    balance_cents: 123456,
    updated_at: '2026-09-05T21:36:27.516Z',
  },
  {
    id: 'acc-credit-1',
    name: 'Cartão',
    institution: 'Emissor de teste',
    type: 'CREDIT',
    subtype: 'CREDIT_CARD',
    balance_cents: -54321,
    updated_at: null,
  },
]

export const fakeSyncStatus: SyncStatus = {
  running: false,
  last_run: { finished_at: '2026-09-22T11:15:00+00:00', status: 'ok', reason: null },
}

function generateFakeExpenses(): Expense[] {
  const total = 45
  const startDate = Date.UTC(2026, 7, 1)
  return Array.from({ length: total }, (_, index) => {
    const id = total - index
    const date = new Date(startDate - index * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)

    if (index === 0) {
      return {
        id,
        date,
        description: 'MERCADO DO BAIRRO',
        payee_name: 'Mercado do Bairro',
        account_name: 'Conta corrente',
        account_institution: 'Banco de teste',
        account_type: 'BANK',
        category: 'Compras',
        amount_cents: -8490,
      }
    }
    if (index === 1) {
      return {
        id,
        date,
        description: `GASTO ${String(id)}`,
        payee_name: null,
        account_name: 'Conta corrente',
        account_institution: 'Banco de teste',
        account_type: 'BANK',
        category: 'Alimentação',
        amount_cents: -1000 * id,
      }
    }
    if (index === 2) {
      return {
        id,
        date,
        description: null,
        payee_name: null,
        account_name: 'Conta corrente',
        account_institution: 'Banco de teste',
        account_type: 'BANK',
        category: null,
        amount_cents: -1000 * id,
      }
    }
    return {
      id,
      date,
      description: `GASTO ${String(id)}`,
      payee_name: null,
      account_name: 'Conta corrente',
      account_institution: 'Banco de teste',
      account_type: 'BANK',
      category: 'Compras',
      amount_cents: -1000 * id,
    }
  })
}

export const fakeExpenses: Expense[] = generateFakeExpenses()

let signedIn = false

export function resetSession(): void {
  signedIn = false
}

export const handlers = [
  http.post('/api/auth/login', async ({ request }) => {
    const body = (await request.json()) as { login: string; password: string }
    if (body.login === 'teste' && body.password === 'senha') {
      signedIn = true
      return new HttpResponse(null, { status: 204 })
    }
    return HttpResponse.json({ detail: 'Login ou senha inválidos.' }, { status: 401 })
  }),

  http.post('/api/auth/logout', () => {
    signedIn = false
    return new HttpResponse(null, { status: 204 })
  }),

  http.get('/api/auth/me', () => {
    if (!signedIn) {
      return HttpResponse.json({ detail: 'nao autenticado' }, { status: 401 })
    }
    return HttpResponse.json(fakeUser)
  }),

  http.get('/api/accounts/balances', () => {
    return HttpResponse.json({ accounts: fakeAccounts })
  }),

  http.get('/api/sync/status', () => {
    return HttpResponse.json(fakeSyncStatus)
  }),

  http.post('/api/sync/run', () => {
    return HttpResponse.json(fakeSyncStatus)
  }),

  http.get('/api/transactions/expenses', ({ request }) => {
    const url = new URL(request.url)
    const page = Number.parseInt(url.searchParams.get('page') ?? '1', 10) || 1
    const pageSize = Number.parseInt(url.searchParams.get('page_size') ?? '20', 10) || 20
    return HttpResponse.json({
      items: fakeExpenses.slice((page - 1) * pageSize, page * pageSize),
      page,
      page_size: pageSize,
      total: fakeExpenses.length,
    })
  }),
]
