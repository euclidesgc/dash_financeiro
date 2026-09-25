import { expect, test } from 'vitest'
import { screen } from '@testing-library/react'

import { AppHeader } from '@/components/layouts/app-header'
import { renderWithProviders } from '@/testing/test-utils'

test('marks "Saldos" as current on the dashboard', () => {
  renderWithProviders(<AppHeader />, { route: '/' })

  expect(screen.getByRole('link', { name: 'Saldos' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('link', { name: 'Gastos' })).not.toHaveAttribute('aria-current')
})

test('marks "Gastos" as current on the expenses page', () => {
  renderWithProviders(<AppHeader />, { route: '/expenses' })

  expect(screen.getByRole('link', { name: 'Gastos' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('link', { name: 'Saldos' })).not.toHaveAttribute('aria-current')
})

test('marks "Categorias" as current on the categories page', () => {
  renderWithProviders(<AppHeader />, { route: '/categories' })

  expect(screen.getByRole('link', { name: 'Categorias' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('link', { name: 'Saldos' })).not.toHaveAttribute('aria-current')
  expect(screen.getByRole('link', { name: 'Gastos' })).not.toHaveAttribute('aria-current')
})

test('renders the login and the action', () => {
  renderWithProviders(
    <AppHeader userLogin="teste" action={<button type="button">Sair</button>} />,
  )

  expect(screen.getByText('teste')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Sair' })).toBeInTheDocument()
})

test('links point to the routes', () => {
  renderWithProviders(<AppHeader />)

  expect(screen.getByRole('link', { name: 'Saldos' })).toHaveAttribute('href', '/')
  expect(screen.getByRole('link', { name: 'Gastos' })).toHaveAttribute('href', '/expenses')
  expect(screen.getByRole('link', { name: 'Categorias' })).toHaveAttribute('href', '/categories')
})
