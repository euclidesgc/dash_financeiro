import { execFileSync } from 'node:child_process'
import { join } from 'node:path'

export function restoreSeededBase(): void {
  const folder = process.env.DASH_E2E_DIR
  if (!folder) {
    throw new Error('DASH_E2E_DIR is not set; playwright.config.ts creates it')
  }
  execFileSync(
    'uv',
    ['run', 'python', '-m', 'tests.e2e_restore', join(folder, 'seed.sqlite'), join(folder, 'dash.sqlite')]
  )
}
