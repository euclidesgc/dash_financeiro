import { expect, test } from '@playwright/test'

const LOGIN = 'e2e'
const PASSWORD = 'senha-e2e-9k2'

// Reason: both tests share the same real backend session flow, and
// sync.spec.ts writes into the same shared e2e SQLite database that this
// spec reads from; running specs across workers in parallel could race.
test.describe.configure({ mode: 'serial' })

test('opens the expenses page and lists only the spending', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Gastos' }).click()
  await expect(page).toHaveURL(/\/app\/expenses$/)

  await expect(page.getByRole('heading', { level: 1, name: 'Gastos' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Gastos' })).toHaveAttribute('aria-current', 'page')

  const item = page.getByRole('listitem').filter({ hasText: 'MERCADO DO BAIRRO' })
  await expect(item).toBeVisible()
  await expect(item).toContainText('02/09/2026')
  await expect(item).toContainText('-R$ 84,90')

  await expect(page.getByText('TED PARA POUPANCA')).toHaveCount(0)
  await expect(page.getByText('SALARIO')).toHaveCount(0)

  await expect(page.getByText('Página 1 de 1 · 5 gastos')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Anterior', exact: true })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Próxima' })).toBeDisabled()
})

test('reorders the expenses by amount and by category and keeps the order on reload', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Gastos' }).click()
  await expect(page).toHaveURL(/\/app\/expenses$/)

  const orderButton = page.getByRole('button', { name: 'Inverter direção da ordenação' })

  await expect(page.getByRole('listitem').first()).toContainText('MERCADO DO BAIRRO')
  await expect(page.getByLabel('Ordenar por')).toHaveValue('date')
  await expect(orderButton).toHaveText('Decrescente')

  await page.getByLabel('Ordenar por').selectOption('amount')
  await expect(page).toHaveURL(/sort=amount/)
  await expect(page.getByRole('listitem').first()).toContainText('POSTO CENTRAL')
  await expect(page.getByRole('listitem').first()).toContainText('-R$ 150,00')

  await orderButton.click()
  await expect(page).toHaveURL(/order=asc/)
  await expect(orderButton).toHaveText('Crescente')
  await expect(page.getByRole('listitem').first()).not.toContainText('POSTO CENTRAL')
  await expect(page.getByRole('listitem').last()).toContainText('POSTO CENTRAL')

  await page.reload()
  await expect(page.getByLabel('Ordenar por')).toHaveValue('amount')
  await expect(orderButton).toHaveText('Crescente')
  await expect(page.getByRole('listitem').last()).toContainText('POSTO CENTRAL')
  await expect(page).toHaveURL(/sort=amount/)

  await page.getByLabel('Ordenar por').selectOption('category')
  await expect(page).toHaveURL(/sort=category/)
  await expect(page.getByRole('listitem').first()).toContainText('POSTO CENTRAL')
  await expect(page.getByRole('listitem').first()).toContainText('Casa')

  await page.getByLabel('Ordenar por').selectOption('date')
  await expect(page).not.toHaveURL(/sort=/)
  await expect(page.getByRole('listitem').first()).toContainText('MERCADO DO BAIRRO')
})

test('filters the expenses by month and by date range and keeps the period on reload', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Gastos' }).click()
  await expect(page).toHaveURL(/\/app\/expenses$/)

  await expect(page.getByText('Página 1 de 1 · 5 gastos · R$ 369,90 no período')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Todo o período' })).toBeDisabled()

  await page.goto('/app/expenses?month=2026-10')
  await expect(page.getByText('Nenhum gasto para esse filtro.')).toBeVisible()
  await expect(page.getByText('outubro de 2026')).toBeVisible()

  await page.getByRole('button', { name: 'Mês anterior' }).click()
  await expect(page).toHaveURL(/month=2026-09/)
  await expect(page.getByText('setembro de 2026')).toBeVisible()
  await expect(page.getByRole('listitem')).toHaveCount(2)
  await expect(page.getByLabel('De', { exact: true })).toHaveValue('2026-09-01')
  await expect(page.getByLabel('Até', { exact: true })).toHaveValue('2026-09-30')

  await page.getByLabel('De', { exact: true }).fill('2026-09-02')
  await expect(page).toHaveURL(/from=2026-09-02/)
  await expect(page).not.toHaveURL(/month=/)

  await page.getByLabel('Até', { exact: true }).fill('2026-09-02')
  await expect(page).toHaveURL(/to=2026-09-02/)
  await expect(page.getByRole('listitem')).toHaveCount(1)
  await expect(page.getByRole('listitem')).toContainText('MERCADO DO BAIRRO')
  await expect(page.getByText('Período personalizado')).toBeVisible()
  await expect(page.getByText('Página 1 de 1 · 1 gasto · R$ 84,90 no período')).toBeVisible()

  await page.reload()
  await expect(page.getByRole('listitem')).toHaveCount(1)
  await expect(page.getByRole('listitem')).toContainText('MERCADO DO BAIRRO')
  await expect(page.getByLabel('De', { exact: true })).toHaveValue('2026-09-02')
  await expect(page.getByLabel('Até', { exact: true })).toHaveValue('2026-09-02')

  await page.getByRole('button', { name: 'Todo o período' }).click()
  await expect(page).not.toHaveURL(/from=/)
  await expect(page.getByRole('button', { name: 'Todo o período' })).toBeDisabled()
  await expect
    .poll(async () => page.getByRole('listitem').count())
    .toBeGreaterThanOrEqual(2)
})

test('filters the expenses by account and keeps the account on reload', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Gastos' }).click()
  await expect(page).toHaveURL(/\/app\/expenses$/)

  const accountSelect = page.getByLabel('Conta', { exact: true })
  await expect(accountSelect).toHaveValue('')

  await accountSelect.selectOption({ label: 'Cartão de teste · Emissor de teste (Cartão)' })
  await expect(page).toHaveURL(/account=acc-fixture-2/)
  const items = page.getByRole('listitem')
  await expect(items).toHaveCount(1)
  await expect(items).toContainText('FARMACIA CENTRAL')
  await expect(items).toContainText('-R$ 45,00')
  await expect(page.getByText('Página 1 de 1 · 1 gasto · R$ 45,00 no período')).toBeVisible()

  await page.reload()
  await expect(page.getByRole('listitem')).toHaveCount(1)
  await expect(page.getByRole('listitem')).toContainText('FARMACIA CENTRAL')
  await expect(accountSelect).toHaveValue('acc-fixture-2')

  await page.goto('/app/expenses?account=acc-fixture-2&month=2026-09')
  await expect(page.getByText('Nenhum gasto para esse filtro.')).toBeVisible()

  await page.getByRole('button', { name: 'Todo o período' }).click()
  await expect(page).not.toHaveURL(/month=/)
  await expect(page).toHaveURL(/account=acc-fixture-2/)
  await expect(page.getByRole('listitem')).toHaveCount(1)

  await accountSelect.selectOption({ label: 'Todas as contas' })
  await expect(page).not.toHaveURL(/account=/)
  await expect.poll(() => page.getByRole('listitem').count()).toBeGreaterThanOrEqual(4)

  await page.goto('/app/expenses?account=nao-existe')
  await expect(page).not.toHaveURL(/account=/)
  await expect(accountSelect).toHaveValue('')
  await expect.poll(() => page.getByRole('listitem').count()).toBeGreaterThanOrEqual(4)
})

test('searches the expenses by text and keeps the search on reload', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Gastos' }).click()
  await expect(page).toHaveURL(/\/app\/expenses$/)

  const searchInput = page.getByLabel('Buscar')
  await expect(searchInput).toHaveValue('')
  await expect(page.getByRole('button', { name: 'Limpar busca' })).toHaveCount(0)

  await searchInput.fill('acougue')
  await expect(page).toHaveURL(/q=acougue/)
  const items = page.getByRole('listitem')
  await expect(items).toHaveCount(1)
  await expect(items).toContainText('AÇOUGUE SÃO JORGE')
  await expect(items).toContainText('-R$ 60,00')
  await expect(page.getByText('Página 1 de 1 · 1 gasto · R$ 60,00 no período')).toBeVisible()

  await page.reload()
  await expect(page.getByRole('listitem')).toHaveCount(1)
  await expect(page.getByRole('listitem')).toContainText('AÇOUGUE SÃO JORGE')
  await expect(searchInput).toHaveValue('acougue')

  await searchInput.fill('a')
  await expect(page).not.toHaveURL(/q=/)
  await expect.poll(() => page.getByRole('listitem').count()).toBeGreaterThanOrEqual(4)

  await searchInput.fill('mercado')
  await searchInput.press('Enter')
  await expect(page).toHaveURL(/q=mercado/)
  await expect(page.getByRole('listitem')).toHaveCount(1)
  await expect(page.getByRole('listitem')).toContainText('MERCADO DO BAIRRO')

  await page.getByRole('button', { name: 'Limpar busca' }).click()
  await expect(page).not.toHaveURL(/q=/)
  await expect(searchInput).toHaveValue('')
  await expect.poll(() => page.getByRole('listitem').count()).toBeGreaterThanOrEqual(4)

  await page.goto('/app/expenses?q=mercado&month=2026-08')
  await expect(page.getByText('Nenhum gasto para esse filtro.')).toBeVisible()
  await expect(searchInput).toHaveValue('mercado')

  await page.getByRole('button', { name: 'Todo o período' }).click()
  await expect(page).not.toHaveURL(/month=/)
  await expect(page).toHaveURL(/q=mercado/)
  await expect(page.getByRole('listitem')).toHaveCount(1)
})

test('shows the totals by category and hides them when the filter has no spending', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.goto('/app/expenses?month=2026-08')
  await expect(page.getByRole('heading', { level: 2, name: 'Por categoria' })).toBeVisible()

  const table = page.getByRole('table', { name: 'Por categoria' })
  const rows = table.getByRole('row')
  await expect(rows).toHaveCount(3)
  await expect(rows.nth(1)).toContainText('Supermercado')
  await expect(rows.nth(1)).toContainText('1 gasto')
  await expect(rows.nth(1)).toContainText('R$ 60,00')
  await expect(rows.nth(2)).toContainText('Plano de saúde')
  await expect(rows.nth(2)).toContainText('R$ 45,00')
  await expect(page.getByRole('button', { name: /Mostrar todas/ })).toHaveCount(0)
  await expect(page.getByRole('listitem')).toHaveCount(2)

  await page.goto('/app/expenses?q=zzzz')
  await expect(page.getByRole('heading', { level: 2, name: 'Por categoria' })).toHaveCount(0)
  await expect(page.getByRole('table')).toHaveCount(0)
  await expect(page.getByText('Nenhum gasto para esse filtro.')).toBeVisible()
})

test('shows the signal of each category against its limit only in a whole month and leaves the base as it found it', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Categorias' }).click()
  const supermercado = page.getByRole('listitem').filter({ has: page.getByText('Supermercado', { exact: true }) })
  await expect(supermercado).toContainText('Sem limite')
  await supermercado.getByRole('button', { name: 'Definir limite de Supermercado' }).click()
  await supermercado.getByLabel('Limite mensal (R$)').fill('50')
  await supermercado.getByLabel('Limite mensal (R$)').press('Enter')
  await expect(supermercado).toContainText('Limite: R$ 50,00')

  await page.goto('/app/expenses?month=2026-08')
  const table = page.getByRole('table', { name: 'Por categoria' })
  const groceries = table.getByRole('row').filter({ hasText: 'Supermercado' })
  await expect(groceries).toContainText('Acima')
  await expect(groceries).toContainText('R$ 60,00 de R$ 50,00 · 120%')
  await expect(page.getByText('1 categoria acima do limite', { exact: true })).toBeVisible()
  const health = table.getByRole('row').filter({ hasText: 'Plano de saúde' })
  await expect(health).not.toContainText('Dentro')
  await expect(health).not.toContainText('Atenção')
  await expect(health).not.toContainText('Acima')
  await expect(page.getByText('Sinal só por mês', { exact: true })).toHaveCount(0)

  await page.goto('/app/expenses?from=2026-08-01&to=2026-08-20')
  await expect(page.getByText('Sinal só por mês', { exact: true })).toBeVisible()
  await expect(page.getByRole('table', { name: 'Por categoria' })).not.toContainText('Acima')
  await expect(page.getByText(/acima do limite/)).toHaveCount(0)

  await page.getByRole('link', { name: 'Categorias' }).click()
  await supermercado.getByRole('button', { name: 'Definir limite de Supermercado' }).click()
  await supermercado.getByLabel('Limite mensal (R$)').fill('')
  await supermercado.getByLabel('Limite mensal (R$)').press('Enter')
  await expect(supermercado).toContainText('Sem limite')

  await page.goto('/app/expenses?month=2026-08')
  await expect(page.getByRole('table', { name: 'Por categoria' })).toBeVisible()
  await expect(page.getByRole('table', { name: 'Por categoria' })).not.toContainText('Acima')
  await expect(page.getByText(/acima do limite/)).toHaveCount(0)
  await expect(page.getByText('Sinal só por mês', { exact: true })).toHaveCount(0)
})

test('shows the month against its ceiling, edits the ceiling inline and leaves the base as it found it', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.goto('/app/expenses?month=2026-08')
  const block = page.getByRole('region', { name: 'Teto do mês' })
  await expect(page.getByRole('heading', { level: 2, name: 'Teto do mês' })).toBeVisible()
  await expect(block).toContainText('Sem teto definido.')
  const field = block.getByLabel('Teto mensal (R$)')
  await expect(field).toBeFocused()

  await field.fill('100')
  await field.press('Enter')
  await expect(block).toContainText('R$ 105,00 de R$ 100,00 · 105%')
  await expect(block.getByText('Acima', { exact: true })).toBeVisible()
  await expect(block).toContainText('Passou R$ 5,00')
  await expect(block.getByLabel('Teto mensal (R$)')).toHaveCount(0)

  await block.getByRole('button', { name: 'Definir teto do mês' }).click()
  await expect(block.getByLabel('Teto mensal (R$)')).toHaveValue('100.00')
  await block.getByLabel('Teto mensal (R$)').fill('200')
  await block.getByLabel('Teto mensal (R$)').press('Enter')
  await expect(block).toContainText('R$ 105,00 de R$ 200,00 · 53%')
  await expect(block.getByText('Dentro', { exact: true })).toBeVisible()
  await expect(block).toContainText('Sobram R$ 95,00')

  await page.reload()
  await expect(page.getByRole('region', { name: 'Teto do mês' })).toContainText(
    'R$ 105,00 de R$ 200,00 · 53%',
  )

  await page.goto('/app/expenses?from=2026-08-01&to=2026-08-20')
  await expect(page.getByRole('heading', { level: 2, name: 'Por categoria' })).toBeVisible()
  await expect(page.getByRole('heading', { level: 2, name: 'Teto do mês' })).toHaveCount(0)

  await page.goto('/app/expenses?month=2026-08')
  await block.getByRole('button', { name: 'Definir teto do mês' }).click()
  await block.getByLabel('Teto mensal (R$)').fill('')
  await block.getByLabel('Teto mensal (R$)').press('Enter')
  await expect(block).toContainText('Sem teto definido.')
  await expect(block).not.toContainText('%')
})

test('marks an expense as not an expense, undoes it, lists it under "Não são gastos" and leaves the base as it found it', async ({
  page,
}) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.goto('/app/expenses?month=2026-08')
  await expect(page.getByText('Página 1 de 1 · 2 gastos · R$ 105,00 no período')).toBeVisible()
  const row = page.getByRole('listitem').filter({ hasText: 'AÇOUGUE SÃO JORGE' })

  await row.getByRole('button', { name: 'Marcar AÇOUGUE SÃO JORGE como não-gasto' }).click()
  const reason = row.getByLabel('Motivo')
  await expect(reason).toBeFocused()
  await expect(reason).toHaveValue('own_transfer')
  await row.getByRole('button', { name: 'Confirmar' }).click()

  const notice = page
    .getByRole('status')
    .filter({ hasText: 'AÇOUGUE SÃO JORGE não conta mais como gasto.' })
  await expect(notice).toBeVisible()
  await expect(page.getByRole('listitem')).toHaveCount(1)
  await expect(page.getByText('Página 1 de 1 · 1 gasto · R$ 45,00 no período')).toBeVisible()
  await expect(page.getByRole('table', { name: 'Por categoria' })).not.toContainText('Supermercado')

  await notice.getByRole('button', { name: 'Desfazer' }).click()
  await expect(notice).toHaveCount(0)
  await expect(page.getByText('Página 1 de 1 · 2 gastos · R$ 105,00 no período')).toBeVisible()
  await expect(row).toBeVisible()

  await row.getByRole('button', { name: 'Marcar AÇOUGUE SÃO JORGE como não-gasto' }).click()
  await expect(reason).toBeFocused()
  await expect(reason).toHaveValue('own_transfer')
  await row.getByRole('button', { name: 'Confirmar' }).click()
  await expect(page.getByText('Página 1 de 1 · 1 gasto · R$ 45,00 no período')).toBeVisible()

  await page.getByLabel('Mostrar').selectOption('excluded')
  await expect(page).toHaveURL(/view=excluded/)
  await expect(page.getByRole('listitem')).toHaveCount(1)
  await expect(page.getByRole('listitem')).toContainText('AÇOUGUE SÃO JORGE')
  await expect(
    page.getByRole('listitem').getByText('Transferência entre minhas contas', { exact: true }),
  ).toBeVisible()
  await expect(page.getByText('Página 1 de 1 · 1 lançamento · R$ 60,00 no período')).toBeVisible()
  await expect(page.getByRole('heading', { level: 2, name: 'Teto do mês' })).toHaveCount(0)

  await page.reload()
  await expect(page.getByLabel('Mostrar')).toHaveValue('excluded')
  await expect(page.getByRole('listitem')).toHaveCount(1)

  await page.getByRole('button', { name: 'Voltar AÇOUGUE SÃO JORGE a ser gasto' }).click()
  await expect(page.getByText('Nenhum lançamento marcado como não-gasto.')).toBeVisible()

  await page.getByLabel('Mostrar').selectOption('expenses')
  await expect(page).not.toHaveURL(/view=/)
  await expect(page.getByText('Página 1 de 1 · 2 gastos · R$ 105,00 no período')).toBeVisible()
})

test('goes back to the balances page', async ({ page }) => {
  await page.goto('/app/login')
  await page.getByLabel('Login').fill(LOGIN)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/app\/?$/)

  await page.getByRole('link', { name: 'Gastos' }).click()
  await expect(page).toHaveURL(/\/app\/expenses$/)

  await page.getByRole('link', { name: 'Saldos' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Saldos de hoje' })).toBeVisible()
  await expect(page).toHaveURL(/\/app\/?$/)
})
