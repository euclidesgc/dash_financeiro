import { http, HttpResponse } from 'msw'
import { expect, test } from 'vitest'

import { ApiError, apiRequest } from '@/lib/api-client'
import { server } from '@/testing/mocks/server'

test('resolves json on 200', async () => {
  server.use(http.get('/api/things', () => HttpResponse.json({ value: 42 })))

  const result = await apiRequest<{ value: number }>('/api/things')

  expect(result).toEqual({ value: 42 })
})

test('resolves undefined on 204', async () => {
  server.use(http.post('/api/things', () => new HttpResponse(null, { status: 204 })))

  const result = await apiRequest('/api/things', { method: 'POST' })

  expect(result).toBeUndefined()
})

test('throws ApiError with status and detail on 401', async () => {
  server.use(
    http.get('/api/things', () =>
      HttpResponse.json({ detail: 'nao autenticado' }, { status: 401 }),
    ),
  )

  await expect(apiRequest('/api/things')).rejects.toMatchObject(
    new ApiError(401, 'nao autenticado'),
  )
})

test('falls back to statusText when the body is not json', async () => {
  server.use(
    http.get('/api/things', () => new HttpResponse('not json', { status: 500 })),
  )

  const error = await apiRequest('/api/things').catch((caught: unknown) => caught)

  expect(error).toBeInstanceOf(ApiError)
  expect((error as ApiError).status).toBe(500)
  expect((error as ApiError).detail.length).toBeGreaterThan(0)
})

test('sends credentials same-origin', async () => {
  let receivedCredentials: RequestCredentials | undefined
  server.use(
    http.get('/api/things', ({ request }) => {
      receivedCredentials = (request as unknown as { credentials?: RequestCredentials })
        .credentials
      return HttpResponse.json({})
    }),
  )

  await apiRequest('/api/things')

  expect(receivedCredentials).toBe('same-origin')
})
