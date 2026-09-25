import { useEffect } from 'react'
import { useUser } from '@/lib/auth'
import { LogoutButton } from '@/features/auth/components/logout-button'
import { BalancesList } from '@/features/accounts/components/balances-list'

export function DashboardRoute(): React.JSX.Element {
  const { data } = useUser()

  useEffect(() => {
    document.title = 'Saldos · dash_financeiro'
  }, [])

  return (
    <>
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-2xl items-center justify-between p-4">
          <span className="font-medium text-gray-900">dash_financeiro</span>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">{data?.login}</span>
            <LogoutButton />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-2xl p-8">
        <h1 className="text-2xl font-bold">Saldos de hoje</h1>
        <p className="mt-2 text-gray-600">Contas e cartões sincronizados da Pluggy.</p>
        <BalancesList />
      </main>
    </>
  )
}
