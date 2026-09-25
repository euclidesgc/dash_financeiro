import type { Period } from '@/features/expenses/types/expense'

const MONTH_NAMES = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
]

export function readMonth(value: string | null): string | null {
  if (value === null || !/^\d{4}-(0[1-9]|1[0-2])$/.test(value)) {
    return null
  }
  return value
}

export function daysInMonth(year: number, month: number): number {
  return new Date(Date.UTC(year, month, 0)).getUTCDate()
}

export function readIsoDate(value: string | null): string | null {
  if (value === null || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return null
  }
  const [yearText, monthText, dayText] = value.split('-')
  const year = Number(yearText)
  const month = Number(monthText)
  const day = Number(dayText)
  if (month < 1 || month > 12) {
    return null
  }
  if (day < 1 || day > daysInMonth(year, month)) {
    return null
  }
  return value
}

// Reason: while the year is typed digit by digit, the browser date field
// reports every step as a valid date (0002, 0020, 0202, then 2026); a year
// below 1000 is a year still being typed, never a period with spending.
export function readTypedDate(value: string): string | null {
  const date = readIsoDate(value)
  if (date === null || Number(date.slice(0, 4)) < 1000) {
    return null
  }
  return date
}

export function monthRange(month: string): { from: string; to: string } {
  const [yearText, monthText] = month.split('-')
  const year = Number(yearText)
  const monthNumber = Number(monthText)
  const lastDay = String(daysInMonth(year, monthNumber)).padStart(2, '0')
  return { from: `${month}-01`, to: `${month}-${lastDay}` }
}

export function shiftMonth(month: string, delta: number): string {
  const [yearText, monthText] = month.split('-')
  const year = Number(yearText)
  const monthNumber = Number(monthText)
  const total = year * 12 + (monthNumber - 1) + delta
  const nextYear = Math.floor(total / 12)
  const nextMonth = (total % 12) + 1
  return `${String(nextYear)}-${String(nextMonth).padStart(2, '0')}`
}

export function currentMonth(): string {
  const now = new Date()
  return `${String(now.getFullYear())}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

export function formatMonth(month: string): string {
  const [yearText, monthText] = month.split('-')
  const name = MONTH_NAMES[Number(monthText) - 1]
  return `${name} de ${yearText}`
}

export function readPeriod(searchParams: URLSearchParams): Period {
  const month = readMonth(searchParams.get('month'))
  if (month !== null) {
    return { kind: 'month', month }
  }
  const from = readIsoDate(searchParams.get('from'))
  let to = readIsoDate(searchParams.get('to'))
  if (from !== null && to !== null && to < from) {
    to = null
  }
  if (from !== null || to !== null) {
    return { kind: 'range', from, to }
  }
  return { kind: 'all' }
}

export function toDateBounds(period: Period): { from: string | null; to: string | null } {
  if (period.kind === 'all') {
    return { from: null, to: null }
  }
  if (period.kind === 'month') {
    return monthRange(period.month)
  }
  return { from: period.from, to: period.to }
}

export function writePeriod(params: URLSearchParams, period: Period): void {
  params.delete('page')
  params.delete('month')
  params.delete('from')
  params.delete('to')
  if (period.kind === 'month') {
    params.set('month', period.month)
  } else if (period.kind === 'range') {
    if (period.from !== null) {
      params.set('from', period.from)
    }
    if (period.to !== null) {
      params.set('to', period.to)
    }
  }
}
