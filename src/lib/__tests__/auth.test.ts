import { http, HttpResponse } from 'msw'
import { expect, test } from 'vitest'

import { ApiError } from '@/lib/api-client'
import { getMe } from '@/lib/auth'
import { server } from '@/testing/mocks/server'

test('resolves the signed-in user', async () => {
  server.use(http.get('/api/auth/me', () => HttpResponse.json({ login: 'teste' })))

  await expect(getMe()).resolves.toEqual({ login: 'teste' })
})

test('resolves null when nobody is signed in', async () => {
  server.use(
    http.get('/api/auth/me', () =>
      HttpResponse.json({ detail: 'nao autenticado' }, { status: 401 }),
    ),
  )

  await expect(getMe()).resolves.toBeNull()
})

test('rejects with the ApiError when the API fails for another reason', async () => {
  server.use(
    http.get('/api/auth/me', () => HttpResponse.json({ detail: 'falhou' }, { status: 500 })),
  )

  const request = getMe()

  await expect(request).rejects.toBeInstanceOf(ApiError)
  await expect(request).rejects.toMatchObject({ status: 500 })
})
