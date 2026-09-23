import { expect, test } from '@playwright/test'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'

// Reason: this spec writes manual categories into the same shared e2e SQLite
// database that expenses.spec.ts and sync.spec.ts read from; running specs
// across workers in parallel could race.
test.describe.configure({ mode: 'serial' })

test('applies the category to the similar expenses and leaves the base as it found it', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.goto('/app/expenses?month=2026-08')
  const august = page.getByRole('listitem').filter({ hasText: 'FARMACIA CENTRAL' })
  await expect(august).toHaveCount(1)
  await expect(august).toContainText('Plano de saúde')

  await august.getByRole('button', { name: 'Trocar categoria de FARMACIA CENTRAL' }).click()
  await august
    .getByRole('combobox', { name: 'Categoria de FARMACIA CENTRAL' })
    .selectOption({ label: 'Supermercado' })
  await expect(august).toContainText('Supermercado')
  await expect(august.getByText('Aplicar a 1 gasto parecido')).toBeVisible()
  await expect(august.getByRole('button', { name: 'Agora não' })).toBeVisible()

  await august.getByRole('button', { name: 'Aplicar', exact: true }).click()
  await expect(august.getByText('Categoria aplicada a 1 gasto')).toBeVisible()
  await expect(august.getByRole('button', { name: 'Aplicar', exact: true })).toHaveCount(0)

  await page.getByRole('button', { name: 'Todo o período' }).click()
  await expect(page).not.toHaveURL(/month=/)
  const july = page.getByRole('listitem').filter({ hasText: '08/07/2026' })
  await expect(july).toContainText('FARMACIA CENTRAL')
  await expect(july).toContainText('Supermercado')
  await expect(july.getByText('manual', { exact: true })).toBeVisible()

  await page.reload()
  await expect(july).toContainText('Supermercado')
  await expect(july.getByText('manual', { exact: true })).toBeVisible()

  await july.getByRole('button', { name: 'Trocar categoria de FARMACIA CENTRAL' }).click()
  await july
    .getByRole('combobox', { name: 'Categoria de FARMACIA CENTRAL' })
    .selectOption({ label: 'Voltar para a automática' })
  await expect(july).toContainText('Plano de saúde')
  await expect(july.getByText('manual', { exact: true })).toHaveCount(0)

  const augustAll = page.getByRole('listitem').filter({ hasText: '15/08/2026' })
  await augustAll.getByRole('button', { name: 'Trocar categoria de FARMACIA CENTRAL' }).click()
  await augustAll
    .getByRole('combobox', { name: 'Categoria de FARMACIA CENTRAL' })
    .selectOption({ label: 'Voltar para a automática' })
  await expect(augustAll).toContainText('Plano de saúde')
  await expect(augustAll.getByText('manual', { exact: true })).toHaveCount(0)

  await page.reload()
  await expect(page.getByText('manual', { exact: true })).toHaveCount(0)
  await expect(page.getByText('Página 1 de 1 · 5 gastos · R$ 369,90 no período')).toBeVisible()
})
