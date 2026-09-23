/// <reference types="vitest/config" />
import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  base: '/app/',
  plugins: [react(), tailwindcss()],
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
