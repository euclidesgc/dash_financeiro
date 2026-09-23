import { expect, test } from 'vitest'

import { formatDateTime } from '@/utils/format-date-time'

test('formats a valid iso string', () => {
  const result = formatDateTime('2026-09-05T21:36:27.516Z')

  expect(result).toContain('05/09/2026')
})

test('returns null for null', () => {
  expect(formatDateTime(null)).toBeNull()
})

test('returns null for an invalid string', () => {
  expect(formatDateTime('not-a-date')).toBeNull()
})
