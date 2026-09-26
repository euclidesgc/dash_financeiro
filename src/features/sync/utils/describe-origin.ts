import type { SyncOrigin } from '@/features/sync/types/sync-status'

const ORIGIN_LABELS: Record<SyncOrigin, string> = {
  pluggy: 'Buscou na Pluggy',
  file: 'Releu o arquivo local',
}

function describeNewTransactions(newTransactions: number): string {
  if (newTransactions === 0) {
    return 'nenhum lançamento novo'
  }
  if (newTransactions === 1) {
    return '1 lançamento novo'
  }
  return `${newTransactions.toString()} lançamentos novos`
}

export function describeOrigin(
  origin: SyncOrigin | null,
  newTransactions: number | null,
): string | null {
  if (origin === null) {
    return null
  }
  const prefix = ORIGIN_LABELS[origin]
  if (newTransactions === null) {
    return prefix
  }
  return `${prefix} · ${describeNewTransactions(newTransactions)}`
}
