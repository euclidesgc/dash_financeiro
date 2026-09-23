import { http, HttpResponse } from 'msw'
import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'

import { LoginForm } from '@/features/auth/components/login-form'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import { screen } from '@testing-library/react'

test('shows field errors when submitted empty', async () => {
  const onSuccess = vi.fn()
  let requested = false
  server.use(
    http.post('/api/auth/login', () => {
      requested = true
      return new HttpResponse(null, { status: 204 })
    }),
  )

  renderWithProviders(<LoginForm onSuccess={onSuccess} />)

  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

  expect(await screen.findByText('Informe o login.')).toBeInTheDocument()
  expect(screen.getByText('Informe a senha.')).toBeInTheDocument()
  expect(requested).toBe(false)
  expect(onSuccess).not.toHaveBeenCalled()
})

test('shows the generic message on 401', async () => {
  const onSuccess = vi.fn()

  renderWithProviders(<LoginForm onSuccess={onSuccess} />)

  await userEvent.type(screen.getByLabelText('Login'), 'errado')
  await userEvent.type(screen.getByLabelText('Senha'), 'errada')
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Login ou senha inválidos.')
  expect(onSuccess).not.toHaveBeenCalled()
})

test('shows the throttled message on 429', async () => {
  server.use(
    http.post('/api/auth/login', () =>
      HttpResponse.json({ detail: 'muitas tentativas' }, { status: 429 }),
    ),
  )

  renderWithProviders(<LoginForm onSuccess={vi.fn()} />)

  await userEvent.type(screen.getByLabelText('Login'), 'teste')
  await userEvent.type(screen.getByLabelText('Senha'), 'senha')
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Muitas tentativas seguidas. Tente novamente mais tarde.')
})

test('shows the network message on 500', async () => {
  server.use(
    http.post('/api/auth/login', () => HttpResponse.json({}, { status: 500 })),
  )

  renderWithProviders(<LoginForm onSuccess={vi.fn()} />)

  await userEvent.type(screen.getByLabelText('Login'), 'teste')
  await userEvent.type(screen.getByLabelText('Senha'), 'senha')
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent(
    'Não foi possível entrar. Verifique se o servidor está no ar e tente de novo.',
  )
})

test('disables the button and shows "Entrando…" while submitting', async () => {
  server.use(
    http.post('/api/auth/login', async () => {
      await new Promise((resolve) => setTimeout(resolve, 50))
      return new HttpResponse(null, { status: 204 })
    }),
  )

  renderWithProviders(<LoginForm onSuccess={vi.fn()} />)

  await userEvent.type(screen.getByLabelText('Login'), 'teste')
  await userEvent.type(screen.getByLabelText('Senha'), 'senha')
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

  const button = await screen.findByRole('button', { name: 'Entrando…' })
  expect(button).toBeDisabled()
})

test('calls onSuccess after a valid login', async () => {
  const onSuccess = vi.fn()

  renderWithProviders(<LoginForm onSuccess={onSuccess} />)

  await userEvent.type(screen.getByLabelText('Login'), 'teste')
  await userEvent.type(screen.getByLabelText('Senha'), 'senha')
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

  await vi.waitFor(() => {
    expect(onSuccess).toHaveBeenCalledTimes(1)
  })
})
