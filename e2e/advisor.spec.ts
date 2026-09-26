import { expect, test } from '@playwright/test'

import { restoreSeededBase } from './restore-seeded-base'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'
const QUESTION = 'quanto gastei com farmácia?'
const ANSWER = 'Encontrei 2 lançamentos com farmácia, somando −R$ 75,00.'

test.describe.configure({ mode: 'serial' })

test.beforeEach(() => {
  restoreSeededBase()
})

test.afterEach(() => {
  restoreSeededBase()
})

test('asks the advisor, gets the tool numbers and finds the conversation again', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page
    .getByRole('navigation', { name: 'Principal' })
    .getByRole('link', { name: 'Consultor', exact: true })
    .click()
  await expect(page).toHaveURL(/\/app\/advisor$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Consultor' })).toBeVisible()
  await expect(page.getByText(/Pergunte sobre seus gastos e entradas/)).toBeVisible()

  await page.getByLabel('Sua pergunta').fill(QUESTION)
  await page.getByRole('button', { name: 'Perguntar' }).click()

  await expect(page.getByText(ANSWER)).toBeVisible()
  await expect(page.getByText('Respondido por Anthropic · consultou seus lançamentos')).toBeVisible()
  await expect(page).toHaveURL(/\/app\/advisor\?c=\d+$/)

  await page.goto('/app/advisor')
  await expect(page.getByText(ANSWER)).toBeVisible()
  await expect(page.getByText(QUESTION)).toBeVisible()

  await page.getByRole('button', { name: 'Nova conversa' }).click()
  await expect(page.getByText(ANSWER)).toHaveCount(0)
})
