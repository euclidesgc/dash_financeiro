import { useId, useState } from 'react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { usePlanCeiling } from '@/features/expenses/api/get-plan-ceiling'
import { useMonthSignal } from '@/features/expenses/api/get-month-signal'
import { CeilingForm } from '@/features/expenses/components/ceiling-form'
import type { MonthSignalQuery } from '@/features/expenses/types/ceiling'
import { SIGNAL_LABELS } from '@/features/expenses/utils/signal-labels'
import { formatMoney } from '@/utils/format-money'

function ceilingText(spentCents: number, ceilingCents: number): string {
  const percent = Math.round((spentCents / ceilingCents) * 100)
  return `${formatMoney(spentCents)} de ${formatMoney(ceilingCents)} · ${String(percent)}%`
}

export function MonthCeiling({ query }: { query: MonthSignalQuery }): React.JSX.Element | null {
  const signal = useMonthSignal(query)
  const ceiling = usePlanCeiling()
  const [editing, setEditing] = useState(false)
  const headingId = useId()

  if (signal.isPending || ceiling.isPending) {
    return (
      <p role="status" className="mt-6 text-gray-600">
        Carregando teto do mês…
      </p>
    )
  }

  if (signal.isError || ceiling.isError) {
    return (
      <Alert
        message="Não foi possível carregar o teto do mês."
        action={{
          label: 'Tentar de novo',
          onClick: () => {
            void signal.refetch()
            void ceiling.refetch()
          },
        }}
      />
    )
  }

  if (signal.data.scope === 'none') {
    return null
  }

  const { ceiling_cents, spent_cents, remaining_cents } = signal.data
  function handleDone(): void {
    setEditing(false)
  }

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId} className="mt-6 text-lg font-semibold">
        Teto do mês
      </h2>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-4 rounded-md border border-gray-200 p-4">
        {ceiling_cents !== null && editing ? (
          <CeilingForm
            key={String(ceiling_cents)}
            ceilingCents={ceiling.data.monthly_ceiling_cents}
            onDone={handleDone}
          />
        ) : ceiling_cents !== null ? (
          <>
            <div className="min-w-0">
              <p className="flex flex-wrap items-center gap-2 tabular-nums font-medium">
                {ceilingText(spent_cents, ceiling_cents)}
                {signal.data.signal !== null ? (
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-sm ${SIGNAL_LABELS[signal.data.signal].className}`}
                  >
                    {SIGNAL_LABELS[signal.data.signal].text}
                  </span>
                ) : null}
              </p>
              {remaining_cents !== null && remaining_cents >= 0 ? (
                <p className="mt-1 text-sm tabular-nums text-gray-600">
                  Sobram {formatMoney(remaining_cents)}
                </p>
              ) : remaining_cents !== null ? (
                <p className="mt-1 text-sm tabular-nums text-red-800">
                  Passou {formatMoney(Math.abs(remaining_cents))}
                </p>
              ) : null}
            </div>
            <Button
              variant="secondary"
              aria-label="Alterar teto do mês"
              onClick={() => {
                setEditing(true)
              }}
            >
              Alterar teto
            </Button>
          </>
        ) : (
          <div className="w-full">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p className="text-gray-600">
                Sem teto definido. Defina um teto para saber se o mês cabe no plano.
              </p>
              {editing ? null : (
                <Button
                  variant="secondary"
                  aria-label="Definir teto do mês"
                  onClick={() => {
                    setEditing(true)
                  }}
                >
                  Definir teto
                </Button>
              )}
            </div>
            {editing ? (
              <div className="mt-3">
                <CeilingForm
                  key={String(ceiling_cents)}
                  ceilingCents={ceiling.data.monthly_ceiling_cents}
                  onDone={handleDone}
                />
              </div>
            ) : null}
          </div>
        )}
      </div>
    </section>
  )
}
