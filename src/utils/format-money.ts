const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })

export function formatMoney(cents: number): string {
  return moneyFormatter.format(cents / 100)
}
