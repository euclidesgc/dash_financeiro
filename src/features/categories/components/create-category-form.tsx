import { useId, useRef } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api-client'
import { useCreateCategory } from '@/features/categories/api/create-category'
import { categoryLabelSchema } from '@/features/categories/types/category-label-schema'
import type { CategoryLabelInput } from '@/features/categories/types/category-label-schema'

function isLabelError(error: unknown): error is ApiError {
  return error instanceof ApiError && error.status === 422
}

export function CreateCategoryForm(): React.JSX.Element {
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<CategoryLabelInput>({
    resolver: zodResolver(categoryLabelSchema),
    defaultValues: { label: '' },
  })
  const mutation = useCreateCategory()
  const id = useId()
  const errorId = `${id}-error`
  const isSubmitting = useRef(false)

  const onSubmit = handleSubmit((input) => {
    if (isSubmitting.current) return
    isSubmitting.current = true
    mutation.mutate(input, {
      onSuccess: () => { reset(); },
      onError: (error) => {
        if (isLabelError(error)) setError('label', { message: error.detail })
      },
      onSettled: () => {
        isSubmitting.current = false
      },
    })
  })

  return (
    <section aria-labelledby={`${id}-heading`}>
      <h2 id={`${id}-heading`} className="mt-8 text-lg font-semibold">
        Nova categoria
      </h2>
      <form
        onSubmit={(event) => void onSubmit(event)}
        className="mt-3 flex flex-wrap items-end gap-3"
        noValidate
      >
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <label htmlFor={id} className="block text-sm font-medium text-gray-900">
            Nome da categoria
          </label>
          <input
            id={id}
            type="text"
            autoComplete="off"
            aria-invalid={errors.label ? true : undefined}
            aria-describedby={errors.label ? errorId : undefined}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 min-h-10 aria-[invalid=true]:border-red-600"
            {...register('label')}
          />
          {errors.label ? (
            <p id={errorId} className="mt-1 text-sm text-red-700">
              {errors.label.message}
            </p>
          ) : null}
        </div>
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Criando…' : 'Criar categoria'}
        </Button>
      </form>
      {mutation.isError && !isLabelError(mutation.error) ? (
        <Alert message="Não foi possível salvar a categoria. Tente de novo." />
      ) : null}
    </section>
  )
}
