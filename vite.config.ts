/// <reference types="vitest/config" />
import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import type { Plugin } from 'vite'

// Reason: the router's home is '/app' (basename without the trailing slash),
// and the dev server's base '/app/' answers '/app' with a hint page instead of
// the SPA, so a reload on the home page would leave the app.
function serveBaseWithoutSlash(): Plugin {
  return {
    name: 'serve-base-without-slash',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url ?? ''
        if (url === '/app' || url.startsWith('/app?')) {
          res.statusCode = 302
          res.setHeader('Location', `/app/${url.slice('/app'.length)}`)
          res.end()
          return
        }
        next()
      })
    },
  }
}

export default defineConfig({
  base: '/app/',
  plugins: [react(), tailwindcss(), serveBaseWithoutSlash()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
  },
  test: {
    environment: './src/testing/jsdom-environment.ts',
    globals: false,
    setupFiles: ['src/testing/setup.ts'],
    exclude: ['e2e/**', 'node_modules/**'],
    coverage: {
      include: ['src/**'],
    },
  },
})
