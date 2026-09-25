import type { Category } from '@/types/category'

export function normalizeSearchText(text: string): string {
  return text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().trim()
}

export function isCategoryInUse(category: Category): boolean {
  return category.usage_count > 0 || category.monthly_limit_cents !== null
}

export interface ArrangedCategories {
  inUse: Category[]
  others: Category[]
}

export function arrangeCategories(categories: Category[], search: string): ArrangedCategories {
  const term = normalizeSearchText(search)
  const matching =
    term === ''
      ? categories
      : categories.filter((category) => normalizeSearchText(category.label).includes(term))
  return {
    inUse: matching.filter(isCategoryInUse),
    others: matching.filter((category) => !isCategoryInUse(category)),
  }
}
