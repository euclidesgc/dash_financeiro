export interface SyncRun {
  finished_at: string | null
  status: 'ok' | 'failed'
  reason: string | null
}

export interface SyncStatus {
  running: boolean
  last_run: SyncRun | null
}
