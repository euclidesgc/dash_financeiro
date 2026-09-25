import { expect, test, type Page } from '@playwright/test'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'
const PHONE = { width: 375, height: 812 }

async function elementsPastTheRightEdge(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const limit = document.documentElement.clientWidth
    return Array.from(document.body.querySelectorAll('*'))
      .filter((element) => {
        const box = element.getBoundingClientRect()
        return box.width > 0 && box.height > 0 && box.right > limit + 0.5
      })
      .map((element) => {
        const text = (element.textContent ?? '').trim().slice(0, 30)
        return `${element.tagName.toLowerCase()} "${text}"`
      })
  })
}

async function expectNoHorizontalScroll(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle')
  const widths = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth,
  }))
  expect(widths.scroll).toBeLessThanOrEqual(widths.viewport)
  expect(await elementsPastTheRightEdge(page)).toEqual([])
}

test('every screen fits a 375 px phone without horizontal scroll', async ({ page }) => {
  await page.setViewportSize(PHONE)

  await page.goto('/app/login')
  await expect(page.getByRole('heading', { level: 1, name: 'Entrar' })).toBeVisible()
  await expectNoHorizontalScroll(page)

  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Saldos de hoje' })).toBeVisible()
  await expect(page.getByText('Conta de teste')).toBeVisible()
  await expectNoHorizontalScroll(page)

  const navigation = page.getByRole('navigation', { name: 'Principal' })
  for (const name of ['Saldos', 'Gastos', 'Categorias', 'Conexões']) {
    await expect(navigation.getByRole('link', { name })).toBeInViewport({ ratio: 1 })
  }

  const screens = [
    { link: 'Gastos', heading: 'Gastos' },
    { link: 'Categorias', heading: 'Categorias' },
    { link: 'Conexões', heading: 'Conexões' },
  ]
  for (const screen of screens) {
    await navigation.getByRole('link', { name: screen.link }).click()
    await expect(page.getByRole('heading', { level: 1, name: screen.heading })).toBeVisible()
    await expectNoHorizontalScroll(page)
  }

  await page.goto('/app/nao-existe')
  await expect(page.getByRole('heading', { level: 1, name: 'Página não encontrada' })).toBeVisible()
  await expectNoHorizontalScroll(page)
})
