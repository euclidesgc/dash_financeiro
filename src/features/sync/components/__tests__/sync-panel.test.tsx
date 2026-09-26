import { http, HttpResponse, delay } from 'msw'
import { expect, test } from 'vitest'
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

test('shows "Nenhuma atualização feita por este painel ainda" when there is no last run', async () => {
  server.use(
    http.get('/api/sync/status', () => HttpResponse.json({ running: false, last_run: null })),
  )

  renderWithProviders(<SyncPanel />)

  expect(await screen.findByText('Nenhuma atualização feita por este painel ainda')).toBeInTheDocument()
  expect(screen.queryByText('Terminou sem erro')).not.toBeInTheDocument()
  expect(screen.queryByText('Falhou')).not.toBeInTheDocument()
})

test('shows the date and the "Terminou sem erro" badge', async () => {
  renderWithProviders(<SyncPanel />)

  expect(await screen.findByText(/Última atualização: 22\/09\/2026/)).toBeInTheDocument()
  expect(screen.getByText('Terminou sem erro')).toBeInTheDocument()
})

test('says the last update was made by a terminal command', async () => {
  renderWithProviders(<SyncPanel />)

  expect(await screen.findByText('Feita por comando no terminal')).toBeInTheDocument()
  expect(screen.queryByText('Você pediu pelo botão “Atualizar agora”')).not.toBeInTheDocument()
})

test('says the last update was asked for on the screen', async () => {
  server.use(
    http.get('/api/sync/status', () =>
      HttpResponse.json({
        running: false,
        last_run: { ...fakeSyncStatus.last_run, triggered_by: 'screen' },
      }),
    ),
  )

  renderWithProviders(<SyncPanel />)

  expect(await screen.findByText('Você pediu pelo botão “Atualizar agora”')).toBeInTheDocument()
  expect(screen.queryByText('Feita por comando no terminal')).not.toBeInTheDocument()
})

test('shows origin and count after successful run', async () => {
  renderWithProviders(<SyncPanel />)

  expect(await screen.findByText('Buscou na Pluggy · 25 lançamentos novos')).toBeInTheDocument()
})

test('shows only origin after failed run', async () => {
  server.use(
    http.get('/api/sync/status', () =>
      HttpResponse.json({
        running: false,
        last_run: {
          finished_at: '2026-09-22T11:15:00+00:00',
          status: 'failed',
          reason: 'a Pluggy não respondeu; verifique a conexão com a internet e tente de novo.',
          triggered_by: 'screen',
          origin: 'pluggy',
          new_transactions: null,
        },
      }),
    ),
  )

  renderWithProviders(<SyncPanel />)

  expect(await screen.findByText('Buscou na Pluggy')).toBeInTheDocument()
  expect(screen.queryByText(/lançamentos? novos?/)).not.toBeInTheDocument()
})

test('hides origin line when origin is null', async () => {
  server.use(
    http.get('/api/sync/status', () =>
      HttpResponse.json({
        running: false,
        last_run: { ...fakeSyncStatus.last_run, origin: null, new_transactions: null },
      }),
    ),
  )

  renderWithProviders(<SyncPanel />)

  await screen.findByText(/Última atualização: 22\/09\/2026/)
  expect(screen.queryByText(/Buscou na Pluggy/)).not.toBeInTheDocument()
  expect(screen.queryByText(/Releu o arquivo local/)).not.toBeInTheDocument()
})

test('shows command trigger as terminal command', async () => {
  renderWithProviders(<SyncPanel />)

  expect(await screen.findByText('Feita por comando no terminal')).toBeInTheDocument()
  expect(screen.queryByText('Feita pela rotina diária')).not.toBeInTheDocument()
})

test('origin line sits between last update and trigger', async () => {
  renderWithProviders(<SyncPanel />)

  const lastUpdate = await screen.findByText(/Última atualização: 22\/09\/2026/)
  const origin = screen.getByText('Buscou na Pluggy · 25 lançamentos novos')
  const trigger = screen.getByText('Feita por comando no terminal')

  expect(
    lastUpdate.compareDocumentPosition(origin) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy()
  expect(
    origin.compareDocumentPosition(trigger) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy()
})

test('says nothing about the origin of a run recorded without one', async () => {
  server.use(
    http.get('/api/sync/status', () =>
      HttpResponse.json({
        running: false,
        last_run: { ...fakeSyncStatus.last_run, triggered_by: null },
      }),
    ),
  )

  renderWithProviders(<SyncPanel />)

  await screen.findByText(/Última atualização: 22\/09\/2026/)
  expect(screen.queryByText('Você pediu pelo botão “Atualizar agora”')).not.toBeInTheDocument()
  expect(screen.queryByText('Feita por comando no terminal')).not.toBeInTheDocument()
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
          triggered_by: 'screen',
          origin: 'pluggy',
          new_transactions: null,
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

test('retries the sync when the failed run alert button is clicked', async () => {
  server.use(
    http.get('/api/sync/status', () =>
      HttpResponse.json({
        running: false,
        last_run: {
          finished_at: '2026-09-22T11:15:00+00:00',
          status: 'failed',
          reason: 'a Pluggy não respondeu; verifique a conexão com a internet e tente de novo.',
          triggered_by: 'screen',
          origin: 'pluggy',
          new_transactions: null,
        },
      }),
    ),
    http.post('/api/sync/run', () => HttpResponse.json(fakeSyncStatus)),
  )

  renderWithProviders(<SyncPanel />)

  await screen.findByText('Falhou')
  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  await screen.findByText('Terminou sem erro')
  expect(screen.queryByText('Falhou')).not.toBeInTheDocument()
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

test('disables the button with "Atualizando…" while running and marks the balances stale', async () => {
  server.use(
    http.post('/api/sync/run', async () => {
      await delay(50)
      return HttpResponse.json(fakeSyncStatus)
    }),
  )

  const { queryClient } = renderWithProviders(<SyncPanel />)
  queryClient.setQueryData(['accounts', 'balances'], [])

  await screen.findByText(/Última atualização: 22\/09\/2026/)

  await userEvent.click(screen.getByRole('button', { name: 'Atualizar agora' }))

  expect(screen.getByRole('button', { name: 'Atualizando…' })).toBeDisabled()
  expect(
    screen.getByText('Atualização em andamento. Isso pode levar alguns minutos.'),
  ).toBeInTheDocument()

  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Atualizar agora' })).toBeInTheDocument(),
  )
  expect(queryClient.getQueryState(['accounts', 'balances'])?.isInvalidated).toBe(true)
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
