import { useEffect } from 'react'
import { useUser } from '@/lib/auth'
import { AppHeader } from '@/components/layouts/app-header'
import { LogoutButton } from '@/features/auth/components/logout-button'
import { ExpensesList } from '@/features/expenses/components/expenses-list'

export function ExpensesRoute(): React.JSX.Element {
  const { data } = useUser()

  useEffect(() => {
    document.title = 'Gastos · dash_financeiro'
  }, [])

  return (
    <>
      <AppHeader userLogin={data?.login} action={<LogoutButton />} />
      <main className="mx-auto max-w-2xl p-8">
        <h1 className="text-2xl font-bold">Gastos</h1>
        <p className="mt-2 text-gray-600">
          Todos os gastos das suas contas e cartões, do mais recente ao mais antigo.
        </p>
        <ExpensesList />
      </main>
    </>
  )
}
