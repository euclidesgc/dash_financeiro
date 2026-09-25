import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { CategoriesResponse } from '@/features/expenses/types/expense'

export function getCategories(): Promise<CategoriesResponse> {
  return apiRequest<CategoriesResponse>('/api/categories')
}

export function categoriesQueryOptions() {
  return queryOptions({
    queryKey: ['categories'],
    queryFn: getCategories,
    // The catalogue is the seed and only changes with a deploy.
    staleTime: Infinity,
  })
}

export function useCategories() {
  return useQuery(categoriesQueryOptions())
}
