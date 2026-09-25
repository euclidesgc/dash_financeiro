import { useId, useState } from 'react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { useCategoryTotals } from '@/features/expenses/api/get-category-totals'
import type { CategoryTotalsQuery } from '@/features/expenses/types/expense'
import { formatMoney } from '@/utils/format-money'

const VISIBLE_GROUPS = 8

export function CategoryTotals({ query }: { query: CategoryTotalsQuery }): React.JSX.Element | null {
  const { data, isPending, isError, refetch } = useCategoryTotals(query)
  const [expanded, setExpanded] = useState(false)
  const headingId = useId()

  if (isPending) {
    return (
      <p role="status" className="mt-6 text-gray-600">
        Carregando totais por categoria…
      </p>
    )
  }

  if (isError) {
    return (
      <Alert
        message="Não foi possível carregar os totais por categoria."
        action={{ label: 'Tentar de novo', onClick: () => void refetch() }}
      />
    )
  }

  if (data.groups.length === 0) {
    return null
  }

  const groups = data.groups
  const visible = expanded ? groups : groups.slice(0, VISIBLE_GROUPS)

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId} className="mt-6 text-lg font-semibold">
        Por categoria
      </h2>
      <table aria-labelledby={headingId} className="mt-3 w-full text-sm">
        <thead className="sr-only">
          <tr>
            <th scope="col">Categoria</th>
            <th scope="col">Gastos</th>
            <th scope="col">Total</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {visible.map((group) => (
            <tr key={group.category ?? ''}>
              <td className="min-w-0 truncate py-2 text-gray-900">{group.label}</td>
              <td className="whitespace-nowrap py-2 pl-4 text-right text-gray-600 tabular-nums">
                {group.count === 1 ? '1 gasto' : `${String(group.count)} gastos`}
              </td>
              <td className="whitespace-nowrap py-2 pl-4 text-right tabular-nums font-medium text-gray-900">
                {formatMoney(Math.abs(group.total_cents))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {groups.length > VISIBLE_GROUPS ? (
        <div className="mt-3">
          <Button
            variant="secondary"
            aria-expanded={expanded}
            onClick={() => {
              setExpanded((value) => !value)
            }}
          >
            {expanded ? 'Mostrar menos' : `Mostrar todas (${String(groups.length)})`}
          </Button>
        </div>
      ) : null}
    </section>
  )
}
