import { expect, test } from '@playwright/test'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'

// Reason: both tests share the same real backend session flow, and
// sync.spec.ts writes into the same shared e2e SQLite database that this
// spec reads from; running specs across workers in parallel could race.
test.describe.configure({ mode: 'serial' })

test('opens the expenses page and lists only the spending', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Gastos' }).click()
  await expect(page).toHaveURL(/\/app\/expenses$/)

  await expect(page.getByRole('heading', { level: 1, name: 'Gastos' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Gastos' })).toHaveAttribute('aria-current', 'page')

  const item = page.getByRole('listitem').filter({ hasText: 'MERCADO DO BAIRRO' })
  await expect(item).toBeVisible()
  await expect(item).toContainText('02/09/2026')
  await expect(item).toContainText('-R$ 84,90')

  await expect(page.getByText('TED PARA POUPANCA')).toHaveCount(0)
  await expect(page.getByText('SALARIO')).toHaveCount(0)

  await expect(page.getByText(/Página 1 de 1 · [23] gastos/)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Anterior' })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Próxima' })).toBeDisabled()
})

test('reorders the expenses by amount and by category and keeps the order on reload', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Gastos' }).click()
  await expect(page).toHaveURL(/\/app\/expenses$/)

  const orderButton = page.getByRole('button', { name: 'Inverter direção da ordenação' })

  await expect(page.getByRole('listitem').first()).toContainText('MERCADO DO BAIRRO')
  await expect(page.getByLabel('Ordenar por')).toHaveValue('date')
  await expect(orderButton).toHaveText('Decrescente')

  await page.getByLabel('Ordenar por').selectOption('amount')
  await expect(page).toHaveURL(/sort=amount/)
  await expect(page.getByRole('listitem').first()).toContainText('POSTO CENTRAL')
  await expect(page.getByRole('listitem').first()).toContainText('-R$ 150,00')

  await orderButton.click()
  await expect(page).toHaveURL(/order=asc/)
  await expect(orderButton).toHaveText('Crescente')
  await expect(page.getByRole('listitem').first()).not.toContainText('POSTO CENTRAL')
  await expect(page.getByRole('listitem').last()).toContainText('POSTO CENTRAL')

  await page.reload()
  await expect(page.getByLabel('Ordenar por')).toHaveValue('amount')
  await expect(orderButton).toHaveText('Crescente')
  await expect(page.getByRole('listitem').last()).toContainText('POSTO CENTRAL')
  await expect(page).toHaveURL(/sort=amount/)

  await page.getByLabel('Ordenar por').selectOption('category')
  await expect(page).toHaveURL(/sort=category/)
  await expect(page.getByRole('listitem').first()).toContainText('POSTO CENTRAL')
  await expect(page.getByRole('listitem').first()).toContainText('Casa')

  await page.getByLabel('Ordenar por').selectOption('date')
  await expect(page).not.toHaveURL(/sort=/)
  await expect(page.getByRole('listitem').first()).toContainText('MERCADO DO BAIRRO')
})

test('goes back to the balances page', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Gastos' }).click()
  await expect(page).toHaveURL(/\/app\/expenses$/)

  await page.getByRole('link', { name: 'Saldos' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Saldos de hoje' })).toBeVisible()
  await expect(page).toHaveURL(/\/app\/?$/)
})
