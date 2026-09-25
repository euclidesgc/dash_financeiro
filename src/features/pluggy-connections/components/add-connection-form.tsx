import { useId, useRef } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api-client'
import { useAddConnection } from '@/features/pluggy-connections/api/add-connection'
import { itemIdSchema } from '@/features/pluggy-connections/types/item-id-schema'
import type { ItemIdInput } from '@/features/pluggy-connections/types/item-id-schema'

function isFieldError(error: unknown): error is ApiError {
  return error instanceof ApiError && (error.status === 409 || error.status === 422)
}

export function AddConnectionForm(): React.JSX.Element {
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<ItemIdInput>({
    resolver: zodResolver(itemIdSchema),
    defaultValues: { itemId: '' },
  })
  const mutation = useAddConnection()
  const id = useId()
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  const isSubmitting = useRef(false)

  const onSubmit = handleSubmit((input) => {
    if (isSubmitting.current) return
    isSubmitting.current = true
    mutation.mutate(input, {
      onSuccess: () => {
        reset()
      },
      onError: (error) => {
        if (isFieldError(error)) setError('itemId', { message: error.detail })
      },
      onSettled: () => {
        isSubmitting.current = false
      },
    })
  })

  return (
    <section aria-labelledby={`${id}-heading`}>
      <h2 id={`${id}-heading`} className="mt-8 text-lg font-semibold">
        Nova conexão
      </h2>
      <form
        onSubmit={(event) => void onSubmit(event)}
        className="mt-3 flex flex-wrap items-end gap-3"
        noValidate
      >
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <label htmlFor={id} className="block text-sm font-medium text-gray-900">
            Identificador da conexão
          </label>
          <input
            id={id}
            type="text"
            autoComplete="off"
            spellCheck={false}
            placeholder="00000000-0000-0000-0000-000000000000"
            aria-invalid={errors.itemId ? true : undefined}
            aria-describedby={errors.itemId ? `${hintId} ${errorId}` : hintId}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 min-h-10 aria-[invalid=true]:border-red-600"
            {...register('itemId')}
          />
          <p id={hintId} className="text-sm text-gray-600">
            Copie o identificador da conexão em meu.pluggy.ai.
          </p>
          {errors.itemId ? (
            <p id={errorId} className="mt-1 text-sm text-red-700">
              {errors.itemId.message}
            </p>
          ) : null}
        </div>
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Cadastrando…' : 'Cadastrar conexão'}
        </Button>
      </form>
      {mutation.isError && !isFieldError(mutation.error) ? (
        <Alert message="Não foi possível cadastrar a conexão. Tente de novo." />
      ) : null}
    </section>
  )
}
