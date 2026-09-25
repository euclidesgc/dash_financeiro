import { expect, test } from 'vitest'

import {
  arrangeCategories,
  normalizeSearchText,
} from '@/features/categories/utils/arrange-categories'
import type { Category } from '@/types/category'

function category(label: string, usage: number, limit: number | null): Category {
  return { key: label, label, is_system: true, usage_count: usage, monthly_limit_cents: limit }
}

const catalogue = [
  category('Água', 0, null),
  category('Casa', 2, null),
  category('Farmácia', 0, 30000),
  category('Lazer', 0, null),
]

test('puts categories with spending or a limit first, keeping the catalogue order in each group', () => {
  const result = arrangeCategories(catalogue, '')

  expect(result.inUse.map((item) => item.label)).toEqual(['Casa', 'Farmácia'])
  expect(result.others.map((item) => item.label)).toEqual(['Água', 'Lazer'])
})

test('filters by label ignoring case and accents', () => {
  const result = arrangeCategories(catalogue, '  FARMACIA ')

  expect(result.inUse.map((item) => item.label)).toEqual(['Farmácia'])
  expect(result.others).toEqual([])
})

test('matches a term typed with accent against a label without it', () => {
  const result = arrangeCategories([category('Agua', 0, null)], 'água')

  expect(result.others.map((item) => item.label)).toEqual(['Agua'])
})

test('returns empty groups when nothing matches', () => {
  const result = arrangeCategories(catalogue, 'xyz')

  expect(result).toEqual({ inUse: [], others: [] })
})

test('normalizes text to lowercase without diacritics', () => {
  expect(normalizeSearchText(' Ação ')).toBe('acao')
})
