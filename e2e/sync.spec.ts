import { expect, test } from '@playwright/test'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'

// Reason: both tests trigger a real POST /api/sync/run against the single
// shared e2e SQLite database; running them in parallel workers races on the
// same write lock, so they run one after the other.
test.describe.configure({ mode: 'serial' })

test('updates the records from the balances page', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await expect(page.getByRole('heading', { level: 2, name: 'Atualização dos registros' })).toBeVisible()
  await expect(page.getByText('Nunca atualizado')).toBeVisible()

  const url = page.url()
  await page.getByRole('button', { name: 'Atualizar agora' }).click()

  await expect(page.getByText('Concluída')).toBeVisible()
  await expect(page.getByText(/Última atualização: \d{2}\/\d{2}\/\d{4}/)).toBeVisible()

  const item = page.getByRole('listitem').filter({ hasText: 'Conta de sincronização' })
  await expect(item).toBeVisible()

  expect(page.url()).toBe(url)
})

test('keeps the last update after a reload', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('button', { name: 'Atualizar agora' }).click()
  await expect(page.getByText('Concluída')).toBeVisible()

  await page.reload()

  await expect(page.getByText(/Última atualização: /)).toBeVisible()
  await expect(page.getByText('Nunca atualizado')).not.toBeVisible()
})
