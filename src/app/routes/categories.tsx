import { useEffect } from 'react'
import { useUser } from '@/lib/auth'
import { AppHeader } from '@/components/layouts/app-header'
import { LogoutButton } from '@/features/auth/components/logout-button'
import { CategoriesList } from '@/features/categories/components/categories-list'
import { CreateCategoryForm } from '@/features/categories/components/create-category-form'

export function CategoriesRoute(): React.JSX.Element {
  const { data } = useUser()

  useEffect(() => {
    document.title = 'Categorias · dash_financeiro'
  }, [])

  return (
    <>
      <AppHeader userLogin={data?.login} action={<LogoutButton />} />
      <main className="mx-auto max-w-2xl p-8">
        <h1 className="text-2xl font-bold">Categorias</h1>
        <p className="mt-2 text-gray-600">
          Crie, renomeie ou apague as categorias dos seus gastos.
        </p>
        <CreateCategoryForm />
        <CategoriesList />
      </main>
    </>
  )
}
