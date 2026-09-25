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

test('a session that ends while the app is open goes to the login page and stays there', async ({
  page,
}) => {
  await page.clock.install()
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Saldos de hoje' })).toBeVisible()

  const loggedOut = await page.request.post('/api/auth/logout')
  expect(loggedOut.ok()).toBe(true)
  await page.clock.fastForward('01:00')

  const visited: string[] = []
  page.on('framenavigated', (frame) => {
    if (frame === page.mainFrame()) visited.push(new URL(frame.url()).pathname)
  })
  await page.getByRole('link', { name: 'Gastos' }).click()

  await expect(page.getByRole('heading', { level: 1, name: 'Entrar' })).toBeVisible()
  await page.clock.fastForward('00:05')
  await expect(page).toHaveURL(/\/app\/login$/)
  expect(visited.filter((path) => path === '/app/').length).toBe(0)

  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Saldos de hoje' })).toBeVisible()
})

test('a session that ends while the user moves between screens goes to the login page', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Saldos de hoje' })).toBeVisible()

  const loggedOut = await page.request.post('/api/auth/logout')
  expect(loggedOut.ok()).toBe(true)

  await page.getByRole('link', { name: 'Gastos' }).click()

  await expect(page.getByRole('heading', { level: 1, name: 'Entrar' })).toBeVisible()
  await expect(page).toHaveURL(/\/app\/login$/)
})

test('opens the app without the trailing slash and shows a Portuguese page for an unknown path', async ({
  page,
}) => {
  await page.goto('/app')
  await expect(page.getByRole('heading', { level: 1, name: 'Entrar' })).toBeVisible()

  await page.goto('/app/nao-existe')
  await expect(page.getByRole('heading', { level: 1, name: 'Página não encontrada' })).toBeVisible()
  await expect(page.getByText('Unexpected Application Error')).toHaveCount(0)

  await page.getByRole('link', { name: 'Voltar para o início' }).click()
  await expect(page).toHaveURL(/\/app\/login$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Entrar' })).toBeVisible()
})
