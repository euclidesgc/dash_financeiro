import { expect, test } from 'vitest'

import { fromCents, toCents } from '../cents'

test('toCents turns an empty string into null', () => {
  expect(toCents('')).toBeNull()
  expect(toCents('  ')).toBeNull()
})

test('toCents converts reais with dot or comma into integer cents', () => {
  expect(toCents('12.5')).toBe(1250)
  expect(toCents('0.1')).toBe(10)
  expect(toCents('1,99')).toBe(199)
  expect(toCents('1500')).toBe(150000)
})

test('toCents has no floating point drift', () => {
  expect(toCents('19.99')).toBe(1999)
  expect(toCents('0.29')).toBe(29)
  expect(toCents('1.15')).toBe(115)
})

test('fromCents turns null into an empty string', () => {
  expect(fromCents(null)).toBe('')
})

test('fromCents writes two decimals with a dot', () => {
  expect(fromCents(150000)).toBe('1500.00')
  expect(fromCents(10)).toBe('0.10')
})
