import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { Button } from '@/components/ui/button'
import { useUpdateCategory } from '@/features/expenses/api/update-category'
import type { Category, CategoryUpdateBody, Expense } from '@/features/expenses/types/expense'

const AUTO_OPTION = '__auto__'

export function CategoryPicker({
  expense,
  categories,
  categoriesReady,
}: {
  expense: Expense
  categories: Category[]
  categoriesReady: boolean
}): React.JSX.Element {
  const [editing, setEditing] = useState(false)
  const [chosen, setChosen] = useState<string | null>(null)
  const mutation = useUpdateCategory()
  const name = expense.description ?? 'Sem descrição'
  const label = chosen ?? expense.category ?? 'Sem categoria'
  const isManual = expense.category_source === 'manual'

  function save(body: CategoryUpdateBody): void {
    mutation.mutate(
      { id: expense.id, body },
      {
        onSettled: () => {
          setChosen(null)
        },
      },
    )
  }

  function handleChange(event: ChangeEvent<HTMLSelectElement>): void {
    const value = event.target.value
    if (value === AUTO_OPTION) {
      setChosen(null)
      save({ mode: 'auto' })
    } else if (value === '') {
      setChosen('Sem categoria')
      save({ mode: 'manual', category: null })
    } else {
      setChosen(categories.find((category) => category.key === value)?.label ?? value)
      save({ mode: 'manual', category: value })
    }
    setEditing(false)
  }

  return (
    <div className="flex flex-col items-end">
      <div className="flex items-center gap-2">
        {isManual ? <span className="text-xs text-gray-600">manual</span> : null}
        {editing ? (
          <select
            autoFocus
            aria-label={`Categoria de ${name}`}
            className="min-h-10 rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
            value={expense.category_key ?? ''}
            onChange={handleChange}
            onBlur={() => {
              setEditing(false)
            }}
            onKeyDown={(event) => {
              if (event.key === 'Escape') setEditing(false)
            }}
          >
            <option value="">Sem categoria</option>
            {categories.map((category) => (
              <option key={category.key} value={category.key}>
                {category.label}
              </option>
            ))}
            {isManual ? <option value={AUTO_OPTION}>Voltar para a automática</option> : null}
          </select>
        ) : (
          <button
            type="button"
            aria-label={`Trocar categoria de ${name}`}
            className="rounded-full px-2 py-0.5 text-sm bg-gray-100 text-gray-700 hover:bg-gray-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50"
            disabled={mutation.isPending || !categoriesReady}
            onClick={() => {
              setEditing(true)
            }}
          >
            {label}
          </button>
        )}
      </div>
      {mutation.isPending ? (
        <span role="status" className="text-xs text-gray-600">
          Salvando…
        </span>
      ) : null}
      {mutation.isError ? (
        <>
          <p role="alert" className="mt-1 text-sm text-red-700">
            Não foi possível salvar a categoria.
          </p>
          <Button
            variant="secondary"
            onClick={() => {
              mutation.mutate(mutation.variables)
            }}
          >
            Tentar de novo
          </Button>
        </>
      ) : null}
    </div>
  )
}
