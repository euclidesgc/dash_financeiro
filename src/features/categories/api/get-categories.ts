import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { CatalogueResponse } from '@/features/categories/types/category'

export function getCatalogue(): Promise<CatalogueResponse> {
  return apiRequest<CatalogueResponse>('/api/categories')
}

export function catalogueQueryOptions() {
  return queryOptions({
    queryKey: ['categories'],
    queryFn: getCatalogue,
  })
}

export function useCatalogue() {
  return useQuery(catalogueQueryOptions())
}
