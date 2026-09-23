import { http, HttpResponse } from 'msw'
import type { SyncStatus } from '@/features/sync/types/sync-status'
import type { CatalogueCategory } from '@/features/categories/types/category'
import type {
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

function generateFakeCategories(): CatalogueCategory[] {
  return [
    { key: 'Food', label: 'Alimentação', is_system: true, usage_count: 1, monthly_limit_cents: 80000 },
    { key: 'Shopping', label: 'Compras', is_system: true, usage_count: 40, monthly_limit_cents: 150000 },
    { key: 'lazer', label: 'Lazer', is_system: false, usage_count: 3, monthly_limit_cents: null },
    { key: 'pet-shop', label: 'Pet shop', is_system: false, usage_count: 0, monthly_limit_cents: null },
    { key: 'Groceries', label: 'Supermercado', is_system: true, usage_count: 0, monthly_limit_cents: null },
    { key: 'Transport', label: 'Transporte', is_system: true, usage_count: 1, monthly_limit_cents: null },
  ]
}

export const fakeCategories: CatalogueCategory[] = generateFakeCategories()

export function resetCategories(): void {
  fakeCategories.splice(0, fakeCategories.length, ...generateFakeCategories())
}

function slugify(label: string): string {
  return foldText(label).replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'categoria'
}

function labelError(label: string, exceptKey?: string): HttpResponse<{ detail: string }> | null {
  const trimmed = label.trim()
  if (trimmed === '') {
    return HttpResponse.json({ detail: 'Informe o nome da categoria.' }, { status: 422 })
  }
  if (
    fakeCategories.some(
      (category) => category.key !== exceptKey && foldText(category.label) === foldText(trimmed),
    )
  ) {
    return HttpResponse.json({ detail: 'Já existe uma categoria com esse nome.' }, { status: 422 })
  }
  return null
}

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

function isWholeMonth(from: string | null, to: string | null): boolean {
  if (from === null || to === null || !from.endsWith('-01')) {
    return false
  }
  const year = Number(from.slice(0, 4))
  const month = Number(from.slice(5, 7))
  const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate()
  return to === `${from.slice(0, 7)}-${String(lastDay).padStart(2, '0')}`
}

function signalFor(
  spentCents: number,
  limitCents: number | null,
): 'within' | 'warning' | 'over' | null {
  if (limitCents === null) {
    return null
  }
  if (spentCents > limitCents) {
    return 'over'
  }
  if (spentCents * 5 >= limitCents * 4) {
    return 'warning'
  }
  return 'within'
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
        limit_cents: null,
        signal: null,
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

function similarTo(item: Expense): Expense[] {
  return fakeExpenses.filter(
    (other) =>
      other.id !== item.id &&
      other.amount_cents < 0 &&
      (item.payee_name !== null
        ? other.payee_name === item.payee_name
        : item.description !== null &&
          other.description !== null &&
          foldText(other.description) === foldText(item.description)),
  )
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
    const from = url.searchParams.get('from')
    const to = url.searchParams.get('to')
    const scope = isWholeMonth(from, to) ? 'month' : 'none'
    const groups = groupByCategory(filterExpenses(url)).map((group) => {
      const limit_cents =
        fakeCategories.find((c) => c.label === group.label)?.monthly_limit_cents ?? null
      const signal = scope === 'month' ? signalFor(Math.abs(group.total_cents), limit_cents) : null
      return { ...group, limit_cents, signal }
    })
    return HttpResponse.json({
      groups,
      total_cents: groups.reduce((sum, group) => sum + group.total_cents, 0),
      over_limit_count: groups.filter((g) => g.signal === 'over').length,
      signal_scope: scope,
    })
  }),

  http.get('/api/categories', () => {
    return HttpResponse.json({
      categories: [...fakeCategories].sort((a, b) =>
        foldText(a.label).localeCompare(foldText(b.label)),
      ),
    })
  }),

  http.post('/api/categories', async ({ request }) => {
    const body = (await request.json()) as { label: string }
    const trimmed = body.label.trim()
    const error = labelError(body.label)
    if (error) {
      return error
    }
    let key = slugify(trimmed)
    let suffix = 2
    while (fakeCategories.some((category) => category.key === key)) {
      key = `${slugify(trimmed)}-${String(suffix)}`
      suffix += 1
    }
    const item: CatalogueCategory = {
      key,
      label: trimmed,
      is_system: false,
      usage_count: 0,
      monthly_limit_cents: null,
    }
    fakeCategories.push(item)
    return HttpResponse.json(item, { status: 201 })
  }),

  http.patch('/api/categories/:key', async ({ params, request }) => {
    const item = fakeCategories.find((category) => category.key === params.key)
    if (item === undefined) {
      return HttpResponse.json({ detail: 'Categoria não encontrada.' }, { status: 404 })
    }
    const body = (await request.json()) as { label: string }
    const trimmed = body.label.trim()
    const error = labelError(body.label, item.key)
    if (error) {
      return error
    }
    item.label = trimmed
    return HttpResponse.json(item)
  }),

  http.put('/api/categories/:key/limit', async ({ params, request }) => {
    const item = fakeCategories.find((category) => category.key === params.key)
    if (item === undefined) {
      return HttpResponse.json({ detail: 'Categoria não encontrada.' }, { status: 404 })
    }
    const body = (await request.json()) as { monthly_limit_cents: number | null }
    if (body.monthly_limit_cents !== null && body.monthly_limit_cents <= 0) {
      return HttpResponse.json(
        { detail: 'O limite precisa ser maior que zero.' },
        { status: 422 },
      )
    }
    item.monthly_limit_cents = body.monthly_limit_cents
    return HttpResponse.json(item)
  }),

  http.delete('/api/categories/:key', ({ params }) => {
    const item = fakeCategories.find((category) => category.key === params.key)
    if (item === undefined) {
      return HttpResponse.json({ detail: 'Categoria não encontrada.' }, { status: 404 })
    }
    if (item.is_system) {
      return HttpResponse.json(
        { detail: 'Categoria do sistema não pode ser apagada.' },
        { status: 403 },
      )
    }
    if (item.usage_count > 0) {
      return HttpResponse.json(
        {
          detail:
            'Esta categoria está em uso por ' +
            String(item.usage_count) +
            (item.usage_count === 1 ? ' gasto.' : ' gastos.'),
        },
        { status: 409 },
      )
    }
    fakeCategories.splice(fakeCategories.indexOf(item), 1)
    return new HttpResponse(null, { status: 204 })
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

  http.get('/api/transactions/:id/similar', ({ params }) => {
    const item = fakeExpenses.find((expense) => expense.id === Number(params.id))
    if (item === undefined) {
      return HttpResponse.json({ detail: 'Gasto não encontrado.' }, { status: 404 })
    }
    return HttpResponse.json({ count: similarTo(item).length })
  }),

  http.post('/api/transactions/:id/category/apply-to-similar', async ({ params, request }) => {
    const item = fakeExpenses.find((expense) => expense.id === Number(params.id))
    if (item === undefined) {
      return HttpResponse.json({ detail: 'Gasto não encontrado.' }, { status: 404 })
    }
    const body = (await request.json()) as { category: string | null }
    const found = fakeCategories.find((category) => category.key === body.category)
    if (body.category !== null && found === undefined) {
      return HttpResponse.json({ detail: 'Categoria desconhecida.' }, { status: 422 })
    }
    let updated = 0
    for (const other of similarTo(item)) {
      if (!autoCategories.has(other.id)) {
        autoCategories.set(other.id, { category: other.category, category_key: other.category_key })
      }
      other.category = found?.label ?? null
      other.category_key = body.category
      other.category_source = 'manual'
      updated += 1
    }
    return HttpResponse.json({ updated })
  }),
]
