export interface CatalogueCategory {
  key: string
  label: string
  is_system: boolean
  usage_count: number
}

export interface CatalogueResponse {
  categories: CatalogueCategory[]
}
