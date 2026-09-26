import { useEffect } from 'react'
import { useUser } from '@/lib/auth'
import { AppHeader } from '@/components/layouts/app-header'
import { LogoutButton } from '@/features/auth/components/logout-button'
import { AdvisorChat } from '@/features/advisor/components/advisor-chat'

export function AdvisorRoute(): React.JSX.Element {
  const { data } = useUser()

  useEffect(() => {
    document.title = 'Consultor · dash_financeiro'
  }, [])

  return (
    <>
      <AppHeader userLogin={data?.login} action={<LogoutButton />} />
      <main className="mx-auto max-w-2xl p-8">
        <h1 className="text-2xl font-bold">Consultor</h1>
        <p className="mt-2 text-gray-600">
          Pergunte sobre seus lançamentos em português. O consultor busca nos seus dados e responde
          com os valores do painel.
        </p>
        <AdvisorChat />
      </main>
    </>
  )
}
