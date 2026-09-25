import { useId, useRef } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api-client'
import { useSetPlanCeiling } from '@/features/expenses/api/set-plan-ceiling'
import { ceilingSchema } from '@/features/expenses/types/ceiling-schema'
import type { CeilingInput } from '@/features/expenses/types/ceiling-schema'
import { formatMoneyInput, parseMoneyText } from '@/utils/money-text'

function isCeilingError(error: unknown): error is ApiError {
  return error instanceof ApiError && error.status === 422
}

export function CeilingForm({
  ceilingCents,
  onDone,
}: {
  ceilingCents: number | null
  onDone: () => void
}): React.JSX.Element {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<CeilingInput>({
    resolver: zodResolver(ceilingSchema),
    defaultValues: { ceiling: formatMoneyInput(ceilingCents) },
  })
  const mutation = useSetPlanCeiling()
  const id = useId()
  const errorId = `${id}-error`
  const isSubmitting = useRef(false)

  function save(cents: number | null): void {
    if (isSubmitting.current) return
    isSubmitting.current = true
    mutation.mutate(
      { monthly_ceiling_cents: cents },
      {
        onSuccess: onDone,
        onError: (error) => {
          if (isCeilingError(error)) setError('ceiling', { message: error.detail })
        },
        onSettled: () => {
          isSubmitting.current = false
        },
      },
    )
  }

  const onSubmit = handleSubmit((input) => {
    const amount = parseMoneyText(input.ceiling)
    if (amount.ok) save(amount.cents)
  })
  const isRemoving = mutation.isPending && mutation.variables.monthly_ceiling_cents === null

  return (
    <div className="w-full">
      <form
        onSubmit={(event) => void onSubmit(event)}
        className="flex flex-wrap items-end gap-3"
        noValidate
      >
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <label htmlFor={id} className="block text-sm font-medium text-gray-900">
            Teto mensal (R$)
          </label>
          <input
            id={id}
            type="text"
            inputMode="decimal"
            autoComplete="off"
            autoFocus
            aria-invalid={errors.ceiling ? true : undefined}
            aria-describedby={errors.ceiling ? errorId : undefined}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 min-h-10 tabular-nums aria-[invalid=true]:border-red-600"
            onKeyDown={(event) => {
              if (event.key === 'Escape') onDone()
            }}
            {...register('ceiling')}
          />
          {errors.ceiling ? (
            <p id={errorId} className="mt-1 text-sm text-red-700">
              {errors.ceiling.message}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending && !isRemoving ? 'Salvando…' : 'Salvar'}
          </Button>
          {ceilingCents !== null ? (
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                save(null)
              }}
              disabled={mutation.isPending}
            >
              {isRemoving ? 'Removendo…' : 'Remover teto'}
            </Button>
          ) : null}
          <Button type="button" variant="secondary" onClick={onDone} disabled={mutation.isPending}>
            Cancelar
          </Button>
        </div>
      </form>
      {mutation.isError && !isCeilingError(mutation.error) ? (
        <Alert message="Não foi possível salvar o teto. Tente de novo." />
      ) : null}
    </div>
  )
}
