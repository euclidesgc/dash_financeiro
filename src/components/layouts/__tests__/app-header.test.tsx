import { expect, test } from 'vitest'
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

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
  expect(screen.getByRole('link', { name: 'Conexões' })).toHaveAttribute('href', '/connections')
})

test('marks "Conexões" as current on the connections page', () => {
  renderWithProviders(<AppHeader />, { route: '/connections' })

  expect(screen.getByRole('link', { name: 'Conexões' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('link', { name: 'Categorias' })).not.toHaveAttribute('aria-current')
})

test('"Mais telas" opens full-page links to the old panel screens', async () => {
  const user = userEvent.setup()
  renderWithProviders(<AppHeader />, { route: '/expenses' })

  const navigation = screen.getByRole('navigation', { name: 'Principal' })
  await user.click(within(navigation).getByText('Mais telas'))

  const expected = [
    ['Resumo', '/'],
    ['Objetivo', '/objetivo'],
    ['Dívidas', '/dividas'],
    ['Simulador', '/simulador'],
    ['Consultor antigo', '/consultor'],
    ['Configuração', '/configuracao'],
  ]
  for (const [name, href] of expected) {
    const link = within(navigation).getByRole('link', { name })
    expect(link).toBeVisible()
    expect(link).toHaveAttribute('href', href)
    expect(link).not.toHaveAttribute('aria-current')
  }
})

test('marks "Consultor" as current on the advisor page', () => {
  renderWithProviders(<AppHeader />, { route: '/advisor' })

  expect(screen.getByRole('link', { name: 'Consultor' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('link', { name: 'Consultor' })).toHaveAttribute('href', '/advisor')
})
