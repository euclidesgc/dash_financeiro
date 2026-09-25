import { http, HttpResponse } from 'msw'
import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor } from '@testing-library/react'

import { SimilarOffer } from '@/features/expenses/components/similar-offer'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'

interface ApplyCall {
  id: string
  body: { category: string | null }
}

function countIs(n: number): void {
  server.use(
    http.get('/api/transactions/:id/similar', () => HttpResponse.json({ count: n })),
  )
}

function spyOnApply(): ApplyCall[] {
  const calls: ApplyCall[] = []
  server.use(
    http.post('/api/transactions/:id/category/apply-to-similar', async ({ params, request }) => {
      calls.push({ id: params.id as string, body: (await request.json()) as { category: string | null } })
      return HttpResponse.json({ updated: 3 })
    }),
  )
  return calls
}

function spyOnPendingApply(): { calls: ApplyCall[]; release: () => void } {
  const calls: ApplyCall[] = []
  let resolvePromise: () => void = () => {
    /* replaced below */
  }
  const promise = new Promise<void>((resolve) => {
    resolvePromise = resolve
  })
  server.use(
    http.post('/api/transactions/:id/category/apply-to-similar', async ({ params, request }) => {
      calls.push({ id: params.id as string, body: (await request.json()) as { category: string | null } })
      await promise
      return HttpResponse.json({ updated: 3 })
    }),
  )
  return { calls, release: resolvePromise }
}

function renderOffer(onDismiss = vi.fn()) {
  return {
    onDismiss,
    ...renderWithProviders(
      <SimilarOffer expenseId={44} category="Groceries" onDismiss={onDismiss} />,
    ),
  }
}

test('renders nothing when the count is zero', async () => {
  let calls = 0
  server.use(
    http.get('/api/transactions/:id/similar', () => {
      calls += 1
      return HttpResponse.json({ count: 0 })
    }),
  )

  const { container } = renderOffer()

  await waitFor(() => {
    expect(calls).toBeGreaterThan(0)
  })
  expect(container).toBeEmptyDOMElement()
  expect(screen.queryByRole('button')).not.toBeInTheDocument()
})

test('renders nothing while the count loads', () => {
  let resolvePromise: () => void = () => {
    /* replaced below */
  }
  const promise = new Promise<void>((resolve) => {
    resolvePromise = resolve
  })
  server.use(
    http.get('/api/transactions/:id/similar', async () => {
      await promise
      return HttpResponse.json({ count: 3 })
    }),
  )

  const { container } = renderOffer()

  expect(container).toBeEmptyDOMElement()
  resolvePromise()
})

test('shows the offer with the plural text and the two buttons', async () => {
  countIs(3)

  renderOffer()

  await screen.findByText('Aplicar a 3 gastos parecidos')
  expect(screen.getByRole('button', { name: 'Aplicar' })).toHaveAttribute('type', 'button')
  expect(screen.getByRole('button', { name: 'Agora não' })).toHaveAttribute('type', 'button')
})

test('uses the singular text for one similar expense', async () => {
  countIs(1)

  renderOffer()

  await screen.findByText('Aplicar a 1 gasto parecido')
})

test('"Agora não" calls onDismiss without calling the API', async () => {
  const user = userEvent.setup()
  countIs(3)
  const calls = spyOnApply()
  const onDismiss = vi.fn()

  renderOffer(onDismiss)

  await screen.findByText('Aplicar a 3 gastos parecidos')
  await user.click(screen.getByRole('button', { name: 'Agora não' }))

  expect(onDismiss).toHaveBeenCalledTimes(1)
  expect(calls.length).toBe(0)
})

test('"Aplicar" sends POST with the category, shows "Aplicando…" and then the confirmation', async () => {
  const user = userEvent.setup()
  countIs(3)
  const { calls, release } = spyOnPendingApply()

  renderOffer()

  await screen.findByText('Aplicar a 3 gastos parecidos')
  await user.click(screen.getByRole('button', { name: 'Aplicar' }))

  expect(calls[0]).toEqual({ id: '44', body: { category: 'Groceries' } })
  const applyingButton = screen.getByRole('button', { name: 'Aplicando…' })
  expect(applyingButton).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Agora não' })).toBeDisabled()
  expect(screen.getByRole('status')).toHaveTextContent('Aplicando…')

  release()

  await waitFor(() => {
    expect(screen.getByRole('status')).toHaveTextContent('Categoria aplicada a 3 gastos')
  })
  expect(screen.queryByRole('button', { name: 'Aplicar' })).not.toBeInTheDocument()
})

test('uses the singular text in the confirmation', async () => {
  const user = userEvent.setup()
  countIs(3)
  server.use(
    http.post('/api/transactions/:id/category/apply-to-similar', () =>
      HttpResponse.json({ updated: 1 }),
    ),
  )

  renderOffer()

  await screen.findByText('Aplicar a 3 gastos parecidos')
  await user.click(screen.getByRole('button', { name: 'Aplicar' }))

  await screen.findByRole('status')
  expect(screen.getByRole('status')).toHaveTextContent('Categoria aplicada a 1 gasto')
})

test('sends category null for "Sem categoria"', async () => {
  const user = userEvent.setup()
  countIs(3)
  const calls = spyOnApply()

  renderWithProviders(<SimilarOffer expenseId={44} category={null} onDismiss={vi.fn()} />)

  await screen.findByText('Aplicar a 3 gastos parecidos')
  await user.click(screen.getByRole('button', { name: 'Aplicar' }))

  await waitFor(() => {
    expect(calls[0]?.body).toEqual({ category: null })
  })
})

test('a 500 on apply shows the alert and "Tentar de novo" repeats the call', async () => {
  const user = userEvent.setup()
  countIs(3)
  const calls: ApplyCall[] = []
  let first = true
  server.use(
    http.post('/api/transactions/:id/category/apply-to-similar', async ({ params, request }) => {
      const body = (await request.json()) as { category: string | null }
      calls.push({ id: params.id as string, body })
      if (first) {
        first = false
        return HttpResponse.json({ detail: 'erro' }, { status: 500 })
      }
      return HttpResponse.json({ updated: 3 })
    }),
  )

  renderOffer()

  await screen.findByText('Aplicar a 3 gastos parecidos')
  await user.click(screen.getByRole('button', { name: 'Aplicar' }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível aplicar a categoria aos gastos parecidos.')
  expect(screen.getByRole('button', { name: 'Agora não' })).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  await waitFor(() => {
    expect(calls.length).toBe(2)
  })
  expect(calls[1]?.body).toEqual(calls[0]?.body)

  await waitFor(() => {
    expect(screen.getByRole('status')).toHaveTextContent('Categoria aplicada a 3 gastos')
  })
})

test('an error on the count shows the alert and "Tentar de novo" refetches', async () => {
  const user = userEvent.setup()
  let first = true
  server.use(
    http.get('/api/transactions/:id/similar', () => {
      if (first) {
        first = false
        return HttpResponse.json({ detail: 'erro' }, { status: 500 })
      }
      return HttpResponse.json({ count: 2 })
    }),
  )

  renderOffer()

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível contar os gastos parecidos.')

  await user.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  await screen.findByText('Aplicar a 2 gastos parecidos')
})

test('success invalidates the expenses and the categories queries', async () => {
  const user = userEvent.setup()
  countIs(3)
  spyOnApply()

  const { queryClient } = renderOffer()
  const spy = vi.spyOn(queryClient, 'invalidateQueries')

  await screen.findByText('Aplicar a 3 gastos parecidos')
  await user.click(screen.getByRole('button', { name: 'Aplicar' }))

  await waitFor(() => {
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['expenses'] }))
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['categories'] }))
  })
})

test('a double click on "Aplicar" sends one call', async () => {
  const user = userEvent.setup()
  countIs(3)
  const { calls, release } = spyOnPendingApply()

  renderOffer()

  await screen.findByText('Aplicar a 3 gastos parecidos')
  await user.dblClick(screen.getByRole('button', { name: 'Aplicar' }))

  expect(calls.length).toBe(1)
  release()
})
