import { expect, test } from '@playwright/test'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'

test('the balances page shows the month plan and links to the month expenses', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Saldos de hoje' })).toBeVisible()

  const card = page.getByRole('region', { name: /^Plano de / })
  await expect(card).toBeVisible()
  await expect(card.getByText('Gasto no mês', { exact: true })).toBeVisible()
  await expect(card.getByText('Teto do mês', { exact: true })).toBeVisible()
  await expect(card.getByText('Resultado até hoje', { exact: true })).toBeVisible()

  await card.getByRole('link').click()
  await expect(page).toHaveURL(/\/app\/expenses\?month=\d{4}-\d{2}$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Gastos' })).toBeVisible()
})
