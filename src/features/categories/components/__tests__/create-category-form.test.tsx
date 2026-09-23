import { http, HttpResponse } from 'msw'
import { expect, test } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor } from '@testing-library/react'

import { CreateCategoryForm } from '@/features/categories/components/create-category-form'
import { renderWithProviders } from '@/testing/test-utils'
import { server } from '@/testing/mocks/server'

interface PostCall {
  body: { label: string }
}

function spyOnPost(): PostCall[] {
  const calls: PostCall[] = []
  server.use(
    http.post('/api/categories', async ({ request }) => {
      const body = (await request.json()) as { label: string }
      calls.push({ body })
      return HttpResponse.json(
        { key: 'nova', label: body.label.trim(), is_system: false, usage_count: 0 },
        { status: 201 },
      )
    }),
  )
  return calls
}

function spyOnPendingPost(): { calls: PostCall[]; release: () => void } {
  const calls: PostCall[] = []
  let resolvePromise: () => void = () => {
    /* replaced below */
  }
  const promise = new Promise<void>((resolve) => {
    resolvePromise = resolve
  })
  server.use(
    http.post('/api/categories', async ({ request }) => {
      const body = (await request.json()) as { label: string }
      calls.push({ body })
      await promise
      return HttpResponse.json(
        { key: 'nova', label: body.label.trim(), is_system: false, usage_count: 0 },
        { status: 201 },
      )
    }),
  )
  return { calls, release: resolvePromise }
}

test('renders the heading, the labelled field and the submit button', () => {
  renderWithProviders(<CreateCategoryForm />)

  expect(screen.getByRole('heading', { level: 2, name: 'Nova categoria' })).toBeInTheDocument()
  expect(screen.getByLabelText('Nome da categoria')).toHaveAttribute('type', 'text')
  expect(screen.getByRole('button', { name: 'Criar categoria' })).toHaveAttribute('type', 'submit')
})

test('submitting empty shows the message, focuses the field and does not call the API', async () => {
  const user = userEvent.setup()
  const calls = spyOnPost()
  renderWithProviders(<CreateCategoryForm />)

  await user.click(screen.getByRole('button', { name: 'Criar categoria' }))

  expect(screen.getByText('Informe o nome da categoria.')).toBeInTheDocument()
  const input = screen.getByLabelText('Nome da categoria')
  expect(input).toHaveFocus()
  expect(input).toHaveAttribute('aria-invalid', 'true')
  expect(calls).toHaveLength(0)
})

test('a 422 from the server shows next to the field and keeps the value', async () => {
  const user = userEvent.setup()
  server.use(
    http.post('/api/categories', () =>
      HttpResponse.json({ detail: 'Já existe uma categoria com esse nome.' }, { status: 422 }),
    ),
  )
  renderWithProviders(<CreateCategoryForm />)

  await user.type(screen.getByLabelText('Nome da categoria'), '  supermercado ')
  await user.click(screen.getByRole('button', { name: 'Criar categoria' }))

  expect(await screen.findByText('Já existe uma categoria com esse nome.')).toBeInTheDocument()
  expect(screen.getByLabelText('Nome da categoria')).toHaveValue('  supermercado ')
})

test('a valid name sends POST with the trimmed label and clears the field', async () => {
  const user = userEvent.setup()
  const calls = spyOnPost()
  renderWithProviders(<CreateCategoryForm />)

  await user.type(screen.getByLabelText('Nome da categoria'), '  Pet food ')
  await user.click(screen.getByRole('button', { name: 'Criar categoria' }))

  await waitFor(() => {
    expect(calls[0]?.body).toEqual({ label: 'Pet food' })
  })
  await waitFor(() => {
    expect(screen.getByLabelText('Nome da categoria')).toHaveValue('')
  })
})

test('"Criando…" is shown while pending', async () => {
  const user = userEvent.setup()
  const { release } = spyOnPendingPost()
  renderWithProviders(<CreateCategoryForm />)

  await user.type(screen.getByLabelText('Nome da categoria'), 'Lanche')
  await user.click(screen.getByRole('button', { name: 'Criar categoria' }))

  const button = screen.getByRole('button', { name: 'Criando…' })
  expect(button).toBeDisabled()

  release()

  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Criar categoria' })).toBeEnabled()
  })
})

test('a 500 shows the generic alert and keeps the value', async () => {
  const user = userEvent.setup()
  server.use(http.post('/api/categories', () => HttpResponse.json({}, { status: 500 })))
  renderWithProviders(<CreateCategoryForm />)

  await user.type(screen.getByLabelText('Nome da categoria'), 'Lanche')
  await user.click(screen.getByRole('button', { name: 'Criar categoria' }))

  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Não foi possível salvar a categoria. Tente de novo.')
  expect(screen.getByLabelText('Nome da categoria')).toHaveValue('Lanche')
  expect(screen.queryByText('Informe o nome da categoria.')).not.toBeInTheDocument()
})

test('pressing Enter twice while pending sends one call', async () => {
  const user = userEvent.setup()
  const { calls, release } = spyOnPendingPost()
  renderWithProviders(<CreateCategoryForm />)

  await user.type(screen.getByLabelText('Nome da categoria'), 'Lanche')
  await user.keyboard('{Enter}{Enter}')

  await waitFor(() => {
    expect(calls).toHaveLength(1)
  })

  release()
})
