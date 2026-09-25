import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { CategoriesResponse } from '@/types/category'

export const categoriesQueryKey = ['categories'] as const

export function getCategories(): Promise<CategoriesResponse> {
  return apiRequest<CategoriesResponse>('/api/categories')
}

export function categoriesQueryOptions() {
  return queryOptions({
    queryKey: categoriesQueryKey,
    queryFn: getCategories,
  })
}

export function useCategories() {
  return useQuery(categoriesQueryOptions())
}
