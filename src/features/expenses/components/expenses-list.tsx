import { useEffect } from 'react'
import { useSearchParams } from 'react-router'
import { Alert } from '@/components/ui/alert'
import { useExpenses } from '@/features/expenses/api/get-expenses'
import { ExpenseItem } from '@/features/expenses/components/expense-item'
import { Pagination } from '@/features/expenses/components/pagination'
import { SortControls } from '@/features/expenses/components/sort-controls'
import type { ExpenseOrder, ExpenseSort } from '@/features/expenses/types/expense'

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
  const { data, isPending, isError, isPlaceholderData, refetch } = useExpenses({
    page,
    sort,
    order,
  })
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  useEffect(() => {
    if (data && data.total > 0 && page > pages) {
      const params = new URLSearchParams(searchParams)
      params.set('page', String(pages))
      setSearchParams(params, { replace: true })
    }
  }, [data, page, pages, searchParams, setSearchParams])

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

  const sortControls = (
    <SortControls
      sort={sort}
      order={order}
      onSortChange={handleSortChange}
      onOrderToggle={handleOrderToggle}
    />
  )

  if (isPending) {
    return (
      <>
        {sortControls}
        <p role="status" className="mt-6 text-gray-600">
          Carregando gastos…
        </p>
      </>
    )
  }

  if (isError) {
    return (
      <>
        {sortControls}
        <Alert
          message="Não foi possível carregar os gastos."
          action={{ label: 'Tentar de novo', onClick: () => void refetch() }}
        />
      </>
    )
  }

  if (data.total === 0) {
    return (
      <>
        {sortControls}
        <p className="mt-6 rounded-md border border-dashed border-gray-300 p-6 text-center text-gray-600">
          Nenhum gasto registrado ainda.
        </p>
      </>
    )
  }

  return (
    <>
      {sortControls}
      <ul className="mt-6 divide-y divide-gray-200">
        {data.items.map((expense) => (
          <ExpenseItem key={expense.id} expense={expense} />
        ))}
      </ul>
      <Pagination
        page={page}
        pages={pages}
        total={data.total}
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
