import { Alert } from '@/components/ui/alert'
import { useBalances } from '@/features/accounts/api/get-balances'
import { BalanceItem } from '@/features/accounts/components/balance-item'

export function BalancesList(): React.JSX.Element {
  const { data, isPending, isError, refetch } = useBalances()

  if (isPending) {
    return (
      <p role="status" className="mt-6 text-gray-600">
        Carregando saldos…
      </p>
    )
  }

  if (isError) {
    return (
      <Alert
        message="Não foi possível carregar os saldos."
        action={{ label: 'Tentar de novo', onClick: () => void refetch() }}
      />
    )
  }

  if (data.accounts.length === 0) {
    return (
      <p className="mt-6 rounded-md border border-dashed border-gray-300 p-6 text-center text-gray-600">
        Nenhuma conta trazida do banco ainda. Use “Atualizar agora” para buscar suas contas e cartões.
      </p>
    )
  }

  return (
    <ul className="mt-6 divide-y divide-gray-200">
      {data.accounts.map((account) => (
        <BalanceItem key={account.id} account={account} />
      ))}
    </ul>
  )
}
