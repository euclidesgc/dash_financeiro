import { http, HttpResponse } from 'msw'
import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'

import { CategoriesList } from '@/features/categories/components/categories-list'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import { fakeCategories } from '@/testing/mocks/handlers'

interface DeleteCall {
  key: string
}

interface PatchCall {
  key: string
  body: { label: string }
}

interface PutCall {
  key: string
  body: { monthly_limit_cents: number | null }
}

function itemOf(label: string): HTMLElement {
  const labelEl = screen.getByText(label, { selector: '[title]', exact: true })
  const item = labelEl.closest('li')
  if (item === null) {
    throw new Error(`no <li> found for "${label}"`)
  }
  return item
}

function spyOnDelete(): DeleteCall[] {
  const calls: DeleteCall[] = []
  server.use(
    http.delete('/api/categories/:key', ({ params }) => {
      calls.push({ key: params.key as string })
      return new HttpResponse(null, { status: 204 })
    }),
  )
  return calls
}

function spyOnPendingDelete(): { calls: DeleteCall[]; release: () => void } {
  const calls: DeleteCall[] = []
  let resolvePromise: () => void = () => {
    /* replaced below */
  }
  const promise = new Promise<void>((resolve) => {
    resolvePromise = resolve
  })
  server.use(
    http.delete('/api/categories/:key', async ({ params }) => {
      calls.push({ key: params.key as string })
      await promise
      const index = fakeCategories.findIndex((category) => category.key === params.key)
      if (index !== -1) {
        fakeCategories.splice(index, 1)
      }
      return new HttpResponse(null, { status: 204 })
    }),
  )
  return { calls, release: resolvePromise }
}

function spyOnPatch(): PatchCall[] {
  const calls: PatchCall[] = []
  server.use(
    http.patch('/api/categories/:key', async ({ params, request }) => {
      const body = (await request.json()) as { label: string }
      calls.push({ key: params.key as string, body })
      const item = fakeCategories.find((category) => category.key === params.key)
      if (item !== undefined) {
        item.label = body.label.trim()
      }
      return HttpResponse.json({
        key: params.key as string,
        label: body.label.trim(),
        is_system: item?.is_system ?? false,
        usage_count: item?.usage_count ?? 0,
      })
    }),
  )
  return calls
}

function spyOnPendingPatch(): { calls: PatchCall[]; release: () => void } {
  const calls: PatchCall[] = []
  let resolvePromise: () => void = () => {
    /* replaced below */
  }
  const promise = new Promise<void>((resolve) => {
    resolvePromise = resolve
  })
  server.use(
    http.patch('/api/categories/:key', async ({ params, request }) => {
      const body = (await request.json()) as { label: string }
      calls.push({ key: params.key as string, body })
      await promise
      const item = fakeCategories.find((category) => category.key === params.key)
      if (item !== undefined) {
        item.label = body.label.trim()
      }
      return HttpResponse.json({
        key: params.key as string,
        label: body.label.trim(),
        is_system: item?.is_system ?? false,
        usage_count: item?.usage_count ?? 0,
      })
    }),
  )
  return { calls, release: resolvePromise }
}

function spyOnPut(): PutCall[] {
  const calls: PutCall[] = []
  server.use(
    http.put('/api/categories/:key/limit', async ({ params, request }) => {
      const body = (await request.json()) as { monthly_limit_cents: number | null }
      calls.push({ key: params.key as string, body })
      const item = fakeCategories.find((category) => category.key === params.key)
      if (item !== undefined) {
        item.monthly_limit_cents = body.monthly_limit_cents
      }
      return HttpResponse.json(item)
    }),
  )
  return calls
}

test('shows the loading state', () => {
  renderWithProviders(<CategoriesList />)

  expect(screen.getByRole('status')).toHaveTextContent('Carregando categorias…')
})

test('shows the error and "Tentar de novo" refetches', async () => {
  const user = userEvent.setup()
  let attempt = 0
  server.use(
    http.get('/api/categories', () => {
      attempt += 1
      if (attempt === 1) {
        return HttpResponse.json({}, { status: 500 })
      }
      return HttpResponse.json({
        categories: [
          { key: 'Food', label: 'Alimentação', is_system: true, usage_count: 1, monthly_limit_cents: null },
          { key: 'Shopping', label: 'Compras', is_system: true, usage_count: 40, monthly_limit_cents: null },
          { key: 'lazer', label: 'Lazer', is_system: false, usage_count: 3, monthly_limit_cents: null },
          { key: 'pet-shop', label: 'Pet shop', is_system: false, usage_count: 0, monthly_limit_cents: null },
          { key: 'Groceries', label: 'Supermercado', is_system: true, usage_count: 0, monthly_limit_cents: null },
          { key: 'Transport', label: 'Transporte', is_system: true, usage_count: 1, monthly_limit_cents: null },
        ],
      })
    }),
  )

  renderWithProviders(<CategoriesList />)

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível carregar as categorias.')

  await user.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  expect(await screen.findAllByRole('listitem')).toHaveLength(6)
})

test('lists the catalogue in the order of the API with badges and counts', async () => {
  renderWithProviders(<CategoriesList />)

  const items = await screen.findAllByRole('listitem')
  expect(items).toHaveLength(6)
  expect(items.map((item) => within(item).getByText(/./, { selector: '[title]' }).textContent)).toEqual(
    ['Alimentação', 'Compras', 'Lazer', 'Pet shop', 'Supermercado', 'Transporte'],
  )

  expect(within(itemOf('Alimentação')).getByText('Do sistema')).toBeInTheDocument()
  expect(within(itemOf('Alimentação')).getByText('1 gasto')).toBeInTheDocument()
  expect(within(itemOf('Compras')).getByText('40 gastos')).toBeInTheDocument()
  expect(within(itemOf('Pet shop')).getByText('Criada por você')).toBeInTheDocument()
  expect(within(itemOf('Pet shop')).getByText('Nenhum gasto')).toBeInTheDocument()
  expect(within(itemOf('Lazer')).getByText('3 gastos')).toBeInTheDocument()
})

test('hides "Apagar" on system categories and shows it on the owner\'s', async () => {
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')

  expect(screen.queryByRole('button', { name: 'Apagar Supermercado' })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Apagar Pet shop' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Apagar Lazer' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Renomear Alimentação' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Renomear Compras' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Renomear Lazer' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Renomear Pet shop' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Renomear Supermercado' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Renomear Transporte' })).toBeInTheDocument()
})

test('"Apagar" on a category in use shows the notice without calling the API', async () => {
  const user = userEvent.setup()
  const calls = spyOnDelete()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Apagar Lazer' }))

  const item = itemOf('Lazer')
  expect(within(item).getByRole('alert')).toHaveTextContent(
    'Esta categoria está em uso por 3 gastos. Troque a categoria desses gastos antes de apagá-la.',
  )
  expect(calls).toHaveLength(0)

  await user.click(within(item).getByRole('button', { name: 'Fechar' }))

  expect(within(item).queryByRole('alert')).not.toBeInTheDocument()
})

test('"Apagar" on a free category asks for confirmation and "Confirmar" deletes it', async () => {
  const user = userEvent.setup()
  const { calls, release } = spyOnPendingDelete()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Apagar Pet shop' }))

  const item = itemOf('Pet shop')
  expect(within(item).getByText('Apagar a categoria “Pet shop”?')).toBeInTheDocument()

  await user.click(within(item).getByRole('button', { name: 'Confirmar' }))

  expect(calls[0]).toEqual({ key: 'pet-shop' })
  expect(within(item).getByRole('button', { name: 'Apagando…' })).toBeDisabled()

  release()

  await waitFor(() => {
    expect(screen.queryByText('Pet shop')).not.toBeInTheDocument()
  })
  expect(screen.getAllByRole('listitem')).toHaveLength(5)
})

test('"Cancelar" closes the confirmation without calling the API', async () => {
  const user = userEvent.setup()
  const calls = spyOnDelete()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Apagar Pet shop' }))

  const item = itemOf('Pet shop')
  await user.click(within(item).getByRole('button', { name: 'Cancelar' }))

  expect(calls).toHaveLength(0)
  expect(within(item).getByRole('button', { name: 'Apagar Pet shop' })).toBeInTheDocument()
})

test('a 409 on delete shows the server detail and "Tentar de novo" repeats the call', async () => {
  const user = userEvent.setup()
  let attempt = 0
  server.use(
    http.delete('/api/categories/:key', () => {
      attempt += 1
      if (attempt === 1) {
        return HttpResponse.json(
          { detail: 'Esta categoria está em uso por 3 gastos.' },
          { status: 409 },
        )
      }
      return new HttpResponse(null, { status: 204 })
    }),
  )
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Apagar Pet shop' }))

  const item = itemOf('Pet shop')
  await user.click(within(item).getByRole('button', { name: 'Confirmar' }))

  expect(await within(item).findByRole('alert')).toHaveTextContent(
    'Esta categoria está em uso por 3 gastos.',
  )

  await user.click(within(item).getByRole('button', { name: 'Tentar de novo' }))

  await waitFor(() => {
    expect(attempt).toBe(2)
  })
})

test('a 500 on delete shows the generic message', async () => {
  const user = userEvent.setup()
  server.use(http.delete('/api/categories/:key', () => HttpResponse.json({}, { status: 500 })))
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Apagar Pet shop' }))

  const item = itemOf('Pet shop')
  await user.click(within(item).getByRole('button', { name: 'Confirmar' }))

  expect(await within(item).findByRole('alert')).toHaveTextContent(
    'Não foi possível apagar a categoria. Tente de novo.',
  )
})

test('"Renomear" opens the field with the label and focus, and Escape closes it without calling the API', async () => {
  const user = userEvent.setup()
  const calls = spyOnPatch()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Renomear Supermercado' }))

  const item = itemOf('Supermercado')
  const input = within(item).getByLabelText('Novo nome')
  expect(input).toHaveValue('Supermercado')
  expect(input).toHaveFocus()

  fireEvent.keyDown(input, { key: 'Escape' })

  expect(within(item).queryByLabelText('Novo nome')).not.toBeInTheDocument()
  expect(calls).toHaveLength(0)
})

test('the rename field stops at the 40 characters the server accepts', async () => {
  const user = userEvent.setup()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Renomear Supermercado' }))

  const input = within(itemOf('Supermercado')).getByLabelText('Novo nome')
  await user.clear(input)
  await user.type(input, 'a'.repeat(45))

  expect(input).toHaveAttribute('maxLength', '40')
  expect(input).toHaveValue('a'.repeat(40))
})

test('"Cancelar" closes the rename without calling the API', async () => {
  const user = userEvent.setup()
  const calls = spyOnPatch()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Renomear Supermercado' }))

  const item = itemOf('Supermercado')
  await user.click(within(item).getByRole('button', { name: 'Cancelar' }))

  expect(within(item).queryByLabelText('Novo nome')).not.toBeInTheDocument()
  expect(calls).toHaveLength(0)
})

test('saving an empty name shows the field error without calling the API', async () => {
  const user = userEvent.setup()
  const calls = spyOnPatch()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Renomear Supermercado' }))

  const item = itemOf('Supermercado')
  const input = within(item).getByLabelText('Novo nome')
  await user.clear(input)
  await user.click(within(item).getByRole('button', { name: 'Salvar' }))

  expect(within(item).getByText('Informe o nome da categoria.')).toBeInTheDocument()
  expect(input).toHaveAttribute('aria-invalid', 'true')
  expect(calls).toHaveLength(0)
})

test('a 422 on rename shows the server message next to the field and keeps the typed value', async () => {
  const user = userEvent.setup()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Renomear Supermercado' }))

  const item = itemOf('Supermercado')
  const input = within(item).getByLabelText('Novo nome')
  await user.clear(input)
  await user.type(input, 'compras')
  await user.click(within(item).getByRole('button', { name: 'Salvar' }))

  expect(await within(item).findByText('Já existe uma categoria com esse nome.')).toBeInTheDocument()
  expect(input).toHaveValue('compras')
  expect(within(item).getByLabelText('Novo nome')).toBeInTheDocument()
})

test('saving a new name sends PATCH and the list shows it', async () => {
  const user = userEvent.setup()
  const calls = spyOnPatch()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Renomear Supermercado' }))

  const item = itemOf('Supermercado')
  const input = within(item).getByLabelText('Novo nome')
  await user.clear(input)
  await user.type(input, 'Mercado')
  await user.click(within(item).getByRole('button', { name: 'Salvar' }))

  await waitFor(() => {
    expect(calls[0]).toEqual({ key: 'Groceries', body: { label: 'Mercado' } })
  })
  expect(await screen.findByText('Mercado', { selector: '[title]' })).toBeInTheDocument()
  expect(screen.queryByLabelText('Novo nome')).not.toBeInTheDocument()
})

test('"Salvando…" is shown while the rename is pending', async () => {
  const user = userEvent.setup()
  const { release } = spyOnPendingPatch()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Renomear Pet shop' }))

  const item = itemOf('Pet shop')
  const input = within(item).getByLabelText('Novo nome')
  await user.clear(input)
  await user.type(input, 'Bicho')
  await user.click(within(item).getByRole('button', { name: 'Salvar' }))

  expect(within(item).getByRole('button', { name: 'Salvando…' })).toBeDisabled()

  release()

  await waitFor(() => {
    expect(screen.queryByLabelText('Novo nome')).not.toBeInTheDocument()
  })
})

test('success invalidates the categories and the expenses queries', async () => {
  const user = userEvent.setup()
  spyOnPatch()
  const { queryClient } = renderWithProviders(<CategoriesList />)
  const spy = vi.spyOn(queryClient, 'invalidateQueries')

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Renomear Pet shop' }))

  const item = itemOf('Pet shop')
  const input = within(item).getByLabelText('Novo nome')
  await user.clear(input)
  await user.type(input, 'Bicho')
  await user.click(within(item).getByRole('button', { name: 'Salvar' }))

  await waitFor(() => {
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['categories'] }))
  })
  await waitFor(() => {
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['expenses'] }))
  })
})

test('shows the limit of each category or "Sem limite"', async () => {
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')

  expect(within(itemOf('Compras')).getByText('Limite: R$ 1.500,00')).toBeInTheDocument()
  expect(within(itemOf('Alimentação')).getByText('Limite: R$ 800,00')).toBeInTheDocument()
  expect(within(itemOf('Pet shop')).getByText('Sem limite')).toBeInTheDocument()
  expect(within(itemOf('Supermercado')).getByText('Sem limite')).toBeInTheDocument()
})

test('shows "Limite" on every row, system ones included, named by whether a limit is set', async () => {
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')

  expect(screen.getByRole('button', { name: 'Definir limite de Supermercado' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Alterar limite de Compras' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Definir limite de Pet shop' })).toBeInTheDocument()
})

test('"Limite" opens the field with the current value in the row', async () => {
  const user = userEvent.setup()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Alterar limite de Compras' }))

  const item = itemOf('Compras')
  const input = within(item).getByLabelText('Limite mensal (R$)')
  expect(input).toHaveValue('1.500,00')
  expect(input).toHaveFocus()
  expect(within(item).queryByRole('button', { name: 'Alterar limite de Compras' })).not.toBeInTheDocument()
})

test('saving a limit sends PUT, the row shows it and the categories query is invalidated', async () => {
  const user = userEvent.setup()
  spyOnPut()
  const { queryClient } = renderWithProviders(<CategoriesList />)
  const spy = vi.spyOn(queryClient, 'invalidateQueries')

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Definir limite de Pet shop' }))

  const item = itemOf('Pet shop')
  const input = within(item).getByLabelText('Limite mensal (R$)')
  await user.clear(input)
  await user.type(input, '300')
  await user.click(within(item).getByRole('button', { name: 'Salvar' }))

  expect(await within(item).findByText('Limite: R$ 300,00')).toBeInTheDocument()
  expect(within(item).queryByLabelText('Limite mensal (R$)')).not.toBeInTheDocument()
  await waitFor(() => {
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['categories'] }))
  })
  await waitFor(() => {
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['expenses'] }))
  })
})

test('"Remover limite" sends null and the row shows "Sem limite"', async () => {
  const user = userEvent.setup()
  spyOnPut()
  renderWithProviders(<CategoriesList />)

  await screen.findAllByRole('listitem')
  await user.click(screen.getByRole('button', { name: 'Alterar limite de Compras' }))

  const item = itemOf('Compras')
  await user.click(within(item).getByRole('button', { name: 'Remover limite' }))

  expect(await within(item).findByText('Sem limite')).toBeInTheDocument()
})
