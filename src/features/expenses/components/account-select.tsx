import { useId } from 'react'
import { Button } from '@/components/ui/button'
import type { ExpenseAccount } from '@/features/expenses/types/expense'

export function accountOptionLabel(account: ExpenseAccount): string {
  const parts = [account.name, account.institution].filter((part): part is string => part !== null)
  const base = parts.length > 0 ? parts.join(' · ') : 'Conta sem nome'
  const suffix = account.type === 'CREDIT' ? ' (Cartão)' : ' (Conta)'
  return base + suffix
}

export function AccountSelect({
  value,
  accounts,
  isPending,
  isError,
  onChange,
  onRetry,
}: {
  value: string | null
  accounts: ExpenseAccount[]
  isPending: boolean
  isError: boolean
  onChange: (id: string | null) => void
  onRetry: () => void
}): React.JSX.Element {
  const id = useId()

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="block text-sm font-medium text-gray-900">
        Conta
      </label>
      <select
        id={id}
        value={value ?? ''}
        disabled={isPending}
        aria-busy={isPending ? 'true' : undefined}
        onChange={(event) => {
          onChange(event.target.value === '' ? null : event.target.value)
        }}
        className="mt-1 block min-h-10 rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
      >
        <option value="">Todas as contas</option>
        {!isPending && !isError
          ? accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {accountOptionLabel(account)}
              </option>
            ))
          : null}
      </select>
      {isError ? (
        <>
          <p role="alert" className="mt-1 text-sm text-red-700">
            Não foi possível carregar as contas.
          </p>
          <Button type="button" variant="secondary" onClick={onRetry}>
            Tentar de novo
          </Button>
        </>
      ) : null}
    </div>
  )
}
