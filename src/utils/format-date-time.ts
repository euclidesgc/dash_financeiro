const dateTimeFormatter = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' })

export function formatDateTime(iso: string | null): string | null {
  if (iso === null || Number.isNaN(Date.parse(iso))) {
    return null
  }
  return dateTimeFormatter.format(new Date(iso))
}
