import { http, HttpResponse } from 'msw'

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
]
