import { useId } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api-client'
import { useRenameCategory } from '@/features/categories/api/rename-category'
import { categoryLabelSchema } from '@/features/categories/types/category-label-schema'
import type { CategoryLabelInput } from '@/features/categories/types/category-label-schema'
import type { CatalogueCategory } from '@/features/categories/types/category'

function isLabelError(error: unknown): error is ApiError {
  return error instanceof ApiError && error.status === 422
}

export function RenameCategoryForm({
  category,
  onDone,
}: {
  category: CatalogueCategory
  onDone: () => void
}): React.JSX.Element {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<CategoryLabelInput>({
    resolver: zodResolver(categoryLabelSchema),
    defaultValues: { label: category.label },
  })
  const mutation = useRenameCategory()
  const id = useId()
  const errorId = `${id}-error`

  const onSubmit = handleSubmit((input) => {
    if (mutation.isPending) return
    mutation.mutate(
      { key: category.key, label: input.label },
      {
        onSuccess: onDone,
        onError: (error) => {
          if (isLabelError(error)) setError('label', { message: error.detail })
        },
      },
    )
  })

  return (
    <div className="w-full">
      <form
        onSubmit={(event) => void onSubmit(event)}
        className="flex flex-wrap items-end gap-3"
        noValidate
      >
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <label htmlFor={id} className="block text-sm font-medium text-gray-900">
            Novo nome
          </label>
          <input
            id={id}
            type="text"
            autoComplete="off"
            autoFocus
            aria-invalid={errors.label ? true : undefined}
            aria-describedby={errors.label ? errorId : undefined}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 min-h-10 aria-[invalid=true]:border-red-600"
            onKeyDown={(event) => {
              if (event.key === 'Escape') onDone()
            }}
            {...register('label')}
          />
          {errors.label ? (
            <p id={errorId} className="mt-1 text-sm text-red-700">
              {errors.label.message}
            </p>
          ) : null}
        </div>
        <div className="flex gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Salvando…' : 'Salvar'}
          </Button>
          <Button type="button" variant="secondary" onClick={onDone} disabled={mutation.isPending}>
            Cancelar
          </Button>
        </div>
      </form>
      {mutation.isError && !isLabelError(mutation.error) ? (
        <Alert message="Não foi possível salvar a categoria. Tente de novo." />
      ) : null}
    </div>
  )
}
