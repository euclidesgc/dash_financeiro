import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import { renderWithProviders } from '@/testing/test-utils'

import { Pagination } from '../pagination'

test('shows page, pages and the plural total', () => {
  renderWithProviders(
    <Pagination page={1} pages={3} total={45} outflowCents={-321000} inflowCents={0} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByText('Página 1 de 3 · 45 gastos · R$ 3.210,00 no período')).toBeInTheDocument()
})

test('uses the singular for one expense', () => {
  renderWithProviders(
    <Pagination page={1} pages={1} total={1} outflowCents={-8490} inflowCents={0} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByText('Página 1 de 1 · 1 gasto · R$ 84,90 no período')).toBeInTheDocument()
})

test('disables "Anterior" on the first page', () => {
  renderWithProviders(
    <Pagination page={1} pages={3} total={45} outflowCents={-321000} inflowCents={0} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Próxima' })).toBeEnabled()
})

test('disables "Próxima" on the last page', () => {
  renderWithProviders(
    <Pagination page={3} pages={3} total={45} outflowCents={-321000} inflowCents={0} isFetching={false} onChange={vi.fn()} />,
  )

  expect(screen.getByRole('button', { name: 'Próxima' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Anterior' })).toBeEnabled()
})

test('disables both while fetching', () => {
  renderWithProviders(
    <Pagination page={2} pages={3} total={45} outflowCents={-321000} inflowCents={0} isFetching={true} onChange={vi.fn()} />,
  )

  expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Próxima' })).toBeDisabled()
})

test('calls onChange with the neighbour page', async () => {
  const onChangeNext = vi.fn()
  const { unmount } = renderWithProviders(
    <Pagination page={1} pages={3} total={45} outflowCents={-321000} inflowCents={0} isFetching={false} onChange={onChangeNext} />,
  )

  await userEvent.click(screen.getByRole('button', { name: 'Próxima' }))

  expect(onChangeNext).toHaveBeenCalledWith(2)

  unmount()

  const onChangePrevious = vi.fn()
  renderWithProviders(
    <Pagination page={2} pages={3} total={45} outflowCents={-321000} inflowCents={0} isFetching={false} onChange={onChangePrevious} />,
  )

  await userEvent.click(screen.getByRole('button', { name: 'Anterior' }))

  expect(onChangePrevious).toHaveBeenCalledWith(1)
})

test('shows R$ 0,00 when the total is zero', () => {
  renderWithProviders(
    <Pagination page={1} pages={1} total={0} outflowCents={0} inflowCents={0} isFetching={false} onChange={vi.fn()} />,
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
      outflowCents={-6000} inflowCents={0}
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
      outflowCents={-6000} inflowCents={0}
      isFetching={false}
      onChange={vi.fn()}
      noun={{ one: 'lançamento', many: 'lançamentos' }}
    />,
  )

  expect(screen.getByText('Página 1 de 1 · 2 lançamentos · R$ 60,00 no período')).toBeInTheDocument()
})

test('shows the money that moved, never a difference, when the flows are not split', () => {
  renderWithProviders(
    <Pagination
      page={1}
      pages={1}
      total={1}
      outflowCents={0}
      inflowCents={600000}
      isFetching={false}
      onChange={vi.fn()}
      noun={{ one: 'entrada', many: 'entradas' }}
    />,
  )

  expect(screen.getByText('Página 1 de 1 · 1 entrada · R$ 6.000,00 no período')).toBeInTheDocument()
})

test('shows the outflows and the inflows apart when the flows are split', () => {
  renderWithProviders(
    <Pagination
      page={1}
      pages={1}
      total={2}
      outflowCents={-100000}
      inflowCents={100000}
      splitFlows
      isFetching={false}
      onChange={vi.fn()}
      noun={{ one: 'lançamento', many: 'lançamentos' }}
    />,
  )

  expect(
    screen.getByText(
      'Página 1 de 1 · 2 lançamentos · R$ 1.000,00 em saídas e R$ 1.000,00 em entradas no período',
    ),
  ).toBeInTheDocument()
})

test('keeps a split side with nothing in it at R$ 0,00 without a minus sign', () => {
  renderWithProviders(
    <Pagination
      page={1}
      pages={1}
      total={1}
      outflowCents={0}
      inflowCents={15000}
      splitFlows
      isFetching={false}
      onChange={vi.fn()}
      noun={{ one: 'lançamento', many: 'lançamentos' }}
    />,
  )

  const summary = screen.getByText(/no período/)
  expect(summary).toHaveTextContent('R$ 0,00 em saídas e R$ 150,00 em entradas no período')
  expect(summary).not.toHaveTextContent('-R$')
})
