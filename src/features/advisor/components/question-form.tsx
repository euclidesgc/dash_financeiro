import { useId } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import { questionSchema } from '@/features/advisor/types/question-schema'
import type { QuestionInput } from '@/features/advisor/types/question-schema'

export function QuestionForm({
  isPending,
  onAsk,
}: {
  isPending: boolean
  onAsk: (text: string, onSent: () => void) => void
}): React.JSX.Element {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<QuestionInput>({
    resolver: zodResolver(questionSchema),
    defaultValues: { text: '' },
  })
  const id = useId()
  const errorId = `${id}-error`
  const hintId = `${id}-hint`

  const onSubmit = handleSubmit((input) => {
    if (isPending) return
    onAsk(input.text, () => {
      reset()
    })
  })

  return (
    <form onSubmit={(event) => void onSubmit(event)} className="mt-6 flex flex-col gap-3" noValidate>
      <div className="flex flex-col gap-1">
        <label htmlFor={id} className="block text-sm font-medium text-gray-900">
          Sua pergunta
        </label>
        <textarea
          id={id}
          rows={3}
          placeholder="Ex.: quais foram meus gastos com posto em agosto?"
          aria-invalid={errors.text ? true : undefined}
          aria-describedby={errors.text ? `${hintId} ${errorId}` : hintId}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 aria-[invalid=true]:border-red-600"
          {...register('text')}
        />
        <p id={hintId} className="text-sm text-gray-600">
          Os valores da resposta saem da mesma conta das telas do painel.
        </p>
        {errors.text ? (
          <p id={errorId} className="mt-1 text-sm text-red-700">
            {errors.text.message}
          </p>
        ) : null}
      </div>
      <div>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Consultando…' : 'Perguntar'}
        </Button>
      </div>
    </form>
  )
}
