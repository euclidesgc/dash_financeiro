import { expect, test } from 'vitest'

import { EXPENSE_NOUN, formatCount } from '@/utils/format-count'

test('uses the singular for one', () => {
  expect(formatCount(1, EXPENSE_NOUN)).toBe('1 gasto')
})

test('uses the plural for zero', () => {
  expect(formatCount(0, EXPENSE_NOUN)).toBe('0 gastos')
})

test('uses the plural for more than one', () => {
  expect(formatCount(2, EXPENSE_NOUN)).toBe('2 gastos')
})

test('inflects every word of a compound noun given by the caller', () => {
  const noun = { one: 'gasto parecido', many: 'gastos parecidos' }

  expect(formatCount(1, noun)).toBe('1 gasto parecido')
  expect(formatCount(12, noun)).toBe('12 gastos parecidos')
})
