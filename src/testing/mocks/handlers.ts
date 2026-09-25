import { http, HttpResponse } from 'msw'
import type { SyncStatus } from '@/features/sync/types/sync-status'
import type {
  Category,
  CategoryGroup,
  CategoryUpdateBody,
  Expense,
  ExpenseOrder,
  ExpenseSort,
} from '@/features/expenses/types/expense'

export const fakeUser = { login: 'teste' }

export function foldText(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
}

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

export const fakeCategories: Category[] = [
  { key: 'Food', label: 'Alimentação' },
  { key: 'Shopping', label: 'Compras' },
  { key: 'Groceries', label: 'Supermercado' },
  { key: 'Transport', label: 'Transporte' },
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
        account_id: 'acc-bank-1',
        category: 'Compras',
        category_key: 'Shopping',
        category_source: 'auto',
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
        account_id: 'acc-bank-1',
        category: 'Alimentação',
        category_key: 'Food',
        category_source: 'auto',
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
        account_id: 'acc-bank-1',
        category: null,
        category_key: null,
        category_source: 'auto',
        amount_cents: -1000 * id,
      }
    }
    if (index === 3) {
      return {
        id,
        date,
        description: `GASTO ${String(id)}`,
        payee_name: 'Açougue São Jorge',
        account_name: 'Conta corrente',
        account_institution: 'Banco de teste',
        account_type: 'BANK',
        account_id: 'acc-bank-1',
        category: 'Transporte',
        category_key: 'Transport',
        category_source: 'auto',
        amount_cents: -1000 * id,
      }
    }
    if (index === 4) {
      return {
        id,
        date,
        description: `GASTO ${String(id)}`,
        payee_name: null,
        account_name: 'Conta corrente',
        account_institution: 'Banco de teste',
        account_type: 'BANK',
        account_id: 'acc-bank-1',
        category: 'Compras',
        category_key: 'Shopping',
        category_source: 'auto',
        amount_cents: -120000,
      }
    }
    if (id % 3 === 0) {
      return {
        id,
        date,
        description: `GASTO ${String(id)}`,
        payee_name: null,
        account_name: 'Cartão',
        account_institution: 'Emissor de teste',
        account_type: 'CREDIT',
        account_id: 'acc-credit-1',
        category: 'Compras',
        category_key: 'Shopping',
        category_source: 'auto',
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
      account_id: 'acc-bank-1',
      category: 'Compras',
      category_key: 'Shopping',
      category_source: 'auto',
      amount_cents: -1000 * id,
    }
  })
}

export const fakeExpenses: Expense[] = generateFakeExpenses()

const autoCategories = new Map<number, { category: string | null; category_key: string | null }>()

export function resetExpenses(): void {
  fakeExpenses.splice(0, fakeExpenses.length, ...generateFakeExpenses())
  autoCategories.clear()
}

function sortExpenses(items: Expense[], sort: ExpenseSort, order: ExpenseOrder): Expense[] {
  const direction = order === 'desc' ? -1 : 1
  return [...items].sort((a, b) => {
    let comparison = 0
    if (sort === 'date') {
      comparison = a.date < b.date ? -1 : a.date > b.date ? 1 : 0
      comparison *= direction
    } else if (sort === 'amount') {
      comparison = (Math.abs(a.amount_cents) - Math.abs(b.amount_cents)) * direction
    } else {
      if (a.category === null && b.category === null) {
        comparison = 0
      } else if (a.category === null) {
        comparison = 1
      } else if (b.category === null) {
        comparison = -1
      } else {
        comparison = a.category.localeCompare(b.category, 'pt-BR') * direction
      }
    }
    return comparison !== 0 ? comparison : b.id - a.id
  })
}

export function filterExpenses(url: URL): Expense[] {
  const from = url.searchParams.get('from')
  const to = url.searchParams.get('to')
  const accountId = url.searchParams.get('account_id')
  const rawTerm = url.searchParams.get('q')?.trim() ?? ''
  const term = rawTerm.length >= 2 ? foldText(rawTerm) : null
  return fakeExpenses.filter(
    (item) =>
      (from === null || item.date >= from) &&
      (to === null || item.date <= to) &&
      (accountId === null || item.account_id === accountId) &&
      (term === null ||
        foldText(item.description ?? '').includes(term) ||
        foldText(item.payee_name ?? '').includes(term)),
  )
}

export function groupByCategory(items: Expense[]): CategoryGroup[] {
  const byCategory = new Map<string | null, CategoryGroup>()
  for (const item of items) {
    const category = item.category ?? null
    const existing = byCategory.get(category)
    if (existing) {
      existing.count += 1
      existing.total_cents += item.amount_cents
    } else {
      byCategory.set(category, {
        category,
        label: category ?? 'Sem categoria',
        count: 1,
        total_cents: item.amount_cents,
      })
    }
  }
  return [...byCategory.values()].sort((a, b) => {
    const diff = Math.abs(b.total_cents) - Math.abs(a.total_cents)
    if (diff !== 0) {
      return diff
    }
    if (a.category === null && b.category === null) {
      return 0
    }
    if (a.category === null) {
      return 1
    }
    if (b.category === null) {
      return -1
    }
    return a.category < b.category ? -1 : a.category > b.category ? 1 : 0
  })
}

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
    const sort = (url.searchParams.get('sort') ?? 'date') as ExpenseSort
    const order = (url.searchParams.get('order') ?? 'desc') as ExpenseOrder
    const filtered = filterExpenses(url)
    const items = sortExpenses(filtered, sort, order)
    return HttpResponse.json({
      items: items.slice((page - 1) * pageSize, page * pageSize),
      page,
      page_size: pageSize,
      total: filtered.length,
      total_cents: filtered.reduce((sum, item) => sum + item.amount_cents, 0),
    })
  }),

  http.get('/api/transactions/expenses/by-category', ({ request }) => {
    const url = new URL(request.url)
    const groups = groupByCategory(filterExpenses(url))
    return HttpResponse.json({
      groups,
      total_cents: groups.reduce((sum, group) => sum + group.total_cents, 0),
    })
  }),

  http.get('/api/categories', () => {
    return HttpResponse.json({ categories: fakeCategories })
  }),

  http.patch('/api/transactions/:id/category', async ({ params, request }) => {
    const id = Number(params.id)
    const item = fakeExpenses.find((expense) => expense.id === id)
    if (item === undefined) {
      return HttpResponse.json({ detail: 'Gasto não encontrado.' }, { status: 404 })
    }
    const body = (await request.json()) as CategoryUpdateBody
    if (body.mode === 'manual') {
      const found = fakeCategories.find((category) => category.key === body.category)
      if (body.category !== null && found === undefined) {
        return HttpResponse.json({ detail: 'Categoria desconhecida.' }, { status: 422 })
      }
      if (!autoCategories.has(id)) {
        autoCategories.set(id, { category: item.category, category_key: item.category_key })
      }
      item.category = found?.label ?? null
      item.category_key = body.category
      item.category_source = 'manual'
    } else {
      const auto = autoCategories.get(id)
      if (auto !== undefined) {
        item.category = auto.category
        item.category_key = auto.category_key
      }
      item.category_source = 'auto'
    }
    return HttpResponse.json(item)
  }),
]
