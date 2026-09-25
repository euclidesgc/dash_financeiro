import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { useClearNotExpense } from '@/features/expenses/api/clear-not-expense'
import { useExpenseAccounts } from '@/features/expenses/api/get-accounts'
import { useCategories } from '@/hooks/use-categories'
import { useExpenses } from '@/features/expenses/api/get-expenses'
import { AccountSelect } from '@/features/expenses/components/account-select'
import { CategoryTotals } from '@/features/expenses/components/category-totals'
import { ExpenseItem } from '@/features/expenses/components/expense-item'
import { MonthCeiling } from '@/features/expenses/components/month-ceiling'
import { Pagination } from '@/features/expenses/components/pagination'
import { PeriodControls } from '@/features/expenses/components/period-controls'
import { PeriodResult } from '@/features/expenses/components/period-result'
import { SearchInput } from '@/features/expenses/components/search-input'
import { SortControls } from '@/features/expenses/components/sort-controls'
import { ViewSelect } from '@/features/expenses/components/view-select'
import type {
  CategoryTotalsQuery,
  ExpenseOrder,
  ExpenseSort,
  ExpenseView,
  Period,
} from '@/features/expenses/types/expense'
import { currentMonth, readPeriod, shiftMonth, toDateBounds, writePeriod } from '@/features/expenses/utils/period'
import { EXPENSE_NOUN, type CountNoun } from '@/utils/format-count'

const SORTS = ['date', 'amount', 'category'] as const
const ORDERS = ['asc', 'desc'] as const
const DEFAULT_SORT: ExpenseSort = 'date'
const DEFAULT_ORDER: ExpenseOrder = 'desc'
const DEFAULT_ORDER_BY_SORT: Record<ExpenseSort, ExpenseOrder> = {
  date: 'desc',
  amount: 'desc',
  category: 'asc',
}

function readPage(value: string | null): number {
  const page = Number.parseInt(value ?? '', 10)
  return Number.isNaN(page) || page < 1 ? 1 : page
}

function readSort(value: string | null): ExpenseSort {
  return (SORTS as readonly string[]).includes(value ?? '') ? (value as ExpenseSort) : 'date'
}

function readOrder(value: string | null): ExpenseOrder {
  return (ORDERS as readonly string[]).includes(value ?? '') ? (value as ExpenseOrder) : 'desc'
}

function readAccount(value: string | null): string | null {
  return value === null || value === '' ? null : value
}

function readSearch(value: string | null): string | null {
  const term = (value ?? '').trim()
  return term.length >= 2 ? term : null
}

const VIEW_TEXT: Record<
  ExpenseView,
  {
    loading: string
    error: string
    emptyFiltered: string
    emptyAll: string
    noun: CountNoun
    excludedNotice: (name: string) => string
  }
> = {
  expenses: {
    loading: 'Carregando gastos…',
    error: 'Não foi possível carregar os gastos.',
    emptyFiltered: 'Nenhum gasto para esse filtro.',
    emptyAll: 'Nenhum gasto registrado ainda.',
    noun: EXPENSE_NOUN,
    excludedNotice: (name) => `${name} não conta mais como gasto.`,
  },
  excluded: {
    loading: 'Carregando gastos…',
    error: 'Não foi possível carregar os gastos.',
    emptyFiltered: 'Nenhum lançamento marcado como não-gasto.',
    emptyAll: 'Nenhum lançamento marcado como não-gasto.',
    noun: { one: 'lançamento', many: 'lançamentos' },
    excludedNotice: (name) => `${name} não conta mais como gasto.`,
  },
  income: {
    loading: 'Carregando entradas…',
    error: 'Não foi possível carregar as entradas.',
    emptyFiltered: 'Nenhuma entrada nesse período.',
    emptyAll: 'Nenhuma entrada registrada ainda.',
    noun: { one: 'entrada', many: 'entradas' },
    excludedNotice: (name) => `${name} não conta mais como entrada.`,
  },
}

function readView(value: string | null): ExpenseView {
  if (value === 'income') return 'income'
  if (value === 'excluded') return 'excluded'
  return 'expenses'
}

function writeView(params: URLSearchParams, view: ExpenseView): void {
  params.delete('page')
  if (view === 'expenses') {
    params.delete('view')
  } else {
    params.set('view', view)
  }
}

function writeSearch(params: URLSearchParams, text: string): boolean {
  const next = readSearch(text)
  const current = readSearch(params.get('q'))
  if (next === current) {
    return false
  }
  params.delete('page')
  if (next === null) {
    params.delete('q')
  } else {
    params.set('q', next)
  }
  return true
}

function writeAccount(params: URLSearchParams, id: string | null): void {
  params.delete('page')
  if (id === null) {
    params.delete('account')
  } else {
    params.set('account', id)
  }
}

function writeSorting(params: URLSearchParams, sort: ExpenseSort, order: ExpenseOrder): void {
  params.delete('page')
  if (sort === DEFAULT_SORT) {
    params.delete('sort')
  } else {
    params.set('sort', sort)
  }
  if (order === DEFAULT_ORDER) {
    params.delete('order')
  } else {
    params.set('order', order)
  }
}

export function ExpensesList(): React.JSX.Element {
  const [searchParams, setSearchParams] = useSearchParams()
  const page = readPage(searchParams.get('page'))
  const sort = readSort(searchParams.get('sort'))
  const order = readOrder(searchParams.get('order'))
  const period = readPeriod(searchParams)
  const { from, to } = toDateBounds(period)
  const account = readAccount(searchParams.get('account'))
  const search = readSearch(searchParams.get('q'))
  const view = readView(searchParams.get('view'))
  const text = VIEW_TEXT[view]
  const accounts = useExpenseAccounts()
  const categories = useCategories()
  const accountKnown = accounts.data
    ? accounts.data.accounts.some((item) => item.id === account)
    : true
  const filters: CategoryTotalsQuery = {
    from,
    to,
    account: accountKnown ? account : null,
    search,
    view,
  }
  const { data, isPending, isError, isPlaceholderData, refetch } = useExpenses({
    page,
    sort,
    order,
    ...filters,
  })
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1
  const [lastExcluded, setLastExcluded] = useState<{
    id: number
    description: string | null
  } | null>(null)
  const undo = useClearNotExpense()

  useEffect(() => {
    setLastExcluded(null)
  }, [view])

  useEffect(() => {
    if (data && data.total > 0 && page > pages) {
      const params = new URLSearchParams(searchParams)
      params.set('page', String(pages))
      setSearchParams(params, { replace: true })
    }
  }, [data, page, pages, searchParams, setSearchParams])

  useEffect(() => {
    if (account !== null && accounts.data && !accountKnown) {
      const params = new URLSearchParams(searchParams)
      params.delete('account')
      setSearchParams(params, { replace: true })
    }
  }, [account, accountKnown, accounts.data, searchParams, setSearchParams])

  // Reason: the data router writes the URL first and renders it later inside a
  // transition; every handler builds on the rendered searchParams, so without a
  // synchronous render a second edit in that gap rewrites the URL from stale
  // params and drops the first edit.
  function commitParams(params: URLSearchParams, { replace = true } = {}): void {
    setSearchParams(params, { replace, flushSync: true })
  }

  function commitPeriod(next: Period): void {
    const params = new URLSearchParams(searchParams)
    writePeriod(params, next)
    commitParams(params)
  }

  function handleMonthChange(delta: -1 | 1): void {
    const base = period.kind === 'month' ? period.month : currentMonth()
    commitPeriod({ kind: 'month', month: shiftMonth(base, delta) })
  }

  function handleRangeChange(field: 'from' | 'to', value: string): void {
    const bounds = toDateBounds(period)
    const nextValue = value || null
    let nextFrom = field === 'from' ? nextValue : bounds.from
    let nextTo = field === 'to' ? nextValue : bounds.to
    if (nextFrom !== null && nextTo !== null && nextTo < nextFrom) {
      if (field === 'from') {
        nextTo = null
      } else {
        nextFrom = null
      }
    }
    commitPeriod(
      nextFrom !== null || nextTo !== null
        ? { kind: 'range', from: nextFrom, to: nextTo }
        : { kind: 'all' },
    )
  }

  function handleClear(): void {
    commitPeriod({ kind: 'all' })
  }

  function handleSortChange(next: ExpenseSort): void {
    const params = new URLSearchParams(searchParams)
    writeSorting(params, next, DEFAULT_ORDER_BY_SORT[next])
    commitParams(params)
  }

  function handleOrderToggle(): void {
    const params = new URLSearchParams(searchParams)
    writeSorting(params, sort, order === 'asc' ? 'desc' : 'asc')
    commitParams(params)
  }

  function handleAccountChange(next: string | null): void {
    const params = new URLSearchParams(searchParams)
    writeAccount(params, next)
    commitParams(params)
  }

  function handleViewChange(next: ExpenseView): void {
    const params = new URLSearchParams(searchParams)
    writeView(params, next)
    commitParams(params)
  }

  function handleSearchCommit(text: string): void {
    const params = new URLSearchParams(searchParams)
    if (writeSearch(params, text)) {
      commitParams(params)
    }
  }

  const header = (
    <>
      <div className="mt-6 flex flex-wrap items-end gap-3">
        <SearchInput value={search} onCommit={handleSearchCommit} />
        <AccountSelect
          value={account}
          accounts={accounts.data?.accounts ?? []}
          isPending={accounts.isPending}
          isError={accounts.isError}
          onChange={handleAccountChange}
          onRetry={() => void accounts.refetch()}
        />
        <PeriodControls
          period={period}
          onMonthChange={handleMonthChange}
          onRangeChange={handleRangeChange}
          onClear={handleClear}
        />
        <SortControls
          sort={sort}
          order={order}
          onSortChange={handleSortChange}
          onOrderToggle={handleOrderToggle}
        />
        <ViewSelect value={view} onChange={handleViewChange} />
      </div>
      {period.kind !== 'all' ? (
        <PeriodResult query={{ from, to, account: filters.account, search }} />
      ) : null}
      {period.kind === 'month' && view === 'expenses' ? <MonthCeiling query={{ from, to }} /> : null}
      {view === 'expenses' ? <CategoryTotals query={filters} /> : null}
    </>
  )

  function handleUndo(id: number): void {
    if (undo.isPending) return
    undo.mutate(id, {
      onSuccess: () => {
        setLastExcluded(null)
      },
    })
  }

  const notice =
    lastExcluded === null ? null : undo.isError ? (
      <div
        role="alert"
        className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-md border border-red-200 bg-red-50 p-3"
      >
        <p className="text-sm text-red-800">Não foi possível desfazer.</p>
        <Button
          variant="secondary"
          type="button"
          disabled={undo.isPending}
          onClick={() => {
            handleUndo(lastExcluded.id)
          }}
        >
          Tentar de novo
        </Button>
      </div>
    ) : (
      <div
        role="status"
        className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-md border border-green-200 bg-green-50 p-3"
      >
        <p className="text-sm text-green-800">
          {text.excludedNotice(lastExcluded.description ?? 'Sem descrição')}
        </p>
        <Button
          variant="secondary"
          type="button"
          disabled={undo.isPending}
          onClick={() => {
            handleUndo(lastExcluded.id)
          }}
        >
          {undo.isPending ? 'Desfazendo…' : 'Desfazer'}
        </Button>
      </div>
    )

  if (isPending) {
    return (
      <>
        {header}
        <p role="status" className="mt-6 text-gray-600">
          {text.loading}
        </p>
      </>
    )
  }

  if (isError) {
    return (
      <>
        {header}
        <Alert
          message={text.error}
          action={{ label: 'Tentar de novo', onClick: () => void refetch() }}
        />
      </>
    )
  }

  if (data.total === 0) {
    const filtered = period.kind !== 'all' || account !== null || search !== null
    return (
      <>
        {header}
        {notice}
        <p className="mt-6 rounded-md border border-dashed border-gray-300 p-6 text-center text-gray-600">
          {filtered ? text.emptyFiltered : text.emptyAll}
        </p>
      </>
    )
  }

  return (
    <>
      {header}
      {notice}
      <ul className="mt-6 divide-y divide-gray-200">
        {data.items.map((expense) => (
          <ExpenseItem
            key={expense.id}
            expense={expense}
            categories={categories.data?.categories ?? []}
            categoriesReady={categories.isSuccess}
            view={view}
            onExcluded={(excluded) => {
              undo.reset()
              setLastExcluded(excluded)
            }}
          />
        ))}
      </ul>
      <Pagination
        page={page}
        pages={pages}
        total={data.total}
        totalCents={data.total_cents}
        isFetching={isPlaceholderData}
        noun={text.noun}
        onChange={(next) => {
          const params = new URLSearchParams(searchParams)
          params.set('page', String(next))
          commitParams(params, { replace: false })
        }}
      />
    </>
  )
}
