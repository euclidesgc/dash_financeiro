import { useState } from 'react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api-client'
import { useDeleteCategory } from '@/features/categories/api/delete-category'
import { RenameCategoryForm } from '@/features/categories/components/rename-category-form'
import type { CatalogueCategory } from '@/features/categories/types/category'

function usageText(count: number): string {
  if (count === 0) return 'Nenhum gasto'
  if (count === 1) return '1 gasto'
  return `${String(count)} gastos`
}

function deleteErrorMessage(error: unknown): string {
  if (error instanceof ApiError && (error.status === 403 || error.status === 409)) {
    return error.detail
  }
  return 'Não foi possível apagar a categoria. Tente de novo.'
}

export function CategoryItem({ category }: { category: CatalogueCategory }): React.JSX.Element {
  const [mode, setMode] = useState<'view' | 'rename' | 'confirm-delete' | 'in-use'>('view')
  const deletion = useDeleteCategory()

  const badgeColor = category.is_system ? 'bg-gray-100 text-gray-700' : 'bg-blue-100 text-blue-800'

  const deleteError = deletion.isError ? (
    <div className="w-full">
      <Alert
        message={deleteErrorMessage(deletion.error)}
        action={{ label: 'Tentar de novo', onClick: () => { deletion.mutate({ key: category.key }); } }}
      />
    </div>
  ) : null

  function confirmDelete(): void {
    if (deletion.isPending) return
    deletion.mutate({ key: category.key }, { onSuccess: () => { setMode('view'); } })
  }

  return (
    <li className="flex flex-wrap items-start justify-between gap-x-4 gap-y-3 py-3">
      <div className="flex min-w-0 flex-1 items-center gap-2">
        <span className="min-w-0 font-medium truncate text-gray-900" title={category.label}>
          {category.label}
        </span>
        <span className={`rounded-full px-2 py-0.5 text-sm ${badgeColor} shrink-0`}>
          {category.is_system ? 'Do sistema' : 'Criada por você'}
        </span>
      </div>

      {mode === 'view' ? (
        <>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <span className="text-sm text-gray-600 tabular-nums">
              {usageText(category.usage_count)}
            </span>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="secondary"
                aria-label={`Renomear ${category.label}`}
                onClick={() => { setMode('rename'); }}
              >
                Renomear
              </Button>
              {!category.is_system ? (
                <Button
                  type="button"
                  variant="secondary"
                  aria-label={`Apagar ${category.label}`}
                  onClick={() => { setMode(category.usage_count > 0 ? 'in-use' : 'confirm-delete'); }}
                >
                  Apagar
                </Button>
              ) : null}
            </div>
          </div>
          {deleteError}
        </>
      ) : null}

      {mode === 'rename' ? (
        <RenameCategoryForm key={category.label} category={category} onDone={() => { setMode('view'); }} />
      ) : null}

      {mode === 'confirm-delete' ? (
        <div className="w-full">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-800">{`Apagar a categoria “${category.label}”?`}</p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="danger"
                disabled={deletion.isPending}
                onClick={confirmDelete}
              >
                {deletion.isPending ? 'Apagando…' : 'Confirmar'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="bg-white"
                disabled={deletion.isPending}
                onClick={() => { setMode('view'); }}
              >
                Cancelar
              </Button>
            </div>
          </div>
          {deleteError}
        </div>
      ) : null}

      {mode === 'in-use' ? (
        <div
          role="alert"
          className="flex w-full flex-wrap items-center justify-between gap-3 rounded-md border border-red-200 bg-red-50 p-3"
        >
          <p className="min-w-0 flex-1 text-sm text-red-800">
            {`Esta categoria está em uso por ${usageText(category.usage_count)}. Troque a categoria desses gastos antes de apagá-la.`}
          </p>
          <Button
            type="button"
            variant="secondary"
            className="bg-white"
            onClick={() => { setMode('view'); }}
          >
            Fechar
          </Button>
        </div>
      ) : null}
    </li>
  )
}
