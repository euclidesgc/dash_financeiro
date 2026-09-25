import { Button } from '@/components/ui/button'
import { useApplyCategoryToSimilar } from '@/features/expenses/api/apply-category-to-similar'
import { useSimilarCount } from '@/features/expenses/api/get-similar-count'
import { EXPENSE_NOUN, formatCount, type CountNoun } from '@/utils/format-count'

const OFFER_CLASSES =
  'mt-1 flex flex-wrap items-center justify-end gap-2 rounded-md border border-blue-200 bg-blue-50 p-2'

const SIMILAR_NOUN: CountNoun = { one: 'gasto parecido', many: 'gastos parecidos' }

function offerText(n: number): string {
  return `Aplicar a ${formatCount(n, SIMILAR_NOUN)}`
}

function appliedText(n: number): string {
  return `Categoria aplicada a ${formatCount(n, EXPENSE_NOUN)}`
}

export function SimilarOffer({
  expenseId,
  category,
  onDismiss,
}: {
  expenseId: number
  category: string | null
  onDismiss: () => void
}): React.JSX.Element | null {
  const count = useSimilarCount(expenseId)
  const mutation = useApplyCategoryToSimilar()

  if (mutation.isSuccess) {
    return (
      <p role="status" className="mt-1 text-sm text-green-800">
        {appliedText(mutation.data.updated)}
      </p>
    )
  }

  if (mutation.isError) {
    return (
      <div className={OFFER_CLASSES}>
        <p role="alert" className="mt-1 text-sm text-red-700">
          Não foi possível aplicar a categoria aos gastos parecidos.
        </p>
        <Button
          variant="secondary"
          type="button"
          onClick={() => {
            mutation.mutate(mutation.variables)
          }}
        >
          Tentar de novo
        </Button>
        <Button variant="secondary" type="button" onClick={onDismiss}>
          Agora não
        </Button>
      </div>
    )
  }

  if (count.isError) {
    return (
      <div className={OFFER_CLASSES}>
        <p role="alert" className="mt-1 text-sm text-red-700">
          Não foi possível contar os gastos parecidos.
        </p>
        <Button
          variant="secondary"
          type="button"
          onClick={() => {
            void count.refetch()
          }}
        >
          Tentar de novo
        </Button>
        <Button variant="secondary" type="button" onClick={onDismiss}>
          Agora não
        </Button>
      </div>
    )
  }

  if (count.isPending || count.data.count === 0) return null

  return (
    <div className={OFFER_CLASSES}>
      <p className="text-right text-sm text-blue-800">{offerText(count.data.count)}</p>
      <Button
        variant="primary"
        type="button"
        disabled={mutation.isPending}
        onClick={() => {
          if (mutation.isPending) return
          mutation.mutate({ id: expenseId, category })
        }}
      >
        {mutation.isPending ? 'Aplicando…' : 'Aplicar'}
      </Button>
      {mutation.isPending ? (
        <span role="status" className="sr-only">
          Aplicando…
        </span>
      ) : null}
      <Button variant="secondary" type="button" disabled={mutation.isPending} onClick={onDismiss}>
        Agora não
      </Button>
    </div>
  )
}
