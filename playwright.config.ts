import { defineConfig, devices } from '@playwright/test'

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
    },
    {
      command: 'pnpm dev --port 5173 --strictPort',
      url: 'http://127.0.0.1:5173/app/',
      reuseExistingServer: false,
    },
  ],
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
