import { expect, test } from '@playwright/test'

import { restoreSeededBase } from './restore-seeded-base'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'
const ITEM_ID = '3f2504e0-4f89-11d3-9a0c-0305e82c3301'

// Reason: this spec writes into the shared e2e SQLite database that the other
// specs read from; restoring the seed on both sides keeps them independent.
test.describe.configure({ mode: 'serial' })

test.beforeEach(() => {
  restoreSeededBase()
})

test.afterEach(() => {
  restoreSeededBase()
})

test('registers a Pluggy connection, keeps it on reload and removes it', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Conexões' }).click()
  await expect(page).toHaveURL(/\/app\/connections$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Conexões' })).toBeVisible()
  await expect(page.getByText(/Nenhuma conexão cadastrada\./)).toBeVisible()

  const field = page.getByLabel('Identificador da conexão')
  await field.fill('abc')
  await page.getByRole('button', { name: 'Cadastrar conexão' }).click()
  await expect(
    page.getByText('Informe um identificador de conexão da Pluggy (formato 8-4-4-4-12).'),
  ).toBeVisible()

  await field.fill(ITEM_ID.toUpperCase())
  await page.getByRole('button', { name: 'Cadastrar conexão' }).click()
  await expect(page.getByText(ITEM_ID, { exact: true })).toBeVisible()
  await expect(field).toHaveValue('')

  await page.reload()
  await expect(page.getByText(ITEM_ID, { exact: true })).toBeVisible()

  await field.fill(ITEM_ID)
  await page.getByRole('button', { name: 'Cadastrar conexão' }).click()
  await expect(page.getByText('Essa conexão já está cadastrada.')).toBeVisible()

  await page.getByRole('button', { name: `Remover a conexão ${ITEM_ID}` }).click()
  await page.getByRole('button', { name: 'Confirmar' }).click()
  await expect(page.getByText(/Nenhuma conexão cadastrada\./)).toBeVisible()

  await page.reload()
  await expect(page.getByText(/Nenhuma conexão cadastrada\./)).toBeVisible()
})
