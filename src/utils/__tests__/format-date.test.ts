import { expect, test } from 'vitest'

import { formatDate } from '@/utils/format-date'

test('formats a day-only ISO date as dd/mm/yyyy', () => {
  expect(formatDate('2026-08-01')).toBe('01/08/2026')
})

test('keeps the last day of the month regardless of timezone', () => {
  expect(formatDate('2026-07-31')).toBe('31/07/2026')
})

test('returns unknown formats untouched', () => {
  expect(formatDate('2026-08-01T10:00:00Z')).toBe('2026-08-01T10:00:00Z')
  expect(formatDate('')).toBe('')
})
