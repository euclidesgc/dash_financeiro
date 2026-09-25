export interface Category {
  key: string
  label: string
  is_system: boolean
  usage_count: number
  monthly_limit_cents: number | null
}

export interface CategoriesResponse {
  categories: Category[]
}
