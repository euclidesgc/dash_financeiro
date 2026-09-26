import { expect, test } from 'vitest'

import { describeOrigin } from '../describe-origin'

test('returns null when origin is null', () => {
  expect(describeOrigin(null, 3)).toBeNull()
})

test('describes pluggy with many new transactions', () => {
  expect(describeOrigin('pluggy', 25)).toBe('Buscou na Pluggy · 25 lançamentos novos')
})

test('describes pluggy with one new transaction', () => {
  expect(describeOrigin('pluggy', 1)).toBe('Buscou na Pluggy · 1 lançamento novo')
})

test('describes file with zero new transactions', () => {
  expect(describeOrigin('file', 0)).toBe('Releu o arquivo local · nenhum lançamento novo')
})

test('returns only the origin when count is null', () => {
  expect(describeOrigin('pluggy', null)).toBe('Buscou na Pluggy')
})
