import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import { renderWithProviders } from '@/testing/test-utils'

import { Pagination } from '../pagination'

test('shows page, pages and the plural total', () => {
  renderWithProviders(
    <Pagination page={1} pages={3} total={45} totalCents={-321000} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByText('Página 1 de 3 · 45 gastos · R$ 3.210,00 no período')).toBeInTheDocument()
})

test('uses the singular for one expense', () => {
  renderWithProviders(
    <Pagination page={1} pages={1} total={1} totalCents={-8490} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByText('Página 1 de 1 · 1 gasto · R$ 84,90 no período')).toBeInTheDocument()
})

test('disables "Anterior" on the first page', () => {
  renderWithProviders(
    <Pagination page={1} pages={3} total={45} totalCents={-321000} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Próxima' })).toBeEnabled()
})

test('disables "Próxima" on the last page', () => {
  renderWithProviders(
    <Pagination page={3} pages={3} total={45} totalCents={-321000} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByRole('button', { name: 'Próxima' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Anterior' })).toBeEnabled()
})

test('disables both while fetching', () => {
  renderWithProviders(
    <Pagination page={2} pages={3} total={45} totalCents={-321000} isFetching={true} onChange={vi.fn()} />,
  )

  expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Próxima' })).toBeDisabled()
})

test('calls onChange with the neighbour page', async () => {
  const onChangeNext = vi.fn()
  const { unmount } = renderWithProviders(
    <Pagination page={1} pages={3} total={45} totalCents={-321000} isFetching={false} onChange={onChangeNext} />,
  )

  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }))

  expect(onChangeNext).toHaveBeenCalledWith(2)

  unmount()

  const onChangePrevious = vi.fn()
  renderWithProviders(
    <Pagination page={2} pages={3} total={45} totalCents={-321000} isFetching={false} onChange={onChangePrevious} />,
  )

  await userEvent.click(screen.getByRole('button', { name: 'Anterior' }))

  expect(onChangePrevious).toHaveBeenCalledWith(1)
})

test('shows R$ 0,00 when the total is zero', () => {
  renderWithProviders(
    <Pagination page={1} pages={1} total={0} totalCents={0} isFetching={false} onChange={vi.fn()} />,
  )

  const summary = screen.getByText(/no período/)
  expect(summary).toHaveTextContent('R$ 0,00 no período')
  expect(summary).not.toHaveTextContent('-R$')
})

test('uses the noun given for the singular and the plural', () => {
  const { unmount } = renderWithProviders(
    <Pagination
      page={1}
      pages={1}
      total={1}
      totalCents={-6000}
      isFetching={false}
      onChange={vi.fn()}
      noun={{ one: 'lançamento', many: 'lançamentos' }}
    />,
  )

  expect(screen.getByText('Página 1 de 1 · 1 lançamento · R$ 60,00 no período')).toBeInTheDocument()

  unmount()

  renderWithProviders(
    <Pagination
      page={1}
      pages={1}
      total={2}
      totalCents={-6000}
      isFetching={false}
      onChange={vi.fn()}
      noun={{ one: 'lançamento', many: 'lançamentos' }}
    />,
  )

  expect(screen.getByText('Página 1 de 1 · 2 lançamentos · R$ 60,00 no período')).toBeInTheDocument()
})
