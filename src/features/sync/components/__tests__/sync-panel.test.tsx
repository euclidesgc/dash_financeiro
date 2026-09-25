import { http, HttpResponse, delay } from 'msw'
import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor } from '@testing-library/react'

import { SyncPanel } from '@/features/sync/components/sync-panel'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import { fakeSyncStatus } from '@/testing/mocks/handlers'

test('shows the loading state', () => {
  renderWithProviders(<SyncPanel />)

  expect(screen.getByRole('status')).toHaveTextContent('Carregando situação da atualização…')
})

test('shows "Nunca atualizado" when there is no last run', async () => {
  server.use(
    http.get('/api/sync/status', () => HttpResponse.json({ running: false, last_run: null })),
  )

  renderWithProviders(<SyncPanel />)

  expect(await screen.findByText('Nunca atualizado')).toBeInTheDocument()
  expect(screen.queryByText('Concluída')).not.toBeInTheDocument()
  expect(screen.queryByText('Falhou')).not.toBeInTheDocument()
})

test('shows the date and the "Concluída" badge', async () => {
  renderWithProviders(<SyncPanel />)

  expect(await screen.findByText(/Última atualização: 22\/09\/2026/)).toBeInTheDocument()
  expect(screen.getByText('Concluída')).toBeInTheDocument()
})

test('shows "Falhou" with the reason and a retry button', async () => {
  server.use(
    http.get('/api/sync/status', () =>
      HttpResponse.json({
        running: false,
        last_run: {
          finished_at: '2026-09-22T11:15:00+00:00',
          status: 'failed',
          reason: 'a Pluggy não respondeu; verifique a conexão com a internet e tente de novo.',
        },
      }),
    ),
  )

  renderWithProviders(<SyncPanel />)

  expect(await screen.findByText('Falhou')).toBeInTheDocument()
  const alert = screen.getByRole('alert')
  expect(alert).toHaveTextContent(
    'A última atualização falhou: a Pluggy não respondeu; verifique a conexão com a internet e tente de novo.',
  )
  expect(screen.getByRole('button', { name: 'Tentar de novo' })).toBeInTheDocument()
})

test('shows the status error and retries', async () => {
  let attempt = 0
  server.use(
    http.get('/api/sync/status', () => {
      attempt += 1
      if (attempt === 1) {
        return HttpResponse.json({}, { status: 500 })
      }
      return HttpResponse.json(fakeSyncStatus)
    }),
  )

  renderWithProviders(<SyncPanel />)

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar a situação da atualização.')

  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  expect(await screen.findByText(/Última atualização: 22\/09\/2026/)).toBeInTheDocument()
})

test('disables the button with "Atualizando…" while running and invalidates the balances', async () => {
  server.use(
    http.post('/api/sync/run', async () => {
      await delay(50)
      return HttpResponse.json(fakeSyncStatus)
    }),
  )

  const { queryClient } = renderWithProviders(<SyncPanel />)
  const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

  await screen.findByText(/Última atualização: 22\/09\/2026/)

  await userEvent.click(screen.getByRole('button', { name: 'Atualizar agora' }))

  expect(screen.getByRole('button', { name: 'Atualizando…' })).toBeDisabled()
  expect(
    screen.getByText('Atualização em andamento. Isso pode levar alguns minutos.'),
  ).toBeInTheDocument()

  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Atualizar agora' })).toBeInTheDocument(),
  )
  expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['accounts', 'balances'] })
})

test('shows the server detail on 409', async () => {
  server.use(
    http.post('/api/sync/run', () =>
      HttpResponse.json({ detail: 'Já existe uma atualização em andamento.' }, { status: 409 }),
    ),
  )

  renderWithProviders(<SyncPanel />)

  await screen.findByText(/Última atualização: 22\/09\/2026/)
  await userEvent.click(screen.getByRole('button', { name: 'Atualizar agora' }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Já existe uma atualização em andamento.')
  expect(screen.getByRole('button', { name: 'Tentar de novo' })).toBeInTheDocument()
})

test('shows the server detail on 503', async () => {
  server.use(
    http.post('/api/sync/run', () =>
      HttpResponse.json(
        { detail: 'Sem credencial cadastrada para sincronizar com a Pluggy.' },
        { status: 503 },
      ),
    ),
  )

  renderWithProviders(<SyncPanel />)

  await screen.findByText(/Última atualização: 22\/09\/2026/)
  await userEvent.click(screen.getByRole('button', { name: 'Atualizar agora' }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Sem credencial cadastrada para sincronizar com a Pluggy.')
})

test('shows the generic message on 500', async () => {
  server.use(http.post('/api/sync/run', () => HttpResponse.json({}, { status: 500 })))

  renderWithProviders(<SyncPanel />)

  await screen.findByText(/Última atualização: 22\/09\/2026/)
  await userEvent.click(screen.getByRole('button', { name: 'Atualizar agora' }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent(
    'Não foi possível atualizar. Verifique se o servidor está no ar e tente de novo.',
  )
})

test('disables the button when the server says running', async () => {
  server.use(
    http.get('/api/sync/status', () =>
      HttpResponse.json({ running: true, last_run: fakeSyncStatus.last_run }),
    ),
  )

  renderWithProviders(<SyncPanel />)

  expect(await screen.findByRole('button', { name: 'Atualizando…' })).toBeDisabled()
  expect(screen.getByText('Em andamento')).toBeInTheDocument()
})
