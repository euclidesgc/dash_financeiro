import { expect, test } from 'vitest'

import {
  formatMonth,
  monthRange,
  readIsoDate,
  readMonth,
  readPeriod,
  readTypedDate,
  shiftMonth,
  toDateBounds,
  writePeriod,
} from '../period'

test('monthRange gives the first and last day of the month', () => {
  expect(monthRange('2026-02')).toEqual({ from: '2026-02-01', to: '2026-02-28' })
  expect(monthRange('2028-02')).toEqual({ from: '2028-02-01', to: '2028-02-29' })
  expect(monthRange('2026-09')).toEqual({ from: '2026-09-01', to: '2026-09-30' })
})

test('shiftMonth crosses the year in both directions', () => {
  expect(shiftMonth('2026-01', -1)).toBe('2025-12')
  expect(shiftMonth('2026-12', 1)).toBe('2027-01')
  expect(shiftMonth('2026-07', -1)).toBe('2026-06')
})

test('formatMonth spells the month in pt-BR', () => {
  expect(formatMonth('2026-09')).toBe('setembro de 2026')
  expect(formatMonth('2026-01')).toBe('janeiro de 2026')
})

test('readMonth rejects what is not YYYY-MM', () => {
  expect(readMonth('2026-13')).toBeNull()
  expect(readMonth('13')).toBeNull()
  expect(readMonth('2026-9')).toBeNull()
  expect(readMonth(null)).toBeNull()
  expect(readMonth('2026-09')).toBe('2026-09')
})

test('readIsoDate rejects impossible days', () => {
  expect(readIsoDate('2026-02-31')).toBeNull()
  expect(readIsoDate('2026-13-01')).toBeNull()
  expect(readIsoDate('01/09/2026')).toBeNull()
  expect(readIsoDate(null)).toBeNull()
  expect(readIsoDate('2026-02-28')).toBe('2026-02-28')
})

test('readPeriod prefers the month over a range', () => {
  const params = new URLSearchParams('month=2026-07&from=2026-01-01')

  expect(readPeriod(params)).toEqual({ kind: 'month', month: '2026-07' })
})

test('readPeriod drops an inverted "to"', () => {
  const params = new URLSearchParams('from=2026-09-10&to=2026-09-01')

  expect(readPeriod(params)).toEqual({ kind: 'range', from: '2026-09-10', to: null })
})

test('readPeriod falls back to all on invalid values', () => {
  expect(readPeriod(new URLSearchParams('month=13'))).toEqual({ kind: 'all' })
  expect(readPeriod(new URLSearchParams(''))).toEqual({ kind: 'all' })
})

test('toDateBounds expands a month and passes a range through', () => {
  expect(toDateBounds({ kind: 'month', month: '2026-07' })).toEqual({
    from: '2026-07-01',
    to: '2026-07-31',
  })
  expect(toDateBounds({ kind: 'all' })).toEqual({ from: null, to: null })
})

test('writePeriod drops the page and the competing format', () => {
  const rangeParams = new URLSearchParams('page=2&month=2026-07&sort=amount')
  writePeriod(rangeParams, { kind: 'range', from: '2026-07-10', to: null })
  expect(rangeParams.toString()).toBe('sort=amount&from=2026-07-10')

  const monthParams = new URLSearchParams('from=2026-07-10&to=2026-07-20')
  writePeriod(monthParams, { kind: 'month', month: '2026-08' })
  expect(monthParams.toString()).toBe('month=2026-08')

  const clearParams = new URLSearchParams('page=2&month=2026-07&sort=amount')
  writePeriod(clearParams, { kind: 'all' })
  expect(clearParams.toString()).toBe('sort=amount')
})

test('readTypedDate accepts a whole date', () => {
  expect(readTypedDate('2026-09-01')).toBe('2026-09-01')
  expect(readTypedDate('1999-12-31')).toBe('1999-12-31')
})

test('readTypedDate refuses a year still being typed and an invalid date', () => {
  expect(readTypedDate('0002-09-01')).toBeNull()
  expect(readTypedDate('0202-09-01')).toBeNull()
  expect(readTypedDate('2026-02-30')).toBeNull()
  expect(readTypedDate('')).toBeNull()
})
