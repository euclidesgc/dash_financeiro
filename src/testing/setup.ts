import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'

import {
  resetAdvisor,
  resetCategories,
  resetConnections,
  resetExpenses,
  resetPlan,
  resetSession,
} from '@/testing/mocks/handlers'
import { server } from '@/testing/mocks/server'

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' })
})
afterEach(() => {
  cleanup()
  server.resetHandlers()
  resetSession()
  resetExpenses()
  resetCategories()
  resetPlan()
  resetConnections()
  resetAdvisor()
})
afterAll(() => {
  server.close()
})
