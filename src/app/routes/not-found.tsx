import { useEffect } from 'react'
import { Link } from 'react-router'
import { paths } from '@/config/paths'

export function NotFoundRoute(): React.JSX.Element {
  useEffect(() => {
    document.title = 'Página não encontrada · dash_financeiro'
  }, [])

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-bold">Página não encontrada</h1>
      <p className="mt-2 text-gray-600">O endereço que você abriu não existe ou foi movido.</p>
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
