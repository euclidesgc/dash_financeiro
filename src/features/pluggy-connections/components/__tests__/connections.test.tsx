import { http, HttpResponse } from 'msw'
import { expect, test } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, within } from '@testing-library/react'

import { AddConnectionForm } from '@/features/pluggy-connections/components/add-connection-form'
import { ConnectionsList } from '@/features/pluggy-connections/components/connections-list'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'

const EXISTING = '3f2504e0-4f89-11d3-9a0c-0305e82c3301'
const NEW_ID = '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d'
const FORMAT_MESSAGE = 'Informe um identificador de conexão da Pluggy (formato 8-4-4-4-12).'

function renderScreen(): void {
  renderWithProviders(
    <>
      <AddConnectionForm />
      <ConnectionsList />
    </>,
  )
}

test('shows the loading state and then the registered connection', async () => {
  renderScreen()

  expect(screen.getByRole('status')).toHaveTextContent('Carregando conexões…')
  expect(await screen.findByText(EXISTING)).toBeInTheDocument()
  expect(screen.getByText(/Cadastrada em/)).toBeInTheDocument()
})

test('shows the empty state when nothing is registered', async () => {
  server.use(http.get('/api/pluggy-connections', () => HttpResponse.json({ connections: [] })))

  renderScreen()

  expect(await screen.findByText(/Nenhuma conexão cadastrada\./)).toBeInTheDocument()
})

test('a failed load offers a retry that recovers', async () => {
  const user = userEvent.setup()
  let calls = 0
  server.use(
    http.get('/api/pluggy-connections', () => {
      calls += 1
      if (calls === 1) return HttpResponse.json({ detail: 'erro' }, { status: 500 })
      return HttpResponse.json({ connections: [] })
    }),
  )

  renderScreen()

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar as conexões.')
  await user.click(within(alert).getByRole('button', { name: 'Tentar de novo' }))
  expect(await screen.findByText(/Nenhuma conexão cadastrada\./)).toBeInTheDocument()
})

test('an id outside the format is refused without calling the API', async () => {
  const user = userEvent.setup()
  let posts = 0
  server.use(
    http.post('/api/pluggy-connections', () => {
      posts += 1
      return HttpResponse.json({}, { status: 201 })
    }),
  )
  renderScreen()

  await user.type(screen.getByLabelText('Identificador da conexão'), 'abc')
  await user.click(screen.getByRole('button', { name: 'Cadastrar conexão' }))

  expect(await screen.findByText(FORMAT_MESSAGE)).toBeInTheDocument()
  expect(screen.getByLabelText('Identificador da conexão')).toHaveAttribute('aria-invalid', 'true')
  expect(posts).toBe(0)
})

test('a valid id is registered, listed and the field is cleared', async () => {
  const user = userEvent.setup()
  renderScreen()
  await screen.findByText(EXISTING)

  const field = screen.getByLabelText('Identificador da conexão')
  await user.type(field, ` ${NEW_ID.toUpperCase()} `)
  await user.click(screen.getByRole('button', { name: 'Cadastrar conexão' }))

  expect(await screen.findByText(NEW_ID)).toBeInTheDocument()
  expect(field).toHaveValue('')
})

test('a duplicate shows the API message on the field', async () => {
  const user = userEvent.setup()
  renderScreen()
  await screen.findByText(EXISTING)

  await user.type(screen.getByLabelText('Identificador da conexão'), EXISTING)
  await user.click(screen.getByRole('button', { name: 'Cadastrar conexão' }))

  expect(await screen.findByText('Essa conexão já está cadastrada.')).toBeInTheDocument()
})

test('removing asks for confirmation; cancel keeps it and confirm removes it', async () => {
  const user = userEvent.setup()
  renderScreen()
  await screen.findByText(EXISTING)

  const remove = screen.getByRole('button', { name: `Remover a conexão ${EXISTING}` })
  await user.click(remove)
  await user.click(screen.getByRole('button', { name: 'Cancelar' }))
  expect(screen.getByText(EXISTING)).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: `Remover a conexão ${EXISTING}` }))
  expect(screen.getByText(/Remover a conexão 3f2504e0…\?/)).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Confirmar' }))

  expect(await screen.findByText(/Nenhuma conexão cadastrada\./)).toBeInTheDocument()
})

test('a failed removal shows an error and keeps the connection', async () => {
  const user = userEvent.setup()
  server.use(
    http.delete('/api/pluggy-connections/:itemId', () =>
      HttpResponse.json({ detail: 'erro' }, { status: 500 }),
    ),
  )
  renderScreen()
  await screen.findByText(EXISTING)

  await user.click(screen.getByRole('button', { name: `Remover a conexão ${EXISTING}` }))
  await user.click(screen.getByRole('button', { name: 'Confirmar' }))

  expect(await screen.findByText('Não foi possível remover a conexão. Tente de novo.')).toBeInTheDocument()
  expect(screen.getByText(EXISTING)).toBeInTheDocument()
})
