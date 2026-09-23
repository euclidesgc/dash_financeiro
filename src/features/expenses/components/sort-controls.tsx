import { useId } from 'react'
import { Button } from '@/components/ui/button'
import type { ExpenseOrder, ExpenseSort } from '@/features/expenses/types/expense'

const SORT_OPTIONS: { value: ExpenseSort; label: string }[] = [
  { value: 'date', label: 'Data' },
  { value: 'amount', label: 'Valor' },
  { value: 'category', label: 'Categoria' },
]

export function SortControls({
  sort,
  order,
  onSortChange,
  onOrderToggle,
}: {
  sort: ExpenseSort
  order: ExpenseOrder
  onSortChange: (sort: ExpenseSort) => void
  onOrderToggle: () => void
}): React.JSX.Element {
  const selectId = useId()

  return (
    <>
      <div className="flex flex-col gap-1">
        <label htmlFor={selectId} className="block text-sm font-medium text-gray-900">
          Ordenar por
        </label>
        <select
          id={selectId}
          value={sort}
          onChange={(event) => {
            const option = SORT_OPTIONS.find((item) => item.value === event.target.value)
            if (option) {
              onSortChange(option.value)
            }
          }}
          className="mt-1 block min-h-10 rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      <Button
        type="button"
        variant="secondary"
        aria-label="Inverter direção da ordenação"
        onClick={onOrderToggle}
      >
        {order === 'desc' ? 'Decrescente' : 'Crescente'}
      </Button>
    </>
  )
}
