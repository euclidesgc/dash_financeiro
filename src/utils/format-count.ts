export interface CountNoun {
  one: string
  many: string
}

export const EXPENSE_NOUN: CountNoun = { one: 'gasto', many: 'gastos' }

// Intl.PluralRules('pt-BR') puts 0 in the singular ("0 gasto"); the screens write "0 gastos".
export function formatCount(count: number, noun: CountNoun): string {
  return `${String(count)} ${count === 1 ? noun.one : noun.many}`
}
