import { isRouteErrorResponse, Link, useRouteError } from 'react-router'
import { paths } from '@/config/paths'

export function RouteError(): React.JSX.Element {
  const error = useRouteError()
  const isNotFound = isRouteErrorResponse(error) && error.status === 404

  return (
    <main className="mx-auto max-w-2xl p-8">
      <div role="alert">
        <h1 className="text-2xl font-bold">
          {isNotFound ? 'Página não encontrada' : 'Algo deu errado'}
        </h1>
        <p className="mt-2 text-gray-600">
          {isNotFound
            ? 'O endereço que você abriu não existe ou foi movido.'
            : 'Não foi possível abrir esta página. Tente de novo em instantes.'}
        </p>
      </div>
      <Link
        to={paths.dashboard}
        replace
        className="mt-6 inline-block font-medium text-blue-600 underline-offset-4 hover:underline"
      >
        Voltar para o início
      </Link>
    </main>
  )
}
