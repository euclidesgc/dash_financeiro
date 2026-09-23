export interface CatalogueCategory {
  key: string
  label: string
  is_system: boolean
  usage_count: number
  monthly_limit_cents: number | null
}

export interface CatalogueResponse {
  categories: CatalogueCategory[]
}
