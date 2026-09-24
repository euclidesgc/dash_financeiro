import { Button } from '@/components/ui/button'
import { formatMoney } from '@/utils/format-money'

export function Pagination({
  page,
  pages,
  total,
  totalCents,
  isFetching,
  onChange,
  noun = { one: 'gasto', many: 'gastos' },
}: {
  page: number
  pages: number
  total: number
  totalCents: number
  isFetching: boolean
  onChange: (page: number) => void
  noun?: { one: string; many: string }
}): React.JSX.Element {
  const unit = total === 1 ? ` ${noun.one}` : ` ${noun.many}`

  return (
    <nav aria-label="Paginação" className="mt-6 flex flex-wrap items-center justify-between gap-4">
      <p className="text-sm text-gray-600">
        Página {page} de {pages} · {total}
        {unit} · {formatMoney(Math.abs(totalCents))} no período
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
