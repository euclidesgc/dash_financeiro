# Roadmap atualizado

Uma única página web, com todas as contas. Cada linha é uma fatia utilizável sozinha; a primeira
prova o caminho de ponta a ponta (tela React → API FastAPI → SQLite) e as outras crescem sobre ela.

| # | Fatia | O usuário consegue… | Origem | Depende de | Status |
|---|---|---|---|---|---|
| 001 | `login-e-saldos` | entrar no painel e ver o saldo de hoje de cada conta | Pedido de 22/09 | — | in-review |
| 002 | `atualizar-registros` | apertar um botão e ter todos os registros bancários atualizados na base, vendo quando foi a última atualização | Pedido de 22/09 | 001 | in-progress |
| 003 | `lista-de-gastos` | ver uma lista paginada com todos os gastos de todas as contas | Pedido de 22/09 | 001 | planned |
| 004 | `ordenar-gastos` | ordenar os gastos por data, valor ou categoria | Pedido de 22/09 | 003 | planned |
| 005 | `filtrar-por-periodo` | filtrar os gastos por período (mês, intervalo de datas) | Pedido de 22/09 | 003 | planned |
| 006 | `filtrar-por-conta` | filtrar os gastos por banco ou conta | Pedido de 22/09 | 003 | planned |
| 007 | `buscar-por-texto` | encontrar gastos pela descrição ou pelo nome de quem recebeu | Pedido de 22/09 | 003 | planned |
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
