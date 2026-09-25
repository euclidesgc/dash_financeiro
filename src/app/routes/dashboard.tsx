import { useEffect } from 'react'
import { useUser } from '@/lib/auth'
import { AppHeader } from '@/components/layouts/app-header'
import { LogoutButton } from '@/features/auth/components/logout-button'
import { BalancesList } from '@/features/accounts/components/balances-list'
import { SyncPanel } from '@/features/sync/components/sync-panel'

export function DashboardRoute(): React.JSX.Element {
  const { data } = useUser()

  useEffect(() => {
    document.title = 'Saldos · dash_financeiro'
  }, [])

  return (
    <>
      <AppHeader userLogin={data?.login} action={<LogoutButton />} />
      <main className="mx-auto max-w-2xl p-8">
        <h1 className="text-2xl font-bold">Saldos de hoje</h1>
        <p className="mt-2 text-gray-600">Contas e cartões trazidos dos seus bancos pela Pluggy, o serviço que conecta este painel aos bancos.</p>
        <SyncPanel />
        <BalancesList />
      </main>
    </>
  )
}
