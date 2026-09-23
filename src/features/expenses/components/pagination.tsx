import { Button } from '@/components/ui/button'

export function Pagination({
  page,
  pages,
  total,
  isFetching,
  onChange,
}: {
  page: number
  pages: number
  total: number
  isFetching: boolean
  onChange: (page: number) => void
}): React.JSX.Element {
  const unit = total === 1 ? ' gasto' : ' gastos'

  return (
    <nav aria-label="Paginação" className="mt-6 flex flex-wrap items-center justify-between gap-4">
      <p className="text-sm text-gray-600">
        Página {page} de {pages} · {total}
        {unit}
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
