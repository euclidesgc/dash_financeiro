import { http, HttpResponse } from 'msw'
import { expect, test } from 'vitest'

import { apiRequest } from '@/lib/api-client'
import { meQueryOptions } from '@/lib/auth'
import { createQueryClient } from '@/lib/react-query'
import { server } from '@/testing/mocks/server'

const unauthorized = () => HttpResponse.json({ detail: 'nao autenticado' }, { status: 401 })

async function signedInClient() {
  let meRequests = 0
  server.use(
    http.get('/api/auth/me', () => {
      meRequests += 1
      return meRequests === 1 ? HttpResponse.json({ login: 'teste' }) : unauthorized()
    }),
  )
  const client = createQueryClient()
  await client.query(meQueryOptions)
  return { client, meRequests: () => meRequests }
}

async function waitForMe(client: ReturnType<typeof createQueryClient>, expected: unknown) {
  await expect
    .poll(() => client.getQueryData(meQueryOptions.queryKey), { timeout: 2_000 })
    .toEqual(expected)
}

test('a 401 from any query clears the signed-in user', async () => {
  const { client } = await signedInClient()
  server.use(http.get('/api/accounts/balances', unauthorized))

  await client
    .query({
      queryKey: ['accounts', 'balances'],
      queryFn: () => apiRequest('/api/accounts/balances'),
    })
    .catch(() => undefined)

  await waitForMe(client, null)
})

test('a 401 from any mutation clears the signed-in user', async () => {
  const { client } = await signedInClient()
  server.use(http.post('/api/sync/run', unauthorized))

  await client
    .getMutationCache()
    .build(client, { mutationFn: () => apiRequest('/api/sync/run', { method: 'POST' }) })
    .execute(undefined)
    .catch(() => undefined)

  await waitForMe(client, null)
})

test('an error that is not a 401 keeps the signed-in user', async () => {
  const { client, meRequests } = await signedInClient()
  server.use(
    http.get('/api/accounts/balances', () =>
      HttpResponse.json({ detail: 'falhou' }, { status: 500 }),
    ),
  )

  await client
    .query({
      queryKey: ['accounts', 'balances'],
      queryFn: () => apiRequest('/api/accounts/balances'),
      retry: false,
    })
    .catch(() => undefined)

  expect(client.getQueryData(meQueryOptions.queryKey)).toEqual({ login: 'teste' })
  expect(meRequests()).toBe(1)
})

test('a 401 with nobody signed in does not ask for the user again', async () => {
  let meRequests = 0
  server.use(
    http.get('/api/auth/me', () => {
      meRequests += 1
      return unauthorized()
    }),
    http.post('/api/auth/login', () =>
      HttpResponse.json({ detail: 'Login ou senha inválidos.' }, { status: 401 }),
    ),
  )
  const client = createQueryClient()
  await client.query(meQueryOptions)

  await client
    .getMutationCache()
    .build(client, { mutationFn: () => apiRequest('/api/auth/login', { method: 'POST' }) })
    .execute(undefined)
    .catch(() => undefined)

  expect(meRequests).toBe(1)
})
