import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import { renderWithProviders } from '@/testing/test-utils'

import { Pagination } from '../pagination'

test('shows page, pages and the plural total', () => {
  renderWithProviders(
    <Pagination page={1} pages={3} total={45} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByText('Página 1 de 3 · 45 gastos')).toBeInTheDocument()
})

test('uses the singular for one expense', () => {
  renderWithProviders(
    <Pagination page={1} pages={1} total={1} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByText('Página 1 de 1 · 1 gasto')).toBeInTheDocument()
})

test('disables "Anterior" on the first page', () => {
  renderWithProviders(
    <Pagination page={1} pages={3} total={45} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Próxima' })).toBeEnabled()
})

test('disables "Próxima" on the last page', () => {
  renderWithProviders(
    <Pagination page={3} pages={3} total={45} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByRole('button', { name: 'Próxima' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Anterior' })).toBeEnabled()
})

test('disables both while fetching', () => {
  renderWithProviders(
    <Pagination page={2} pages={3} total={45} isFetching={true} onChange={vi.fn()} />,
  )

  expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Próxima' })).toBeDisabled()
})

test('calls onChange with the neighbour page', async () => {
  const onChangeNext = vi.fn()
  const { unmount } = renderWithProviders(
    <Pagination page={1} pages={3} total={45} isFetching={false} onChange={onChangeNext} />,
  )

  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }))

  expect(onChangeNext).toHaveBeenCalledWith(2)

  unmount()

  const onChangePrevious = vi.fn()
  renderWithProviders(
    <Pagination page={2} pages={3} total={45} isFetching={false} onChange={onChangePrevious} />,
  )

  await userEvent.click(screen.getByRole('button', { name: 'Anterior' }))

  expect(onChangePrevious).toHaveBeenCalledWith(1)
})
