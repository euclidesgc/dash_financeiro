export function toCents(value: string): number | null {
  if (value.trim() === '') return null
  return Math.round(Number(value.replace(',', '.')) * 100)
}

export function fromCents(cents: number | null): string {
  if (cents === null) return ''
  return (cents / 100).toFixed(2)
}
