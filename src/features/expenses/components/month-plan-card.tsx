import { useId, useState } from 'react'
import { Link } from 'react-router'
import { Alert } from '@/components/ui/alert'
import { paths } from '@/config/paths'
import { useMonthSignal } from '@/features/expenses/api/get-month-signal'
import { usePeriodResult } from '@/features/expenses/api/get-period-result'
import { currentMonth, formatMonth, monthRange } from '@/features/expenses/utils/period'
import { SIGNAL_LABELS } from '@/features/expenses/utils/signal-labels'
import { formatMoney } from '@/utils/format-money'

function balanceColor(balanceCents: number): string {
  if (balanceCents > 0) return 'text-green-700'
  if (balanceCents < 0) return 'text-red-700'
  return 'text-gray-900'
}

function signedMoney(cents: number): string {
  return `${cents < 0 ? '−' : ''}${formatMoney(Math.abs(cents))}`
}

export function MonthPlanCard(): React.JSX.Element {
  const [month] = useState(currentMonth)
  const { from, to } = monthRange(month)
  const signal = useMonthSignal({ from, to })
  const result = usePeriodResult({ from, to, account: null, search: null })
  const headingId = useId()
  const monthName = formatMonth(month)
  const expensesLink = `${paths.expenses}?month=${month}`

  if (signal.isPending || result.isPending) {
    return (
      <p role="status" className="mt-6 text-gray-600">
        Carregando o plano do mês…
      </p>
    )
  }

  if (signal.isError || result.isError) {
    return (
      <Alert
        message="Não foi possível carregar o plano do mês."
        action={{
          label: 'Tentar de novo',
          onClick: () => {
            void signal.refetch()
            void result.refetch()
          },
        }}
      />
    )
  }

  const { spent_cents, ceiling_cents, remaining_cents } = signal.data
  const planSignal = signal.data.signal
  const { balance_cents } = result.data

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId} className="mt-6 text-lg font-semibold">
        Plano de {monthName}
      </h2>
      <div className="mt-2 rounded-md border border-gray-200 p-4">
        <dl className="flex flex-wrap gap-x-8 gap-y-2">
          <div className="min-w-0">
            <dt className="text-sm text-gray-600">Gasto no mês</dt>
            <dd className="flex flex-wrap items-center gap-2 tabular-nums font-medium">
              {formatMoney(spent_cents)}
              {planSignal !== null ? (
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-sm ${SIGNAL_LABELS[planSignal].className}`}
                >
                  {SIGNAL_LABELS[planSignal].text}
                </span>
              ) : null}
            </dd>
          </div>
          <div className="min-w-0">
            <dt className="text-sm text-gray-600">Teto do mês</dt>
            <dd className="tabular-nums font-medium text-gray-900">
              {ceiling_cents !== null ? formatMoney(ceiling_cents) : 'Sem teto'}
            </dd>
          </div>
          <div className="min-w-0">
            <dt className="text-sm text-gray-600">Resultado até hoje</dt>
            <dd className={`tabular-nums font-medium ${balanceColor(balance_cents)}`}>
              {signedMoney(balance_cents)}
            </dd>
          </div>
        </dl>
        {ceiling_cents === null ? (
          <p className="mt-3 text-sm text-gray-600">
            Sem teto definido, não dá para saber se o mês cabe no plano. Defina o teto na tela de
            gastos.
          </p>
        ) : remaining_cents !== null && remaining_cents >= 0 ? (
          <p className="mt-3 text-sm tabular-nums text-gray-600">
            Sobram {formatMoney(remaining_cents)} até o teto.
          </p>
        ) : remaining_cents !== null ? (
          <p className="mt-3 text-sm tabular-nums text-red-800">
            Passou {formatMoney(Math.abs(remaining_cents))} do teto.
          </p>
        ) : null}
        <Link
          to={expensesLink}
          className="mt-3 inline-block font-medium text-blue-600 underline-offset-4 hover:underline"
        >
          {ceiling_cents === null ? 'Definir o teto do mês' : 'Ver o mês em detalhe'}
        </Link>
      </div>
    </section>
  )
}
