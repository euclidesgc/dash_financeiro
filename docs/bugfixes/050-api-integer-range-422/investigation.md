# Investigação: inteiro fora da faixa do SQLite e último mês do calendário devolvem 500

## Relato
- **Sintoma:** um número inteiro grande demais, digitado na URL, no formulário ou mandado no corpo de uma chamada, derruba a requisição com "Internal Server Error" (HTTP 500) em vez de uma recusa com mensagem. O mesmo acontece em "Gastos" com a data final 31/12/9999.
- **Esperado:** a API responde 422; a tela do teto e a do limite de categoria mostram, em português, que o valor passa do maior aceito; as telas antigas tratam o número como fazem com um texto que não é número (dívida não encontrada, grupo inválido, nenhum lançamento para corrigir); "Gastos" abre no período pedido.
- **Como reproduzir:** `GET /api/transactions/expenses?page=99999999999999999999`; `PUT /api/plan/ceiling` com `{"monthly_ceiling_cents": 100000000000000000000}`; `PUT /api/categories/<chave>/limit` com o mesmo valor; `PUT /api/transactions/99999999999999999999/not-expense`; `POST /dividas/taxa` com `degrau=99999999999999999999`; `GET /gastos?fim=9999-12-31`.
- **Onde:** `app/routers/transactions.py`, `app/routers/plan_api.py`, `app/routers/categories.py`, `app/routers/debts.py`, `app/routers/spending.py`, `app/routers/rules.py`, `app/queries/period.py`.

## Causa raiz
São duas causas.

1. **Inteiro sem limite chega ao SQLite.** O Python aceita inteiro de qualquer tamanho; o SQLite guarda inteiro em 8 bytes com sinal (de −2⁶³ a 2⁶³−1), e o `sqlite3` levanta `OverflowError` ("Python int too large to convert to SQLite INTEGER") quando recebe um maior como parâmetro. Nenhuma entrada inteira verificava essa faixa antes da consulta:
   - a página da lista (`page`) só tinha `ge=1`, e o deslocamento `(page − 1) × page_size` passa da faixa;
   - o id do lançamento (cinco rotas em `/api/transactions/{id}`) e o id da regra (`/regras/{id}/editar` e `/remover`) eram `int` sem limite;
   - o teto (`PUT /api/plan/ceiling`) e o limite de categoria (`PUT /api/categories/{key}/limit`) só recusavam valor menor ou igual a zero, e o valor ia direto para o `INSERT` (`plan_facts` e `categories`);
   - os leitores de texto das telas antigas (`_identifier` em `debts.py`, `_as_int` em `spending.py`, `_number` em `rules.py`) convertiam com `int()` e só recusavam o que não era número.
2. **O fim do mês de 12/9999 não existe no `date`.** `month_end` em `app/queries/period.py` calcula o último dia como "primeiro dia do mês seguinte menos um dia"; para dezembro de 9999 o mês seguinte é janeiro de 10000, e `date` levanta `ValueError: year 10000 is out of range`. `covers_whole_months` chama `month_end` em toda abertura de "Gastos", então qualquer período que termine em dezembro de 9999 derruba a tela.

## Evidência
- Teste de regressão (commit `e022fc3`):
  - `tests/test_integer_range.py`: 29 casos saem com 500 onde se espera 422, 400 ou 200 — página, teto, limite, id de lançamento nas cinco rotas, degrau em `/dividas/taxa` e `/dividas/simular`, "Gastos" com fim em 31/12/9999, alvo e grupo da correção, grupo e id da regra.
  - `tests/test_period.py`, `test_the_last_month_the_calendar_has_ends_on_its_last_day`: `month_end(date(9999, 12, 31))` levanta `ValueError`.

## Correção proposta
- `app/db.py` — a faixa do INTEGER do SQLite (`SQLITE_INTEGER_MIN`, `SQLITE_INTEGER_MAX`) e `storable_int(text)`, que lê um inteiro de um texto e devolve `None` quando não é número ou não cabe na faixa.
- `app/routers/transactions.py` — o id do lançamento vira um tipo com a faixa do SQLite; a página ganha teto `SQLITE_INTEGER_MAX // 100` (o maior `page_size`), para o deslocamento sempre caber. Fora disso, a FastAPI responde 422.
- `app/routers/rules.py` — o id da regra usa o mesmo tipo; `_number` passa a usar `storable_int`, e um grupo fora da faixa é "grupo inválido", como um texto.
- `app/routers/debts.py` e `app/routers/spending.py` — `_identifier` e `_as_int` passam a usar `storable_int`: degrau fora da faixa é "Dívida não encontrada."; alvo e grupo fora da faixa são "nenhum", como um texto.
- `app/settings/limits.py` — `MAX_CENTS`, o maior valor que `parse_money` aceita (12 algarismos, R$ 9.999.999.999,99).
- `app/plan/ceiling.py` e `app/taxonomy/catalogue.py` — o teto e o limite acima de `MAX_CENTS` são recusados pela mesma regra que recusa zero; `plan_api.py` e `categories.py` respondem 422 com "O teto passa do maior valor aceito, R$ 9.999.999.999,99." ou "O limite passa do maior valor aceito, R$ 9.999.999.999,99.". A tela da SPA já mostra o `detail` do 422 embaixo do campo.
- `app/queries/period.py` — `month_end` calcula o último dia com `calendar.monthrange`, sem passar pelo mês seguinte.
- **Risco:** um teto ou limite acima de R$ 9.999.999.999,99 já gravado continua lido como está; só a gravação nova é recusada. Nenhuma tela ou chamada existente manda número nessa faixa.

## Fora da correção
- O nome de categoria aceita 5.000 caracteres (`POST /api/categories`), achado da mesma sondagem da revisão: não derruba nada, é falta de teto de tamanho, e vai para o roadmap como item próprio.

## Pontos em aberto
Nenhum.
