import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api-client'
import { useLogin } from '@/features/auth/api/login'
import { loginSchema } from '@/features/auth/types/login-schema'
import type { LoginInput } from '@/features/auth/types/login-schema'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return 'Login ou senha inválidos.'
    }
    if (error.status === 429) {
      return 'Muitas tentativas seguidas. Tente novamente mais tarde.'
    }
  }
  return 'Não foi possível entrar. Verifique se o servidor está no ar e tente de novo.'
}

export function LoginForm({ onSuccess }: { onSuccess: () => void }): React.JSX.Element {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({ resolver: zodResolver(loginSchema) })
  const loginMutation = useLogin()

  const onSubmit = handleSubmit((input) => {
    loginMutation.mutate(input, { onSuccess })
  })

  return (
    <form onSubmit={(event) => void onSubmit(event)} className="mt-6" noValidate>
      <div>
        <label htmlFor="login" className="block text-sm font-medium text-gray-900">
          Login
        </label>
        <input
          id="login"
          type="text"
          autoComplete="username"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          {...register('login')}
        />
        {errors.login ? (
          <p className="mt-1 text-sm text-red-700">{errors.login.message}</p>
        ) : null}
      </div>

      <div className="mt-4">
        <label htmlFor="password" className="block text-sm font-medium text-gray-900">
          Senha
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          {...register('password')}
        />
        {errors.password ? (
          <p className="mt-1 text-sm text-red-700">{errors.password.message}</p>
        ) : null}
      </div>

      {loginMutation.isError ? <Alert message={errorMessage(loginMutation.error)} /> : null}

      <div className="mt-4">
        <Button type="submit" disabled={loginMutation.isPending}>
          {loginMutation.isPending ? 'Entrando…' : 'Entrar'}
        </Button>
      </div>
    </form>
  )
}
