const dateOnlyPattern = /^(\d{4})-(\d{2})-(\d{2})$/

export function formatDate(iso: string): string {
  // O construtor nativo de datas interpreta 'YYYY-MM-DD' em UTC e vira o dia
  // anterior em fusos negativos; a data é montada por regex, sem depender dele.
  const match = dateOnlyPattern.exec(iso)
  if (!match) {
    return iso
  }
  const [, year, month, day] = match
  return `${day}/${month}/${year}`
}
