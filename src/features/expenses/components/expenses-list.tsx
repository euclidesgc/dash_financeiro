import { useEffect } from 'react'
import { useSearchParams } from 'react-router'
import { Alert } from '@/components/ui/alert'
import { useExpenses } from '@/features/expenses/api/get-expenses'
import { ExpenseItem } from '@/features/expenses/components/expense-item'
import { Pagination } from '@/features/expenses/components/pagination'

function readPage(value: string | null): number {
  const page = Number.parseInt(value ?? '', 10)
  return Number.isNaN(page) || page < 1 ? 1 : page
}

export function ExpensesList(): React.JSX.Element {
  const [searchParams, setSearchParams] = useSearchParams()
  const page = readPage(searchParams.get('page'))
  const { data, isPending, isError, isPlaceholderData, refetch } = useExpenses(page)
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  useEffect(() => {
    if (data && data.total > 0 && page > pages) {
      setSearchParams({ page: String(pages) }, { replace: true })
    }
  }, [data, page, pages, setSearchParams])

  if (isPending) {
    return (
      <p role="status" className="mt-6 text-gray-600">
        Carregando gastos…
      </p>
    )
  }

  if (isError) {
    return (
      <Alert
        message="Não foi possível carregar os gastos."
        action={{ label: 'Tentar de novo', onClick: () => void refetch() }}
      />
    )
  }

  if (data.total === 0) {
    return (
      <p className="mt-6 rounded-md border border-dashed border-gray-300 p-6 text-center text-gray-600">
        Nenhum gasto registrado ainda.
      </p>
    )
  }

  return (
    <>
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
          setSearchParams({ page: String(next) })
        }}
      />
    </>
  )
}
