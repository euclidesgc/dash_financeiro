import { queryOptions, useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'
import type { PluggyConnectionsResponse } from '@/features/pluggy-connections/types/pluggy-connection'

export function getConnections(): Promise<PluggyConnectionsResponse> {
  return apiRequest<PluggyConnectionsResponse>('/api/pluggy-connections')
}

export function connectionsQueryOptions() {
  return queryOptions({
    queryKey: ['pluggy-connections'],
    queryFn: getConnections,
  })
}

export function useConnections() {
  return useQuery(connectionsQueryOptions())
}
