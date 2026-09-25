import { formatDateTime } from '@/utils/format-date-time'
import { formatMoney } from '@/utils/format-money'
import type { AccountBalance } from '@/features/accounts/types/account-balance'

export function BalanceItem({ account }: { account: AccountBalance }): React.JSX.Element {
  const updatedAt = formatDateTime(account.updated_at)
  const isCredit = account.type === 'CREDIT'
  const amountColor = account.balance_cents < 0 ? 'text-red-700' : 'text-gray-900'

  return (
    <li className="flex items-center justify-between gap-4 py-3">
      <div className="min-w-0">
        <p className="font-medium truncate text-gray-900">{account.name ?? 'Conta sem nome'}</p>
        {account.institution ? (
          <p className="text-sm text-gray-600 truncate">{account.institution}</p>
        ) : null}
        <p className="text-sm text-gray-600">
          {updatedAt ? `Saldo informado pelo banco em ${updatedAt}` : 'Sem data de atualização'}
        </p>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1 text-right">
        {isCredit ? (
          <span className="rounded-full px-2 py-0.5 text-sm bg-amber-100 text-amber-800">Cartão</span>
        ) : (
          <span className="rounded-full px-2 py-0.5 text-sm bg-gray-100 text-gray-700">Conta</span>
        )}
        <span className={`tabular-nums font-medium ${amountColor}`}>
          {formatMoney(account.balance_cents)}
        </span>
      </div>
    </li>
  )
}
