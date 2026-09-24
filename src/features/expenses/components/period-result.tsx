import { useId } from 'react'
import { Alert } from '@/components/ui/alert'
import { usePeriodResult } from '@/features/expenses/api/get-period-result'
import type { PeriodResultQuery } from '@/features/expenses/types/expense'
import { formatMoney } from '@/utils/format-money'

function balanceColor(balanceCents: number): string {
  if (balanceCents > 0) return 'text-green-700'
  if (balanceCents < 0) return 'text-red-700'
  return 'text-gray-900'
}

export function PeriodResult({ query }: { query: PeriodResultQuery }): React.JSX.Element {
  const result = usePeriodResult(query)
  const headingId = useId()

  if (result.isPending) {
    return (
      <p role="status" className="mt-6 text-gray-600">
        Carregando resultado do período…
      </p>
    )
  }

  if (result.isError) {
    return (
      <Alert
        message="Não foi possível carregar o resultado do período."
        action={{ label: 'Tentar de novo', onClick: () => void result.refetch() }}
      />
    )
  }

  const { income_cents, spending_cents, balance_cents } = result.data

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId} className="mt-6 text-lg font-semibold">
        Resultado do período
      </h2>
      <dl className="mt-2 flex flex-wrap gap-x-8 gap-y-2 rounded-md border border-gray-200 p-4">
        <div className="min-w-0">
          <dt className="text-sm text-gray-600">Entradas</dt>
          <dd className="tabular-nums font-medium text-green-700">{formatMoney(income_cents)}</dd>
        </div>
        <div className="min-w-0">
          <dt className="text-sm text-gray-600">Gastos</dt>
          <dd className="tabular-nums font-medium text-red-700">
            {formatMoney(Math.abs(spending_cents))}
          </dd>
        </div>
        <div className="min-w-0">
          <dt className="text-sm text-gray-600">Saldo</dt>
          <dd className={`tabular-nums font-medium ${balanceColor(balance_cents)}`}>
            {`${balance_cents < 0 ? '−' : ''}${formatMoney(Math.abs(balance_cents))}`}
          </dd>
        </div>
      </dl>
    </section>
  )
}
