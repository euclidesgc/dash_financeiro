export type SyncTrigger = 'screen' | 'command'

export type SyncOrigin = 'pluggy' | 'file'

export interface SyncRun {
  finished_at: string | null
  status: 'ok' | 'failed'
  reason: string | null
  triggered_by: SyncTrigger | null
  origin: SyncOrigin | null
  new_transactions: number | null
}

export interface SyncStatus {
  running: boolean
  last_run: SyncRun | null
}
