import { useId, useState } from 'react'
import { Button } from '@/components/ui/button'
import type { Period } from '@/features/expenses/types/expense'
import { formatMonth, readTypedDate, toDateBounds } from '@/features/expenses/utils/period'

type DateField = 'from' | 'to'

interface DateDraft {
  value: string
  isPending: boolean
}

interface RangeDraft {
  boundsKey: string
  from: DateDraft
  to: DateDraft
}

const INVERTED_RANGE_MESSAGE = '"Até" não pode ser antes de "De".'

function toDraft(bounds: { from: string | null; to: string | null }): RangeDraft {
  return {
    boundsKey: `${bounds.from ?? ''}|${bounds.to ?? ''}`,
    from: { value: bounds.from ?? '', isPending: false },
    to: { value: bounds.to ?? '', isPending: false },
  }
}

// Reason: a date field with a segment still half typed reports an empty
// value and flags badInput; only an empty value without it is a date the
// person erased.
function readDateInput(input: HTMLInputElement): DateDraft {
  if (input.value === '') {
    return { value: '', isPending: input.validity.badInput }
  }
  return { value: input.value, isPending: readTypedDate(input.value) === null }
}

function isInverted(draft: RangeDraft): boolean {
  if (draft.from.isPending || draft.to.isPending) {
    return false
  }
  return draft.from.value !== '' && draft.to.value !== '' && draft.to.value < draft.from.value
}

export function PeriodControls({
  period,
  onMonthChange,
  onRangeChange,
  onClear,
}: {
  period: Period
  onMonthChange: (delta: -1 | 1) => void
  onRangeChange: (from: string | null, to: string | null) => void
  onClear: () => void
}): React.JSX.Element {
  const fromId = useId()
  const toId = useId()
  const errorId = useId()
  const bounds = toDateBounds(period)
  const boundsDraft = toDraft(bounds)
  const [draft, setDraft] = useState(boundsDraft)

  // Reason: the fields hold what is typed until the range is whole; a period
  // changed from outside (month buttons, "Todo o período", the URL) replaces
  // that draft, the React way of resetting state when a prop changes.
  let shownDraft = draft
  if (draft.boundsKey !== boundsDraft.boundsKey) {
    shownDraft = boundsDraft
    setDraft(boundsDraft)
  }
  const inverted = isInverted(shownDraft)

  function handleDateInput(field: DateField, input: HTMLInputElement): void {
    const next = { ...shownDraft, [field]: readDateInput(input) }
    setDraft(next)
    if (next.from.isPending || next.to.isPending || isInverted(next)) {
      return
    }
    onRangeChange(next.from.value || null, next.to.value || null)
  }

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
            value={shownDraft.from.value}
            aria-invalid={inverted}
            aria-describedby={inverted ? errorId : undefined}
            onChange={(event) => {
              handleDateInput('from', event.target)
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
            value={shownDraft.to.value}
            aria-invalid={inverted}
            aria-describedby={inverted ? errorId : undefined}
            onChange={(event) => {
              handleDateInput('to', event.target)
            }}
            className="mt-1 block min-h-10 rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          />
        </div>
      </div>
      {inverted ? (
        <p id={errorId} role="alert" className="mt-1 text-sm text-red-700">
          {INVERTED_RANGE_MESSAGE}
        </p>
      ) : null}
    </fieldset>
  )
}
