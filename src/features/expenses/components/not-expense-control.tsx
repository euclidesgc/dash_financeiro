import { useId, useState } from 'react'
import { Button } from '@/components/ui/button'
import { useClearNotExpense } from '@/features/expenses/api/clear-not-expense'
import { useSetNotExpense } from '@/features/expenses/api/set-not-expense'
import type { Expense, ExpenseView, NotExpenseReason } from '@/features/expenses/types/expense'
import { REASON_OPTIONS } from '@/features/expenses/utils/reason-labels'

const ROW_CLASSES = 'mt-1 flex flex-wrap items-center justify-end gap-2'

const MARK_TEXT: Record<
  'expenses' | 'income',
  { button: string; ariaLabel: (name: string) => string; error: string }
> = {
  expenses: {
    button: 'Não é gasto',
    ariaLabel: (name) => `Marcar ${name} como não-gasto`,
    error: 'Não foi possível marcar como não-gasto.',
  },
  income: {
    button: 'Não é entrada',
    ariaLabel: (name) => `Marcar ${name} como não-entrada`,
    error: 'Não foi possível marcar como não-entrada.',
  },
}

export function NotExpenseControl({
  expense,
  view,
  onExcluded,
}: {
  expense: Expense
  view: ExpenseView
  onExcluded: (excluded: { id: number; description: string | null }) => void
}): React.JSX.Element {
  const [editing, setEditing] = useState(false)
  const [reason, setReason] = useState<NotExpenseReason>('own_transfer')
  const mutation = useSetNotExpense()
  const undo = useClearNotExpense()
  const selectId = useId()
  const name = expense.description ?? 'Sem descrição'

  function handleSaved(): void {
    setEditing(false)
    onExcluded({ id: expense.id, description: expense.description })
  }

  if (view === 'excluded') {
    return (
      <div className={ROW_CLASSES}>
        {undo.isError ? (
          <>
            <p role="alert" className="mt-1 text-sm text-red-700">
              Não foi possível voltar a contar.
            </p>
            <Button
              variant="secondary"
              type="button"
              onClick={() => {
                undo.mutate(expense.id)
              }}
            >
              Tentar de novo
            </Button>
          </>
        ) : (
          <Button
            variant="secondary"
            type="button"
            aria-label={`Voltar ${name} a contar`}
            disabled={undo.isPending}
            onClick={() => {
              if (undo.isPending) return
              undo.mutate(expense.id)
            }}
          >
            {undo.isPending ? 'Salvando…' : 'Voltar a contar'}
          </Button>
        )}
      </div>
    )
  }

  const text = MARK_TEXT[view]

  if (!editing) {
    return (
      <Button
        variant="secondary"
        type="button"
        aria-label={text.ariaLabel(name)}
        onClick={() => {
          setEditing(true)
        }}
      >
        {text.button}
      </Button>
    )
  }

  return (
    <div className={ROW_CLASSES}>
      <label htmlFor={selectId} className="text-sm font-medium text-gray-900">
        Motivo
      </label>
      <select
        id={selectId}
        autoFocus
        value={reason}
        onChange={(event) => {
          const option = REASON_OPTIONS.find((item) => item.value === event.target.value)
          if (option) {
            setReason(option.value)
          }
        }}
        onKeyDown={(event) => {
          if (event.key === 'Escape') {
            setEditing(false)
          }
        }}
        className="block min-h-10 rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
      >
        {REASON_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {mutation.isError ? (
        <div className="flex basis-full flex-wrap items-center justify-end gap-2">
          <p role="alert" className="mt-1 text-sm text-red-700">
            {text.error}
          </p>
          <Button
            variant="secondary"
            type="button"
            onClick={() => {
              mutation.mutate(mutation.variables, { onSuccess: handleSaved })
            }}
          >
            Tentar de novo
          </Button>
        </div>
      ) : null}
      <Button
        variant="primary"
        type="button"
        disabled={mutation.isPending}
        onClick={() => {
          if (mutation.isPending) return
          mutation.mutate({ id: expense.id, reason }, { onSuccess: handleSaved })
        }}
      >
        {mutation.isPending ? 'Salvando…' : 'Confirmar'}
      </Button>
      <Button
        variant="secondary"
        type="button"
        disabled={mutation.isPending}
        onClick={() => {
          setEditing(false)
        }}
      >
        Cancelar
      </Button>
    </div>
  )
}
