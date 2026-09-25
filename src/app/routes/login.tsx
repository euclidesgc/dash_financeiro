import { useEffect } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { paths } from '@/config/paths'
import { useUser } from '@/lib/auth'
import { LoginForm } from '@/features/auth/components/login-form'

export function LoginRoute(): React.JSX.Element {
  const navigate = useNavigate()
  const { data } = useUser()

  useEffect(() => {
    document.title = 'Entrar · dash_financeiro'
  }, [])

  if (data) {
    return <Navigate to={paths.dashboard} replace />
  }

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-bold">Entrar</h1>
      <p className="mt-2 text-gray-600">Painel financeiro pessoal.</p>
      <LoginForm
        onSuccess={() => {
          void navigate(paths.dashboard, { replace: true })
        }}
      />
    </main>
  )
}
