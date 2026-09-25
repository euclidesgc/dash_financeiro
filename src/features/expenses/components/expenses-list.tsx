import { useEffect } from 'react'
import { useSearchParams } from 'react-router'
import { Alert } from '@/components/ui/alert'
import { useExpenseAccounts } from '@/features/expenses/api/get-accounts'
import { useCategories } from '@/features/expenses/api/get-categories'
import { useExpenses } from '@/features/expenses/api/get-expenses'
import { AccountSelect } from '@/features/expenses/components/account-select'
import { CategoryTotals } from '@/features/expenses/components/category-totals'
import { ExpenseItem } from '@/features/expenses/components/expense-item'
import { Pagination } from '@/features/expenses/components/pagination'
import { PeriodControls } from '@/features/expenses/components/period-controls'
import { SearchInput } from '@/features/expenses/components/search-input'
import { SortControls } from '@/features/expenses/components/sort-controls'
import type {
  CategoryTotalsQuery,
  ExpenseOrder,
  ExpenseSort,
  Period,
} from '@/features/expenses/types/expense'
import { currentMonth, readPeriod, shiftMonth, toDateBounds, writePeriod } from '@/features/expenses/utils/period'

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
  const accounts = useExpenseAccounts()
  const categories = useCategories()
  const accountKnown = accounts.data
    ? accounts.data.accounts.some((item) => item.id === account)
    : true
  const filters: CategoryTotalsQuery = { from, to, account: accountKnown ? account : null, search }
  const { data, isPending, isError, isPlaceholderData, refetch } = useExpenses({
    page,
    sort,
    order,
    ...filters,
  })
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

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

  function commitPeriod(next: Period): void {
    const params = new URLSearchParams(searchParams)
    writePeriod(params, next)
    setSearchParams(params, { replace: true })
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
    setSearchParams(params, { replace: true })
  }

  function handleOrderToggle(): void {
    const params = new URLSearchParams(searchParams)
    writeSorting(params, sort, order === 'asc' ? 'desc' : 'asc')
    setSearchParams(params, { replace: true })
  }

  function handleAccountChange(next: string | null): void {
    const params = new URLSearchParams(searchParams)
    writeAccount(params, next)
    setSearchParams(params, { replace: true })
  }

  function handleSearchCommit(text: string): void {
    const params = new URLSearchParams(searchParams)
    if (writeSearch(params, text)) {
      setSearchParams(params, { replace: true })
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
      </div>
      <CategoryTotals query={filters} />
    </>
  )

  if (isPending) {
    return (
      <>
        {header}
        <p role="status" className="mt-6 text-gray-600">
          Carregando gastos…
        </p>
      </>
    )
  }

  if (isError) {
    return (
      <>
        {header}
        <Alert
          message="Não foi possível carregar os gastos."
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
        <p className="mt-6 rounded-md border border-dashed border-gray-300 p-6 text-center text-gray-600">
          {filtered ? 'Nenhum gasto para esse filtro.' : 'Nenhum gasto registrado ainda.'}
        </p>
      </>
    )
  }

  return (
    <>
      {header}
      <ul className="mt-6 divide-y divide-gray-200">
        {data.items.map((expense) => (
          <ExpenseItem
            key={expense.id}
            expense={expense}
            categories={categories.data?.categories ?? []}
            categoriesReady={categories.isSuccess}
          />
        ))}
      </ul>
      <Pagination
        page={page}
        pages={pages}
        total={data.total}
        totalCents={data.total_cents}
        isFetching={isPlaceholderData}
        onChange={(next) => {
          const params = new URLSearchParams(searchParams)
          params.set('page', String(next))
          setSearchParams(params)
        }}
      />
    </>
  )
}
