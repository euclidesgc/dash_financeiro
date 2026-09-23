# Roadmap atualizado

Uma única página web, com todas as contas. Cada linha é uma fatia utilizável sozinha; a primeira
prova o caminho de ponta a ponta (tela React → API FastAPI → SQLite) e as outras crescem sobre ela.

| # | Fatia | O usuário consegue… | Origem | Depende de | Status |
|---|---|---|---|---|---|
| 001 | `login-e-saldos` | entrar no painel e ver o saldo de hoje de cada conta | Pedido de 22/09 | — | in-review |
| 002 | `atualizar-registros` | apertar um botão e ter todos os registros bancários atualizados na base, vendo quando foi a última atualização | Pedido de 22/09 | 001 | in-review |
| 003 | `lista-de-gastos` | ver uma lista paginada com todos os gastos de todas as contas | Pedido de 22/09 | 001 | in-review |
| 004 | `ordenar-gastos` | ordenar os gastos por data, valor ou categoria | Pedido de 22/09 | 003 | in-review |
| 005 | `filtrar-por-periodo` | filtrar os gastos por período (mês, intervalo de datas) | Pedido de 22/09 | 003 | in-review |
| 006 | `filtrar-por-conta` | filtrar os gastos por banco ou conta | Pedido de 22/09 | 003 | in-review |
| 007 | `buscar-por-texto` | encontrar gastos pela descrição ou pelo nome de quem recebeu | Pedido de 22/09 | 003 | in-review |
| 008 | `total-por-categoria` | ver os gastos do período agrupados por categoria, com o total de cada uma | Pedido de 22/09 | 005 | planned |
| 009 | `ajustar-categoria` | trocar a categoria de um gasto, e a troca sobreviver à próxima atualização | Pedido de 22/09 | 003 | planned |
| 010 | `criar-categoria` | criar, renomear e apagar categorias | Pedido de 22/09 | 009 | planned |
| 011 | `categoria-para-parecidos` | aplicar a mesma categoria a todos os gastos parecidos de uma vez | Pedido de 22/09 | 009 | planned |
| 012 | `limite-por-categoria` | definir um limite mensal para cada categoria | Pedido de 22/09 | 010 | planned |
| 013 | `sinal-por-categoria` | ver, em cada categoria, se está dentro, acima ou abaixo do limite no período | Pedido de 22/09 | 008, 012 | planned |
| 014 | `sinal-do-mes` | ver se o total do mês está dentro, acima ou abaixo do teto do plano de recuperação | Pedido de 22/09 | 005 | planned |
| 015 | `marcar-nao-gasto` | tirar dos totais um lançamento que não é gasto (transferência entre contas próprias, estorno) | Pedido de 22/09 | 003 | planned |
| 016 | `entradas` | ver as entradas (salário e outras receitas) separadas dos gastos, no mesmo período | Pedido de 22/09 | 005 | planned |

## Dívidas técnicas

| # | Fatia | Resolução necessária | Origem | Depende de | Status |
|---|---|---|---|---|---|
| 017 | `jinja-router-extraction` | manter a lógica de consulta única quando uma tela migra de Jinja para React, em vez de reescrever SQL | bug | 001 | planned |
| 018 | `sync-runs-source-field` | rastrear origem do disparo (tela vs comando diário) em `sync_runs.source` em vez de só guardar o caminho do arquivo lido | 002 | — | planned |
| 019 | `pluggy-extract-env-handling` | embrulhar leitura de `.env` e `SystemExit` em `ingestao/pluggy_extract.py` em função limpa, não chamar direto do serviço | 002 | — | planned |
| 020 | `jinja-sync-button-exclusive-lock` | fazer o botão Jinja `/sincronizar` passar pela trava de execução única de `app/sync/exclusive.py` | 002 | — | planned |
| 021 | `pluggy-connections-editable-ui` | mover lista de conexões Pluggy de `data/item_ids.txt` para tela editável (norma 26) | 002 | — | planned |
| 022 | `setup-secrets-pluggy-credentials` | atualizar `docs/setup-secrets.md` para citar `PLUGGY_CLIENT_ID` e `PLUGGY_CLIENT_SECRET` | 002 | — | planned |
| 023 | `category-labels-in-schema` | mover rótulo em pt-BR das categorias de `app/taxonomy/seed.json` para coluna `label` na tabela `categories`, de modo que SQL possa ordenar e filtrar por categoria em 004 e 006 | 003 | — | planned |
| 024 | `payee-filling-post-sync` | mover `_fill_payees` e classificação automática da entrada de dados (`ingest`) para o pós-processamento (`synchronise`), para que bases de teste e e2e tenham recebedor preenchido | 003 | — | planned |
| 025 | `spending-filter-predicate-unification` | unificar predicado de data duplicado em `app/queries/spending.py` (`total_spending_cents`) e `app/queries/expenses.py` (`_where`) em `spending.py`, evitando divergência na soma por categoria (008) | 005 | — | planned |
| 026 | `unify-payee-name-precedence` | consolidar precedência do nome do recebedor entre Python (`app/payees/names.py`, `_chosen`) e SQL (`app/queries/expenses.py`, `_PAYEE_NAME_SQL`), evitando divergência silenciosa se uma mudar | 007 | 025 | planned |
