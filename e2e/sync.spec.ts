import { expect, test } from '@playwright/test'

import { restoreSeededBase } from './restore-seeded-base'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'

// Reason: both tests trigger a real POST /api/sync/run against the single
// shared e2e SQLite database; running them in parallel workers races on the
// same write lock, so they run one after the other.
test.describe.configure({ mode: 'serial' })

// Reason: every test here runs a real sync, which the API cannot undo, and the
// first one needs a base that was never synced; the seed snapshot is copied
// back before and after each test, whether it passed or not.
test.beforeEach(() => {
  restoreSeededBase()
})

test.afterEach(() => {
  restoreSeededBase()
})

test('updates the records from the balances page', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await expect(page.getByRole('heading', { level: 2, name: 'Atualização dos registros' })).toBeVisible()
  await expect(page.getByText('Nenhuma atualização feita por este painel ainda')).toBeVisible()

  const url = page.url()
  await page.getByRole('button', { name: 'Atualizar agora' }).click()

  await expect(page.getByText('Terminou sem erro')).toBeVisible()
  await expect(page.getByText(/Última atualização: \d{2}\/\d{2}\/\d{4}/)).toBeVisible()
  await expect(page.getByText('Você pediu pelo botão “Atualizar agora”')).toBeVisible()

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
  await expect(page.getByText('Terminou sem erro')).toBeVisible()

  await page.reload()

  await expect(page.getByText(/Última atualização: /)).toBeVisible()
  await expect(page.getByText('Nenhuma atualização feita por este painel ainda')).not.toBeVisible()
})

test('keeps a manual category across "Atualizar agora" and goes back to the automatic one', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.goto('/app/expenses?month=2026-08')
  const row = page.getByRole('listitem').filter({ hasText: 'FARMACIA CENTRAL' })
  await expect(row).toContainText('Plano de saúde')

  await row.getByRole('button', { name: 'Trocar categoria de FARMACIA CENTRAL' }).click()
  await row
    .getByRole('combobox', { name: 'Categoria de FARMACIA CENTRAL' })
    .selectOption({ label: 'Supermercado' })

  await expect(row).toContainText('Supermercado')
  await expect(row.getByText('manual', { exact: true })).toBeVisible()
  const table = page.getByRole('table', { name: 'Por categoria' })
  await expect(table.getByRole('row')).toHaveCount(2)
  await expect(table.getByRole('row').nth(1)).toContainText('Supermercado')
  await expect(table.getByRole('row').nth(1)).toContainText('2 gastos')
  await expect(table.getByRole('row').nth(1)).toContainText('R$ 105,00')
  await expect(page.getByText('Plano de saúde')).toHaveCount(0)

  await page.goto('/app/')
  await page.getByRole('button', { name: 'Atualizar agora' }).click()
  await expect(page.getByText('Terminou sem erro')).toBeVisible()

  await page.goto('/app/expenses?month=2026-08')
  await expect(row).toContainText('Supermercado')
  await expect(row.getByText('manual', { exact: true })).toBeVisible()

  await row.getByRole('button', { name: 'Trocar categoria de FARMACIA CENTRAL' }).click()
  await row
    .getByRole('combobox', { name: 'Categoria de FARMACIA CENTRAL' })
    .selectOption({ label: 'Voltar para a automática' })

  await expect(row).toContainText('Plano de saúde')
  await expect(row.getByText('manual', { exact: true })).toHaveCount(0)

  await page.reload()
  await expect(row).toContainText('Plano de saúde')
  await expect(table.getByRole('row')).toHaveCount(3)
  await expect(table.getByRole('row').nth(1)).toContainText('Supermercado')
  await expect(table.getByRole('row').nth(1)).toContainText('1 gasto')
  await expect(table.getByRole('row').nth(1)).toContainText('R$ 60,00')
  await expect(table.getByRole('row').nth(2)).toContainText('Plano de saúde')
  await expect(table.getByRole('row').nth(2)).toContainText('R$ 45,00')
})
