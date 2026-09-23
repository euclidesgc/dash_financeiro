import { expect, test } from 'vitest'

import { formatMoney } from '@/utils/format-money'

function normalize(value: string): string {
  return value.replace(/\u00a0/g, ' ')
}

test('formats a positive amount', () => {
  const result = normalize(formatMoney(123456))

  expect(result).toContain('1.234,56')
  expect(result).toContain('R$')
})

test('formats a negative amount', () => {
  const result = normalize(formatMoney(-54321))

  expect(result).toContain('-')
  expect(result).toContain('543,21')
})

test('formats zero', () => {
  const result = normalize(formatMoney(0))

  expect(result).toContain('0,00')
})

test('keeps the cents', () => {
  const result = normalize(formatMoney(5))

  expect(result).toContain('0,05')
})
