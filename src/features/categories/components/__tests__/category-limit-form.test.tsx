import { http, HttpResponse } from 'msw'
import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { fireEvent, screen, waitFor } from '@testing-library/react'

import { CategoryLimitForm } from '@/features/categories/components/category-limit-form'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import type { Category } from '@/types/category'

const shopping: Category = {
  key: 'Shopping',
  label: 'Compras',
  is_system: true,
  usage_count: 40,
  monthly_limit_cents: 150000,
}

interface PutCall {
  key: string
  body: { monthly_limit_cents: number | null }
}

function spyOnPut(): PutCall[] {
  const calls: PutCall[] = []
  server.use(
    http.put('/api/categories/:key/limit', async ({ params, request }) => {
      const body = (await request.json()) as { monthly_limit_cents: number | null }
      calls.push({ key: params.key as string, body })
      return HttpResponse.json({ ...shopping, monthly_limit_cents: body.monthly_limit_cents })
    }),
  )
  return calls
}

function spyOnPendingPut(): { calls: PutCall[]; release: () => void } {
  const calls: PutCall[] = []
  let resolvePromise: () => void = () => {
    /* replaced below */
  }
  const promise = new Promise<void>((resolve) => {
    resolvePromise = resolve
  })
  server.use(
    http.put('/api/categories/:key/limit', async ({ params, request }) => {
      const body = (await request.json()) as { monthly_limit_cents: number | null }
      calls.push({ key: params.key as string, body })
      await promise
      return HttpResponse.json({ ...shopping, monthly_limit_cents: body.monthly_limit_cents })
    }),
  )
  return { calls, release: resolvePromise }
}

test('opens with the current limit, focus and the money field attributes', () => {
  const onDone = vi.fn()
  renderWithProviders(<CategoryLimitForm category={shopping} onDone={onDone} />)

  const input = screen.getByLabelText('Limite mensal (R$)')
  expect(input).toHaveValue(1500)
  expect(input).toHaveFocus()
  expect(input).toHaveAttribute('type', 'number')
  expect(input).toHaveAttribute('step', '0.01')
  expect(input).toHaveAttribute('min', '0.01')
  expect(input).toHaveAttribute('inputmode', 'decimal')

  expect(screen.getByRole('button', { name: 'Salvar' })).toHaveAttribute('type', 'submit')
  expect(screen.getByRole('button', { name: 'Cancelar' })).toHaveAttribute('type', 'button')
})

test('an empty field plus Enter sends null and calls onDone', async () => {
  const user = userEvent.setup()
  const onDone = vi.fn()
  const calls = spyOnPut()
  renderWithProviders(<CategoryLimitForm category={shopping} onDone={onDone} />)

  const input = screen.getByLabelText('Limite mensal (R$)')
  await user.clear(input)
  const form = input.closest('form')
  if (form === null) throw new Error('form not found')
  fireEvent.submit(form)

  await waitFor(() => {
    expect(calls[0]).toEqual({ key: 'Shopping', body: { monthly_limit_cents: null } })
  })
  expect(onDone).toHaveBeenCalledTimes(1)
})

test('"Salvar" sends the cents, shows "Salvando…" with both buttons disabled and then calls onDone', async () => {
  const user = userEvent.setup()
  const onDone = vi.fn()
  const { calls, release } = spyOnPendingPut()
  renderWithProviders(<CategoryLimitForm category={shopping} onDone={onDone} />)

  const input = screen.getByLabelText('Limite mensal (R$)')
  await user.clear(input)
  await user.type(input, '250.5')
  await user.click(screen.getByRole('button', { name: 'Salvar' }))

  await waitFor(() => {
    expect(calls[0]?.body).toEqual({ monthly_limit_cents: 25050 })
  })
  expect(screen.getByRole('button', { name: 'Salvando…' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Cancelar' })).toBeDisabled()

  release()

  await waitFor(() => {
    expect(onDone).toHaveBeenCalledTimes(1)
  })
})

test('zero shows the field error without calling the API and keeps the value', async () => {
  const user = userEvent.setup()
  const onDone = vi.fn()
  const calls = spyOnPut()
  renderWithProviders(<CategoryLimitForm category={shopping} onDone={onDone} />)

  const input = screen.getByLabelText('Limite mensal (R$)')
  await user.clear(input)
  await user.type(input, '0')
  await user.click(screen.getByRole('button', { name: 'Salvar' }))

  expect(await screen.findByText('Informe um valor maior que zero.')).toBeInTheDocument()
  expect(input).toHaveAttribute('aria-invalid', 'true')
  expect(input).toHaveValue(0)
  expect(calls).toHaveLength(0)
  expect(onDone).not.toHaveBeenCalled()
})

test('more than two decimals shows the field error without calling the API', async () => {
  const user = userEvent.setup()
  const onDone = vi.fn()
  const calls = spyOnPut()
  renderWithProviders(<CategoryLimitForm category={shopping} onDone={onDone} />)

  const input = screen.getByLabelText('Limite mensal (R$)')
  await user.clear(input)
  await user.type(input, '1.999')
  await user.click(screen.getByRole('button', { name: 'Salvar' }))

  expect(await screen.findByText('Use no máximo duas casas decimais.')).toBeInTheDocument()
  expect(calls).toHaveLength(0)
})

test('a 422 from the server goes next to the field and keeps the typed value', async () => {
  const user = userEvent.setup()
  const onDone = vi.fn()
  server.use(
    http.put(
      '/api/categories/:key/limit',
      () => HttpResponse.json({ detail: 'O limite precisa ser maior que zero.' }, { status: 422 }),
    ),
  )
  renderWithProviders(<CategoryLimitForm category={shopping} onDone={onDone} />)

  const input = screen.getByLabelText('Limite mensal (R$)')
  await user.clear(input)
  await user.type(input, '5')
  await user.click(screen.getByRole('button', { name: 'Salvar' }))

  expect(await screen.findByText('O limite precisa ser maior que zero.')).toBeInTheDocument()
  expect(input).toHaveValue(5)
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(onDone).not.toHaveBeenCalled()
})

test('a 500 shows the generic alert and keeps the typed value', async () => {
  const user = userEvent.setup()
  const onDone = vi.fn()
  server.use(http.put('/api/categories/:key/limit', () => HttpResponse.json({}, { status: 500 })))
  renderWithProviders(<CategoryLimitForm category={shopping} onDone={onDone} />)

  const input = screen.getByLabelText('Limite mensal (R$)')
  await user.clear(input)
  await user.type(input, '5')
  await user.click(screen.getByRole('button', { name: 'Salvar' }))

  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Não foi possível salvar o limite. Tente de novo.',
  )
  expect(screen.getByLabelText('Limite mensal (R$)')).toBeInTheDocument()
  expect(screen.getByLabelText('Limite mensal (R$)')).toHaveValue(5)
  expect(onDone).not.toHaveBeenCalled()
})

test('Escape calls onDone without calling the API', () => {
  const onDone = vi.fn()
  const calls = spyOnPut()
  renderWithProviders(<CategoryLimitForm category={shopping} onDone={onDone} />)

  const input = screen.getByLabelText('Limite mensal (R$)')
  fireEvent.keyDown(input, { key: 'Escape' })

  expect(onDone).toHaveBeenCalledTimes(1)
  expect(calls).toHaveLength(0)
})

test('"Cancelar" calls onDone without calling the API', async () => {
  const user = userEvent.setup()
  const onDone = vi.fn()
  const calls = spyOnPut()
  renderWithProviders(<CategoryLimitForm category={shopping} onDone={onDone} />)

  await user.click(screen.getByRole('button', { name: 'Cancelar' }))

  expect(onDone).toHaveBeenCalledTimes(1)
  expect(calls).toHaveLength(0)
})

test('submitting twice while pending sends one call', async () => {
  const user = userEvent.setup()
  const onDone = vi.fn()
  const { calls, release } = spyOnPendingPut()
  renderWithProviders(<CategoryLimitForm category={shopping} onDone={onDone} />)

  const input = screen.getByLabelText('Limite mensal (R$)')
  await user.clear(input)
  await user.type(input, '10')
  const form = input.closest('form')
  if (form === null) throw new Error('form not found')
  fireEvent.submit(form)
  fireEvent.submit(form)

  await waitFor(() => {
    expect(calls).toHaveLength(1)
  })
  release()
})
