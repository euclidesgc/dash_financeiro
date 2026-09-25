import { Button } from '@/components/ui/button'
import { EXPENSE_NOUN, formatCount, type CountNoun } from '@/utils/format-count'
import { formatMoney } from '@/utils/format-money'

export function Pagination({
  page,
  pages,
  total,
  outflowCents,
  inflowCents,
  splitFlows = false,
  isFetching,
  onChange,
  noun = EXPENSE_NOUN,
}: {
  page: number
  pages: number
  total: number
  outflowCents: number
  inflowCents: number
  splitFlows?: boolean
  isFetching: boolean
  onChange: (page: number) => void
  noun?: CountNoun
}): React.JSX.Element {
  return (
    <nav aria-label="Paginação" className="mt-6 flex flex-wrap items-center justify-between gap-4">
      <p className="text-sm text-gray-600">
        Página {page} de {pages} · {formatCount(total, noun)} ·{' '}
        {splitFlows
          ? `${formatMoney(Math.abs(outflowCents))} em saídas e ${formatMoney(inflowCents)} em entradas`
          : formatMoney(Math.abs(outflowCents) + inflowCents)}{' '}
        no período
      </p>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          type="button"
          disabled={page <= 1 || isFetching}
          onClick={() => {
            onChange(page - 1)
          }}
        >
          Anterior
        </Button>
        <Button
          variant="secondary"
          type="button"
          disabled={page >= pages || isFetching}
          onClick={() => {
            onChange(page + 1)
          }}
        >
          Próxima
        </Button>
      </div>
    </nav>
  )
}
