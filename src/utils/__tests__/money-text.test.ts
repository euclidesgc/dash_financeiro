import { expect, test } from 'vitest'

import { formatMoneyInput, parseMoneyText } from '../money-text'
import { moneyTextSchema } from '../money-text-schema'

test.each([
  ['1.500,00', 150000],
  ['1500', 150000],
  ['1.500', 150000],
  ['R$ 1.500,00', 150000],
  ['1500,00', 150000],
  ['  1.500,00  ', 150000],
  ['1500,5', 150050],
  ['1500.50', 150050],
  ['150.5', 15050],
  ['1.234.567,89', 123456789],
  ['0,01', 1],
  ['19,99', 1999],
  ['0.29', 29],
])('parseMoneyText reads "%s" as %i cents', (text, cents) => {
  expect(parseMoneyText(text)).toEqual({ ok: true, cents })
})

test.each([
  ['', 'empty'],
  ['   ', 'empty'],
  ['abc', 'format'],
  ['15,00,0', 'format'],
  ['1.50,00', 'format'],
  ['1500,', 'format'],
  ['12.3.4', 'format'],
  ['1,999', 'decimals'],
  ['1500.999', 'decimals'],
  ['-5', 'not-positive'],
  ['-1.500,00', 'not-positive'],
  ['0', 'not-positive'],
  ['0,00', 'not-positive'],
])('parseMoneyText refuses "%s" as %s', (text, reason) => {
  expect(parseMoneyText(text)).toEqual({ ok: false, reason })
})

test('formatMoneyInput writes the saved value in the format the field asks for', () => {
  expect(formatMoneyInput(150000)).toBe('1.500,00')
  expect(formatMoneyInput(10)).toBe('0,10')
  expect(formatMoneyInput(null)).toBe('')
})

test('formatMoneyInput output reads back as the same cents', () => {
  for (const cents of [1, 99, 150000, 123456789]) {
    expect(parseMoneyText(formatMoneyInput(cents))).toEqual({ ok: true, cents })
  }
})

test.each([
  ['', 'Informe um valor.'],
  ['abc', 'Use o formato 1.500,00.'],
  ['1,999', 'Use no máximo duas casas decimais.'],
  ['-5', 'Informe um valor maior que zero.'],
])('moneyTextSchema explains why "%s" is refused', (text, message) => {
  const result = moneyTextSchema.safeParse(text)
  expect(result.success).toBe(false)
  expect(result.error?.issues[0]?.message).toBe(message)
})

test('moneyTextSchema accepts a pt-BR amount', () => {
  expect(moneyTextSchema.safeParse('1.500,00').success).toBe(true)
})
