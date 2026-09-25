export type SyncTrigger = 'screen' | 'command'

export interface SyncRun {
  finished_at: string | null
  status: 'ok' | 'failed'
  reason: string | null
  triggered_by: SyncTrigger | null
}

export interface SyncStatus {
  running: boolean
  last_run: SyncRun | null
}
