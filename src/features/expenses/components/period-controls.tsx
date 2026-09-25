import { useId } from 'react'
import { Button } from '@/components/ui/button'
import type { Period } from '@/features/expenses/types/expense'
import { formatMonth, toDateBounds } from '@/features/expenses/utils/period'

export function PeriodControls({
  period,
  onMonthChange,
  onRangeChange,
  onClear,
}: {
  period: Period
  onMonthChange: (delta: -1 | 1) => void
  onRangeChange: (field: 'from' | 'to', value: string) => void
  onClear: () => void
}): React.JSX.Element {
  const fromId = useId()
  const toId = useId()
  const bounds = toDateBounds(period)

  let monthLabel = 'Todo o período'
  if (period.kind === 'month') {
    monthLabel = formatMonth(period.month)
  } else if (period.kind === 'range') {
    monthLabel = 'Período personalizado'
  }

  return (
    <fieldset className="flex flex-col gap-1">
      <legend className="text-sm font-medium text-gray-900">Mês</legend>
      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant="secondary"
          onClick={() => {
            onMonthChange(-1)
          }}
        >
          Mês anterior
        </Button>
        <span aria-live="polite" className="min-w-40 text-center text-sm text-gray-900 tabular-nums">
          {monthLabel}
        </span>
        <Button
          type="button"
          variant="secondary"
          onClick={() => {
            onMonthChange(1)
          }}
        >
          Próximo mês
        </Button>
        <Button type="button" variant="secondary" disabled={period.kind === 'all'} onClick={onClear}>
          Todo o período
        </Button>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex flex-col gap-1">
          <label htmlFor={fromId} className="block text-sm font-medium text-gray-900">
            De
          </label>
          <input
            type="date"
            id={fromId}
            value={bounds.from ?? ''}
            onChange={(event) => {
              onRangeChange('from', event.target.value)
            }}
            className="mt-1 block min-h-10 rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor={toId} className="block text-sm font-medium text-gray-900">
            Até
          </label>
          <input
            type="date"
            id={toId}
            value={bounds.to ?? ''}
            onChange={(event) => {
              onRangeChange('to', event.target.value)
            }}
            className="mt-1 block min-h-10 rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          />
        </div>
      </div>
    </fieldset>
  )
}
