# Roadmap atualizado

Uma única página web, com todas as contas. Cada linha é uma fatia utilizável sozinha; a primeira
prova o caminho de ponta a ponta (tela React → API FastAPI → SQLite) e as outras crescem sobre ela.

| # | Fatia | O usuário consegue… | Origem | Depende de | Status |
|---|---|---|---|---|---|
| 001 | `login-e-saldos` | entrar no painel e ver o saldo de hoje de cada conta | Pedido de 22/09 | — | done |
| 002 | `atualizar-registros` | apertar um botão e ter todos os registros bancários atualizados na base, vendo quando foi a última atualização | Pedido de 22/09 | 001 | done |
| 003 | `lista-de-gastos` | ver uma lista paginada com todos os gastos de todas as contas | Pedido de 22/09 | 001 | done |
| 004 | `ordenar-gastos` | ordenar os gastos por data, valor ou categoria | Pedido de 22/09 | 003 | done |
| 005 | `filtrar-por-periodo` | filtrar os gastos por período (mês, intervalo de datas) | Pedido de 22/09 | 003 | done |
| 006 | `filtrar-por-conta` | filtrar os gastos por banco ou conta | Pedido de 22/09 | 003 | done |
| 007 | `buscar-por-texto` | encontrar gastos pela descrição ou pelo nome de quem recebeu | Pedido de 22/09 | 003 | done |
| 008 | `total-por-categoria` | ver os gastos do período agrupados por categoria, com o total de cada uma | Pedido de 22/09 | 005 | done |
| 009 | `ajustar-categoria` | trocar a categoria de um gasto, e a troca sobreviver à próxima atualização | Pedido de 22/09 | 003 | done |
| 010 | `criar-categoria` | criar, renomear e apagar categorias | Pedido de 22/09 | 009 | done |
| 011 | `categoria-para-parecidos` | aplicar a mesma categoria a todos os gastos parecidos de uma vez | Pedido de 22/09 | 009 | done |
| 012 | `limite-por-categoria` | definir um limite mensal para cada categoria | Pedido de 22/09 | 010 | done |
| 013 | `sinal-por-categoria` | ver, em cada categoria, se está dentro, acima ou abaixo do limite no período | Pedido de 22/09 | 008, 012 | done |
| 014 | `sinal-do-mes` | ver se o total do mês está dentro, acima ou abaixo do teto do plano de recuperação | Pedido de 22/09 | 005 | done |
| 015 | `marcar-nao-gasto` | tirar dos totais um lançamento que não é gasto (transferência entre contas próprias, estorno) | Pedido de 22/09 | 003 | done |
| 016 | `entradas` | ver as entradas (salário e outras receitas) separadas dos gastos, no mesmo período | Pedido de 22/09 | 005 | done |

## Dívidas técnicas

| # | Fatia | Resolução necessária | Origem | Depende de | Status |
|---|---|---|---|---|---|
| 017 | `jinja-router-extraction` | manter a lógica de consulta única quando uma tela migra de Jinja para React, em vez de reescrever SQL | bug | 001 | done |
| 018 | `sync-runs-source-field` | rastrear origem do disparo (tela vs comando diário) em `sync_runs.source` em vez de só guardar o caminho do arquivo lido | 002 | — | done |
| 019 | `pluggy-extract-env-handling` | embrulhar leitura de `.env` e `SystemExit` em `ingestao/pluggy_extract.py` em função limpa, não chamar direto do serviço | 002 | — | done |
| 020 | `jinja-sync-button-exclusive-lock` | fazer o botão Jinja `/sincronizar` passar pela trava de execução única de `app/sync/exclusive.py` | 002 | — | done |
| 021 | `pluggy-connections-editable-ui` | mover lista de conexões Pluggy de `data/item_ids.txt` para tela editável (norma 26) | 002 | — | done |
| 022 | `setup-secrets-pluggy-credentials` | atualizar `docs/setup-secrets.md` para citar `PLUGGY_CLIENT_ID` e `PLUGGY_CLIENT_SECRET` | 002 | — | done |
| 023 | `category-labels-in-schema` | mover rótulo em pt-BR das categorias de `app/taxonomy/seed.json` para coluna `label` na tabela `categories`, de modo que SQL possa ordenar e filtrar por categoria em 004 e 006 | 003 | — | done |
| 024 | `payee-filling-at-ingest` | preencher `payee` na própria `ingest`, na transação da carga, para que toda base (sincronização, testes, e2e) nasça com recebedor; a classificação segue no pós-carga | 003 | — | done |
| 025 | `spending-filter-predicate-unification` | unificar predicado de data duplicado em `app/queries/spending.py` (`total_spending_cents`) e `app/queries/expenses.py` (`_where`) em `spending.py`, evitando divergência na soma por categoria (008) | 005 | — | done |
| 026 | `unify-payee-name-precedence` | consolidar precedência do nome do recebedor entre Python (`app/payees/names.py`, `_chosen`) e SQL (`app/queries/expenses.py`, `_PAYEE_NAME_SQL`), evitando divergência silenciosa se uma mudar | 007 | 025 | done |
| 027 | `expenses-list-mock-unification` | `filterForSpy` em `src/features/expenses/components/__tests__/expenses-list.test.tsx` duplica a lógica de filtro dos mocks; importar `filterExpenses` de `src/testing/mocks/handlers.ts` em vez de reinventar | 008 | — | done |
| 028 | `manual-category-classify-precedence` | o ajuste manual de categoria (`transactions.category_source = 'manual'`) não tem precedência sobre regras por descrição no agrupamento (`group_id`) usado pelas telas Jinja antigas (`app/taxonomy/classify.py`, `_match`); enquanto essas telas existirem, um gasto ajustado à mão pode aparecer em outro grupo nelas | 009 | — | done |
| 029 | `jinja-labels-from-schema` | `app/routers/spending.py` e `app/routers/rules.py` montam `LABELS` do seed no import e não veem rótulo renomeado nem categoria criada pelo dono; ler `categories` em requisição nas duas telas Jinja (e em `tests/test_gastos_screen.py`) | 010 | 010 | done |
| 030 | `shared-categories-query` | `src/features/expenses/api/get-categories.ts` e `src/features/categories/api/get-categories.ts` buscam `GET /api/categories` com a mesma chave `['categories']`; mover hook e tipo para `src/hooks/` e `src/types/` pela regra "usado por duas features → compartilhado" | 010 | 010 | in-review |
| 031 | `expense-count-label` | `pagination.tsx:19`, `category-totals.tsx:57` e `similar-offer.tsx` escrevem o plural de "gasto" cada um do seu jeito; um utilitário em `src/features/expenses/utils/` usado pelos três | 011 | — | planned |
| 032 | `e2e-seed-classifies` | o recebedor já nasce preenchido na carga, mas o seed de `scripts/e2e-backend.sh` não roda `classify_all`, então grupo, natureza e essencialidade ficam sem classificação automática; aplicar a classificação no seed | 011 | 024 | done |
| 033 | `income-predicate-unification` | unificar o predicado de "entrada" (receita) que está escrito à mão em `app/projection/forecast.py`, `app/projection/monthly.py` e `app/plan/objective.py` em `app/queries/spending.py` como `INCOME`, antes de 016, para evitar divergência entre plano e tela de entradas | 015 | — | done |
| 034 | `override-unnecessary-reclassify` | `app/taxonomy/override.py::_write` reclassifica tudo via `classify_all` mesmo quando a coluna escrita (`not_expense_reason`) não é lida pela classificação; remover custo desnecessário a cada marcação de não-gasto | 015 | — | planned |
| 035 | `mocks-spending-rule-duplication` | os mocks MSW em `src/testing/mocks/handlers.ts` (`matchesView`, `period-result`) duplicam a regra de entrada/gasto da API; se `app/queries/spending.py` mudar, os testes de componente continuam verdes com regra antiga | 016 | — | planned |
| 036 | `e2e-expenses-reload-flaky` | `e2e/expenses.spec.ts` ("filters the expenses by month and by date range and keeps the period on reload") falhou uma vez em 25/09 com 2 itens em vez de 1 depois do `page.reload()`, com a URL já em `from`/`to` do dia 02; passou na repetição. Achar por que a lista recarregada ignora o intervalo às vezes antes que o flake trave um PR | 017 | — | done |
| 037 | `e2e-suite-repeatable` | rodar `pnpm test:e2e --repeat-each=N` na suíte inteira para caçar teste instável; hoje a segunda volta de `e2e/sync.spec.ts` ("updates the records from the balances page") falha porque espera "Nunca atualizado" numa base que a primeira volta já sincronizou | 036 | — | done |
| 038 | `e2e-ceiling-reload-flaky` | `e2e/expenses.spec.ts` ("shows the month against its ceiling, edits the ceiling inline and leaves the base as it found it") falhou 1 vez em 40 execuções (duas rodadas de `--repeat-each=20`) em 25/09: depois do `page.reload()` a região "Teto do mês" não apareceu em 5 s. Como o teste só devolve o teto ao estado inicial no fim, a falha deixa o teto gravado e derruba todas as repetições seguintes; achar a causa e fazer a limpeza não depender do teste passar | 036 | — | done |
| 039 | `extract-script-reads-connections` | `ingestao/pluggy_extract.py` (`criar-item`, `status`, `extrair`) ainda lê e grava as conexões em `data/item_ids.txt`, que a atualização do painel não lê mais desde a 021; ler e gravar em `pluggy_connections` para o script manual e a tela não divergirem | 021 | 021 | done |
