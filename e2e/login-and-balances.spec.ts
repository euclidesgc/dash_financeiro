import { expect, test } from '@playwright/test'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'

test('signs in, sees the balances and signs out', async ({ page }) => {
  await page.goto('/app/')
  await expect(page).toHaveURL(/\/app\/login$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Entrar' })).toBeVisible()

  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()

  await expect(page).toHaveURL(/\/app\/?$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Saldos de hoje' })).toBeVisible()

  const item = page.getByRole('listitem').filter({ hasText: 'Conta de teste' })
  await expect(item).toContainText('Banco de teste')
  await expect(item.getByText('Conta', { exact: true })).toBeVisible()
  await expect(item).toContainText(/R\$\s12,34/)

  await page.getByRole('button', { name: 'Sair' }).click()
  await expect(page).toHaveURL(/\/app\/login$/)

  await page.goto('/app/')
  await expect(page).toHaveURL(/\/app\/login$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Entrar' })).toBeVisible()
})

test('rejects the wrong password', async ({ page }) => {
  await page.goto('/app/login')

  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill('senha-errada')
  await page.getByRole('button', { name: 'Entrar' }).click()

  await expect(page.getByRole('alert')).toHaveText('Login ou senha inválidos.')
  await expect(page).toHaveURL(/\/app\/login$/)
})
