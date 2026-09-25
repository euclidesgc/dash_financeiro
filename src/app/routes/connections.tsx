import { useEffect } from 'react'
import { useUser } from '@/lib/auth'
import { AppHeader } from '@/components/layouts/app-header'
import { LogoutButton } from '@/features/auth/components/logout-button'
import { AddConnectionForm } from '@/features/pluggy-connections/components/add-connection-form'
import { ConnectionsList } from '@/features/pluggy-connections/components/connections-list'

export function ConnectionsRoute(): React.JSX.Element {
  const { data } = useUser()

  useEffect(() => {
    document.title = 'Conexões · dash_financeiro'
  }, [])

  return (
    <>
      <AppHeader userLogin={data?.login} action={<LogoutButton />} />
      <main className="mx-auto max-w-2xl p-8">
        <h1 className="text-2xl font-bold">Conexões</h1>
        <p className="mt-2 text-gray-600">
          As conexões da Pluggy que a atualização busca, uma por banco. Quando um banco pedir novo
          login e a conexão for refeita, cadastre o identificador novo e remova o antigo.
        </p>
        <AddConnectionForm />
        <ConnectionsList />
      </main>
    </>
  )
}
