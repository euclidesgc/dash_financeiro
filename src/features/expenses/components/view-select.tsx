import { useId } from 'react'
import type { ExpenseView } from '@/features/expenses/types/expense'

const VIEW_OPTIONS: { value: ExpenseView; label: string }[] = [
  { value: 'expenses', label: 'Gastos' },
  { value: 'excluded', label: 'Não são gastos' },
]

export function ViewSelect({
  value,
  onChange,
}: {
  value: ExpenseView
  onChange: (view: ExpenseView) => void
}): React.JSX.Element {
  const selectId = useId()

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={selectId} className="block text-sm font-medium text-gray-900">
        Mostrar
      </label>
      <select
        id={selectId}
        value={value}
        onChange={(event) => {
          const option = VIEW_OPTIONS.find((item) => item.value === event.target.value)
          if (option) {
            onChange(option.value)
          }
        }}
        className="mt-1 block min-h-10 rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
      >
        {VIEW_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}
