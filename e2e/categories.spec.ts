import { expect, test } from '@playwright/test'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'

// Reason: this spec writes categories and a manual category into the same
// shared e2e SQLite database that expenses.spec.ts and sync.spec.ts read
// from; running specs across workers in parallel could race.
test.describe.configure({ mode: 'serial' })

test('creates, uses, renames and deletes a category and leaves the base as it found it', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)
  await page.getByRole('link', { name: 'Categorias' }).click()
  await expect(page).toHaveURL(/\/app\/categories$/)
  await expect(page.getByRole('heading', { level: 1, name: 'Categorias' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Categorias' })).toHaveAttribute(
    'aria-current',
    'page',
  )

  const supermercado = page
    .getByRole('listitem')
    .filter({ has: page.getByText('Supermercado', { exact: true }) })
  await expect(supermercado).toContainText('Do sistema')
  await expect(supermercado.getByRole('button', { name: 'Apagar Supermercado' })).toHaveCount(0)

  await page.getByLabel('Nome da categoria').fill('Pet shop')
  await page.getByRole('button', { name: 'Criar categoria' }).click()
  const petShop = page
    .getByRole('listitem')
    .filter({ has: page.getByText('Pet shop', { exact: true }) })
  await expect(petShop).toBeVisible()
  await expect(petShop).toContainText('Criada por você')
  await expect(petShop).toContainText('Nenhum gasto')
  await expect(page.getByLabel('Nome da categoria')).toHaveValue('')

  await page.getByLabel('Nome da categoria').fill('pet shop')
  await page.getByRole('button', { name: 'Criar categoria' }).click()
  await expect(page.getByText('Já existe uma categoria com esse nome.')).toBeVisible()
  await expect(page.getByLabel('Nome da categoria')).toHaveValue('pet shop')

  await page.goto('/app/expenses?month=2026-08')
  const row = page.getByRole('listitem').filter({ hasText: 'FARMACIA CENTRAL' })
  await row.getByRole('button', { name: 'Trocar categoria de FARMACIA CENTRAL' }).click()
  await row
    .getByRole('combobox', { name: 'Categoria de FARMACIA CENTRAL' })
    .selectOption({ label: 'Pet shop' })
  await expect(row).toContainText('Pet shop')

  await page.getByRole('link', { name: 'Categorias' }).click()
  await expect(petShop).toContainText('1 gasto')
  await petShop.getByRole('button', { name: 'Apagar Pet shop' }).click()
  await expect(petShop.getByRole('alert')).toContainText('Esta categoria está em uso por 1 gasto.')
  await petShop.getByRole('button', { name: 'Fechar' }).click()

  await petShop.getByRole('button', { name: 'Renomear Pet shop' }).click()
  await expect(petShop.getByLabel('Novo nome')).toHaveValue('Pet shop')
  await petShop.getByLabel('Novo nome').fill('Bicho')
  await petShop.getByRole('button', { name: 'Salvar' }).click()
  const bicho = page.getByRole('listitem').filter({ has: page.getByText('Bicho', { exact: true }) })
  await expect(bicho).toBeVisible()
  await expect(page.getByText('Pet shop', { exact: true })).toHaveCount(0)

  await page.goto('/app/expenses?month=2026-08')
  await expect(row).toContainText('Bicho')
  await row.getByRole('button', { name: 'Trocar categoria de FARMACIA CENTRAL' }).click()
  await row
    .getByRole('combobox', { name: 'Categoria de FARMACIA CENTRAL' })
    .selectOption({ label: 'Voltar para a automática' })
  await expect(row).toContainText('Plano de saúde')
  await expect(row.getByText('manual', { exact: true })).toHaveCount(0)

  await page.getByRole('link', { name: 'Categorias' }).click()
  await expect(bicho).toContainText('Nenhum gasto')
  await bicho.getByRole('button', { name: 'Apagar Bicho' }).click()
  await expect(bicho.getByText('Apagar a categoria “Bicho”?')).toBeVisible()
  await bicho.getByRole('button', { name: 'Confirmar' }).click()
  await expect(bicho).toHaveCount(0)
  await page.reload()
  await expect(page.getByRole('heading', { level: 2, name: 'Catálogo' })).toBeVisible()
  await expect(page.getByText('Bicho', { exact: true })).toHaveCount(0)
})
