import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
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

test('redirects to the login page without a session', async () => {
  renderRouter(['/expenses'])

  expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
})

test('navigates from the balances page to the expenses page', async () => {
  renderRouter(['/login'])

  await screen.findByRole('heading', { name: 'Entrar' })
  await login()

  await screen.findByRole('heading', { name: 'Saldos de hoje' })

  await userEvent.click(screen.getByRole('link', { name: 'Gastos' }))

  expect(await screen.findByRole('heading', { name: 'Gastos' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Gastos' })).toHaveAttribute('aria-current', 'page')
  expect(await screen.findByText('MERCADO DO BAIRRO')).toBeInTheDocument()
  expect(document.title).toBe('Gastos · dash_financeiro')
})

test('navigates back to the balances page', async () => {
  renderRouter(['/login'])

  await screen.findByRole('heading', { name: 'Entrar' })
  await login()

  await screen.findByRole('heading', { name: 'Saldos de hoje' })
  await userEvent.click(screen.getByRole('link', { name: 'Gastos' }))
  await screen.findByRole('heading', { name: 'Gastos' })

  await userEvent.click(screen.getByRole('link', { name: 'Saldos' }))

  expect(await screen.findByRole('heading', { name: 'Saldos de hoje' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Saldos' })).toHaveAttribute('aria-current', 'page')
})
