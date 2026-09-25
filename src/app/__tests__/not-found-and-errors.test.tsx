import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { expect, test } from 'vitest'

import { router as appRouter, routes } from '@/app/router'
import { queryClient as appQueryClient } from '@/lib/react-query'
import { server } from '@/testing/mocks/server'

function renderApp(entry: string, queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
  const router = createMemoryRouter(routes, {
    basename: appRouter.basename,
    initialEntries: [entry],
  })

  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )

  return router
}

test('opening /app without the trailing slash shows the app', async () => {
  renderApp('/app')

  expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
})

test('an unknown path shows the not found page in Portuguese with a way back', async () => {
  const router = renderApp('/app/nao-existe')

  expect(await screen.findByRole('heading', { name: 'Página não encontrada' })).toBeInTheDocument()
  expect(screen.queryByText(/Unexpected Application Error/)).not.toBeInTheDocument()

  await userEvent.click(screen.getByRole('link', { name: 'Voltar para o início' }))

  expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
  expect(router.state.location.pathname).toBe('/app/login')
})

test('a transient failure of the user query is retried instead of breaking the page', async () => {
  server.use(
    http.get('/api/auth/me', () => HttpResponse.json({ detail: 'falhou' }, { status: 500 }), {
      once: true,
    }),
  )
  const queryClient = new QueryClient({ defaultOptions: appQueryClient.getDefaultOptions() })

  renderApp('/app/', queryClient)

  expect(await screen.findByRole('heading', { name: 'Entrar' }, { timeout: 4000 })).toBeInTheDocument()
})

test('a user query that keeps failing shows a Portuguese error with a retry', async () => {
  server.use(
    http.get('/api/auth/me', () => HttpResponse.json({ detail: 'falhou' }, { status: 500 }), {
      once: true,
    }),
  )

  renderApp('/app/')

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível confirmar a sua sessão.')
  expect(screen.queryByText(/Unexpected Application Error/)).not.toBeInTheDocument()

  await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
})
