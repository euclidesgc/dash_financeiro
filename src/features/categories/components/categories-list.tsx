import { Alert } from '@/components/ui/alert'
import { useCategories } from '@/hooks/use-categories'
import { CategoryItem } from '@/features/categories/components/category-item'

export function CategoriesList(): React.JSX.Element {
  const catalogue = useCategories()

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
    return (
      <ul className="mt-6 divide-y divide-gray-200">
        {catalogue.data.categories.map((category) => (
          <CategoryItem key={category.key} category={category} />
        ))}
      </ul>
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
