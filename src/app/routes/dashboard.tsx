import { useEffect } from 'react'
import { useUser } from '@/lib/auth'
import { AppHeader } from '@/components/layouts/app-header'
import { LogoutButton } from '@/features/auth/components/logout-button'
import { BalancesList } from '@/features/accounts/components/balances-list'
import { MonthPlanCard } from '@/features/expenses/components/month-plan-card'
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
        <p className="mt-2 text-gray-600">Contas e cartões sincronizados da Pluggy.</p>
        <SyncPanel />
        <MonthPlanCard />
        <BalancesList />
      </main>
    </>
  )
}
