export type MoneyTextRejection = 'empty' | 'format' | 'decimals' | 'not-positive'

export type MoneyTextResult =
  | { ok: true; cents: number }
  | { ok: false; reason: MoneyTextRejection }

const PLAIN_INTEGER = /^\d+$/
const GROUPED_INTEGER = /^\d{1,3}(\.\d{3})+$/
const DOT_DECIMAL = /^(\d+)\.(\d+)$/

function toResult(integerText: string, decimalText: string, negative: boolean): MoneyTextResult {
  if (decimalText.length > 2) return { ok: false, reason: 'decimals' }
  const cents =
    Number(integerText.replaceAll('.', '')) * 100 + Number(decimalText.padEnd(2, '0'))
  if (negative || cents === 0) return { ok: false, reason: 'not-positive' }
  return { ok: true, cents }
}

function isInteger(text: string): boolean {
  return PLAIN_INTEGER.test(text) || GROUPED_INTEGER.test(text)
}

export function parseMoneyText(text: string): MoneyTextResult {
  const trimmed = text.trim()
  if (trimmed === '') return { ok: false, reason: 'empty' }

  const negative = trimmed.startsWith('-')
  const unsigned = trimmed.replace(/^-/, '').replace(/^R\$\s*/, '').trim()

  const commaParts = unsigned.split(',')
  if (commaParts.length === 2) {
    const [integerText = '', decimalText = ''] = commaParts
    if (!isInteger(integerText) || !PLAIN_INTEGER.test(decimalText)) {
      return { ok: false, reason: 'format' }
    }
    return toResult(integerText, decimalText, negative)
  }
  if (commaParts.length > 2) return { ok: false, reason: 'format' }

  if (isInteger(unsigned)) return toResult(unsigned, '', negative)

  const dotDecimal = DOT_DECIMAL.exec(unsigned)
  if (dotDecimal !== null) return toResult(dotDecimal[1], dotDecimal[2], negative)

  return { ok: false, reason: 'format' }
}

const inputFormatter = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function formatMoneyInput(cents: number | null): string {
  if (cents === null) return ''
  return inputFormatter.format(cents / 100)
}
