import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

import { defineConfig, devices } from '@playwright/test'

// Reason: the config is evaluated again in every worker process, and workers
// inherit the runner's environment; creating the folder only when it is not
// set yet gives the backend and the tests the same database folder.
process.env.DASH_E2E_DIR ??= mkdtempSync(join(tmpdir(), 'dash-e2e-'))

export default defineConfig({
  testDir: 'e2e',
  // Reason: every spec file shares the single real FastAPI backend, the same
  // SQLite database and the same "e2e" user; running spec files in parallel
  // workers races logins and writes against that shared state.
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:5173/app',
  },
  webServer: [
    {
      command: 'bash scripts/e2e-backend.sh',
      url: 'http://127.0.0.1:8000/login',
      reuseExistingServer: false,
      timeout: 60_000,
      ignoreHTTPSErrors: true,
      // Reason: the default stop is SIGKILL, which skips the script's EXIT
      // trap and leaves the database folder behind in the temp directory.
      gracefulShutdown: { signal: 'SIGTERM', timeout: 5_000 },
    },
    {
      command: 'pnpm dev --port 5173 --strictPort',
      url: 'http://127.0.0.1:5173/app/',
      reuseExistingServer: false,
    },
  ],
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
