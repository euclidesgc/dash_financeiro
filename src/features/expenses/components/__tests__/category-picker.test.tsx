import { http, HttpResponse } from 'msw'
import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'

import { CategoryPicker } from '@/features/expenses/components/category-picker'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'
import { fakeCategories } from '@/testing/mocks/handlers'
import type { CategoryUpdateBody, Expense } from '@/features/expenses/types/expense'

const CATEGORIES = fakeCategories

const BASE: Expense = {
  id: 44,
  date: '2026-08-01',
  description: 'GASTO 44',
  payee_name: null,
  account_name: 'Conta corrente',
  account_institution: 'Banco de teste',
  account_type: 'BANK',
  account_id: 'acc-bank-1',
  category: 'Compras',
  category_key: 'Shopping',
  category_source: 'auto',
  amount_cents: -4400,
}

interface PatchCall {
  id: string
  body: CategoryUpdateBody
}

function spyOnPatch(): PatchCall[] {
  const calls: PatchCall[] = []
  server.use(
    http.patch('/api/transactions/:id/category', async ({ params, request }) => {
      calls.push({ id: params.id as string, body: (await request.json()) as CategoryUpdateBody })
      return HttpResponse.json({
        ...BASE,
        category: 'Supermercado',
        category_key: 'Groceries',
        category_source: 'manual',
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
    http.patch('/api/transactions/:id/category', async ({ params, request }) => {
      calls.push({ id: params.id as string, body: (await request.json()) as CategoryUpdateBody })
      await promise
      return HttpResponse.json({
        ...BASE,
        category: 'Supermercado',
        category_key: 'Groceries',
        category_source: 'manual',
      })
    }),
  )
  return { calls, release: resolvePromise }
}

test('shows the label as a button and no select when closed', () => {
  renderWithProviders(
    <ul>
      <CategoryPicker expense={BASE} categories={CATEGORIES} categoriesReady />
    </ul>,
  )

  const button = screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' })
  expect(button).toHaveTextContent('Compras')
  expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  expect(screen.queryByText('manual')).not.toBeInTheDocument()
})

test('shows "Sem categoria" when the category is null', () => {
  renderWithProviders(
    <ul>
      <CategoryPicker
        expense={{ ...BASE, category: null, category_key: null }}
        categories={CATEGORIES}
        categoriesReady
      />
    </ul>,
  )

  expect(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' })).toHaveTextContent(
    'Sem categoria',
  )
})

test('uses "Sem descrição" in the accessible name when the description is null', () => {
  renderWithProviders(
    <ul>
      <CategoryPicker expense={{ ...BASE, description: null }} categories={CATEGORIES} categoriesReady />
    </ul>,
  )

  expect(screen.getByRole('button', { name: 'Trocar categoria de Sem descrição' })).toBeInTheDocument()
})

test('opens the select with focus and the options in order for an automatic row', async () => {
  const user = userEvent.setup()
  renderWithProviders(
    <ul>
      <CategoryPicker expense={BASE} categories={CATEGORIES} categoriesReady />
    </ul>,
  )

  await user.click(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' }))

  const select = screen.getByRole('combobox', { name: 'Categoria de GASTO 44' })
  expect(select).toHaveFocus()
  expect(select).toHaveValue('Shopping')
  expect(within(select).getAllByRole('option').map((option) => option.textContent)).toEqual([
    'Sem categoria',
    'Alimentação',
    'Compras',
    'Supermercado',
    'Transporte',
  ])
  expect(screen.queryByRole('button', { name: 'Trocar categoria de GASTO 44' })).not.toBeInTheDocument()
})

test('shows "manual" and the "Voltar para a automática" option for a manual row', async () => {
  const user = userEvent.setup()
  renderWithProviders(
    <ul>
      <CategoryPicker expense={{ ...BASE, category_source: 'manual' }} categories={CATEGORIES} categoriesReady />
    </ul>,
  )

  expect(screen.getByText('manual')).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' }))

  const select = screen.getByRole('combobox', { name: 'Categoria de GASTO 44' })
  const options = within(select).getAllByRole('option')
  expect(options.at(-1)).toHaveTextContent('Voltar para a automática')
  expect(options.at(-1)).toHaveValue('__auto__')
})

test('choosing a category sends mode manual with the key, shows the chosen label and "Salvando…" until it settles', async () => {
  const user = userEvent.setup()
  const { calls, release } = spyOnPendingPatch()
  renderWithProviders(
    <ul>
      <CategoryPicker expense={BASE} categories={CATEGORIES} categoriesReady />
    </ul>,
  )

  await user.click(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' }))
  await user.selectOptions(screen.getByRole('combobox', { name: 'Categoria de GASTO 44' }), 'Groceries')

  expect(calls[0]).toEqual({ id: '44', body: { mode: 'manual', category: 'Groceries' } })
  expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  const button = screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' })
  expect(button).toHaveTextContent('Supermercado')
  expect(button).toBeDisabled()
  expect(screen.getByRole('status')).toHaveTextContent('Salvando…')

  release()

  await waitFor(() => {
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' })).toBeEnabled()
  })
})

test('choosing "Sem categoria" sends category null', async () => {
  const user = userEvent.setup()
  const { calls, release } = spyOnPendingPatch()
  renderWithProviders(
    <ul>
      <CategoryPicker expense={BASE} categories={CATEGORIES} categoriesReady />
    </ul>,
  )

  await user.click(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' }))
  await user.selectOptions(screen.getByRole('combobox', { name: 'Categoria de GASTO 44' }), '')

  expect(calls[0]?.body).toEqual({ mode: 'manual', category: null })
  expect(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' })).toHaveTextContent(
    'Sem categoria',
  )

  release()
  await waitFor(() => {
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})

test('choosing "Voltar para a automática" sends mode auto', async () => {
  const user = userEvent.setup()
  const { calls, release } = spyOnPendingPatch()
  renderWithProviders(
    <ul>
      <CategoryPicker expense={{ ...BASE, category_source: 'manual' }} categories={CATEGORIES} categoriesReady />
    </ul>,
  )

  await user.click(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' }))
  await user.selectOptions(screen.getByRole('combobox', { name: 'Categoria de GASTO 44' }), '__auto__')

  expect(calls[0]?.body).toEqual({ mode: 'auto' })

  release()
  await waitFor(() => {
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})

test('on error the label goes back, shows the alert and "Tentar de novo" repeats the same call', async () => {
  const user = userEvent.setup()
  const calls: PatchCall[] = []
  let first = true
  server.use(
    http.patch('/api/transactions/:id/category', async ({ params, request }) => {
      const body = (await request.json()) as CategoryUpdateBody
      calls.push({ id: params.id as string, body })
      if (first) {
        first = false
        return HttpResponse.json({ detail: 'erro' }, { status: 500 })
      }
      return HttpResponse.json({
        ...BASE,
        category: 'Supermercado',
        category_key: 'Groceries',
        category_source: 'manual',
      })
    }),
  )

  renderWithProviders(
    <ul>
      <CategoryPicker expense={BASE} categories={CATEGORIES} categoriesReady />
    </ul>,
  )

  await user.click(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' }))
  await user.selectOptions(screen.getByRole('combobox', { name: 'Categoria de GASTO 44' }), 'Groceries')

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível salvar a categoria.')
  expect(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' })).toHaveTextContent('Compras')

  await user.click(screen.getByRole('button', { name: 'Tentar de novo' }))

  await waitFor(() => {
    expect(calls).toHaveLength(2)
  })
  expect(calls[1]?.body).toEqual(calls[0]?.body)

  await waitFor(() => {
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

test('Escape closes without calling the API', async () => {
  const user = userEvent.setup()
  const calls = spyOnPatch()
  renderWithProviders(
    <ul>
      <CategoryPicker expense={BASE} categories={CATEGORIES} categoriesReady />
    </ul>,
  )

  await user.click(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' }))
  const select = screen.getByRole('combobox', { name: 'Categoria de GASTO 44' })
  fireEvent.keyDown(select, { key: 'Escape' })

  expect(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' })).toBeInTheDocument()
  expect(calls).toHaveLength(0)
})

test('blur closes without calling the API', async () => {
  const user = userEvent.setup()
  const calls = spyOnPatch()
  renderWithProviders(
    <ul>
      <CategoryPicker expense={BASE} categories={CATEGORIES} categoriesReady />
    </ul>,
  )

  await user.click(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' }))
  const select = screen.getByRole('combobox', { name: 'Categoria de GASTO 44' })
  fireEvent.blur(select)

  expect(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' })).toBeInTheDocument()
  expect(calls).toHaveLength(0)
})

test('the button is disabled while the catalogue is not ready', async () => {
  const user = userEvent.setup()
  renderWithProviders(
    <ul>
      <CategoryPicker expense={BASE} categories={CATEGORIES} categoriesReady={false} />
    </ul>,
  )

  const button = screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' })
  expect(button).toBeDisabled()

  await user.click(button)

  expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
})

test('success invalidates the expenses queries', async () => {
  const user = userEvent.setup()
  spyOnPatch()
  const { queryClient } = renderWithProviders(
    <ul>
      <CategoryPicker expense={BASE} categories={CATEGORIES} categoriesReady />
    </ul>,
  )
  const spy = vi.spyOn(queryClient, 'invalidateQueries')

  await user.click(screen.getByRole('button', { name: 'Trocar categoria de GASTO 44' }))
  await user.selectOptions(screen.getByRole('combobox', { name: 'Categoria de GASTO 44' }), 'Groceries')

  await waitFor(() => {
    expect(spy).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['expenses'] }))
  })
})
