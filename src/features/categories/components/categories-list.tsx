import { useId, useState } from 'react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { useCategories } from '@/hooks/use-categories'
import { CategoryItem } from '@/features/categories/components/category-item'
import { arrangeCategories } from '@/features/categories/utils/arrange-categories'

export function CategoriesList(): React.JSX.Element {
  const catalogue = useCategories()
  const [search, setSearch] = useState('')
  const searchId = useId()

  function content(): React.JSX.Element {
    if (catalogue.isPending) {
      return (
        <p role="status" className="mt-6 text-gray-600">
          Carregando categorias…
        </p>
      )
    }
    if (catalogue.isError) {
      return (
        <Alert
          message="Não foi possível carregar as categorias."
          action={{ label: 'Tentar de novo', onClick: () => void catalogue.refetch() }}
        />
      )
    }
    const { inUse, others } = arrangeCategories(catalogue.data.categories, search)
    return (
      <>
        <div role="search" className="mt-6 flex flex-col gap-1">
          <label htmlFor={searchId} className="block text-sm font-medium text-gray-900">
            Buscar categoria
          </label>
          <div className="flex items-center gap-2">
            <input
              type="search"
              id={searchId}
              value={search}
              placeholder="Nome da categoria"
              autoComplete="off"
              onChange={(event) => {
                setSearch(event.target.value)
              }}
              className="mt-1 block min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
            />
            {search !== '' && (
              <Button
                type="button"
                variant="secondary"
                aria-label="Limpar busca"
                onClick={() => {
                  setSearch('')
                }}
              >
                Limpar
              </Button>
            )}
          </div>
        </div>
        {inUse.length === 0 && others.length === 0 ? (
          <p className="mt-6 rounded-md border border-dashed border-gray-300 p-6 text-center text-gray-600">
            Nenhuma categoria com “{search.trim()}”. Confira a grafia ou crie a categoria acima.
          </p>
        ) : (
          <>
            <p className="mt-4 text-sm text-gray-600">
              <span className="tabular-nums">{inUse.length}</span> com gastos ou limite aparecem
              primeiro; depois, <span className="tabular-nums">{others.length}</span> sem uso.
            </p>
            <ul className="mt-2 divide-y divide-gray-200">
              {[...inUse, ...others].map((category) => (
                <CategoryItem key={category.key} category={category} />
              ))}
            </ul>
          </>
        )}
      </>
    )
  }

  return (
    <section aria-labelledby="catalogue-heading">
      <h2 id="catalogue-heading" className="mt-8 text-lg font-semibold">
        Catálogo
      </h2>
      {content()}
    </section>
  )
}
