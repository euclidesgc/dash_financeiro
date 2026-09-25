import { expect, test } from 'vitest'

import { syncStatusQueryOptions } from '@/features/sync/api/get-sync-status'
import type { SyncStatus } from '@/features/sync/types/sync-status'

const refetchInterval = syncStatusQueryOptions.refetchInterval as (query: {
  state: { data: SyncStatus | undefined }
}) => number | false

test('polls every 5 seconds while running', () => {
  expect(refetchInterval({ state: { data: { running: true, last_run: null } } })).toBe(5000)
})

test('stops polling when idle', () => {
  expect(refetchInterval({ state: { data: { running: false, last_run: null } } })).toBe(false)
})

test('stops polling without data', () => {
  expect(refetchInterval({ state: { data: undefined } })).toBe(false)
})

test('has the sync status query key', () => {
  expect(syncStatusQueryOptions.queryKey).toEqual(['sync', 'status'])
})
