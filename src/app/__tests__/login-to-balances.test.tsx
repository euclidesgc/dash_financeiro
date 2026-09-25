import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { expect, test } from 'vitest'

import { routes } from '@/app/router'

function renderRouter(initialEntries: string[]) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const router = createMemoryRouter(routes, { initialEntries })

  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )

  return { router }
}

async function login() {
  await userEvent.type(screen.getByLabelText('Login'), 'teste')
  await userEvent.type(screen.getByLabelText('Senha'), 'senha')
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
}

test('redirects to /login without a session', async () => {
  renderRouter(['/'])

  expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
})

test('a valid login lands on the balances page', async () => {
  renderRouter(['/login'])

  await screen.findByRole('heading', { name: 'Entrar' })
  await login()

  expect(await screen.findByRole('heading', { name: 'Saldos de hoje' })).toBeInTheDocument()
  expect(await screen.findByText('Conta corrente')).toBeInTheDocument()
  expect(await screen.findByText(/Última atualização/)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Atualizar agora' })).toBeInTheDocument()
})

test('signing out returns to the login page', async () => {
  renderRouter(['/login'])

  await screen.findByRole('heading', { name: 'Entrar' })
  await login()

  await screen.findByRole('heading', { name: 'Saldos de hoje' })
  await userEvent.click(screen.getByRole('button', { name: 'Sair' }))

  expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
})

test('an authenticated user opening /login is sent to the dashboard', async () => {
  const { router } = renderRouter(['/login'])

  await screen.findByRole('heading', { name: 'Entrar' })
  await login()
  await screen.findByRole('heading', { name: 'Saldos de hoje' })

  await act(async () => {
    await router.navigate('/login')
  })

  expect(await screen.findByRole('heading', { name: 'Saldos de hoje' })).toBeInTheDocument()
})
