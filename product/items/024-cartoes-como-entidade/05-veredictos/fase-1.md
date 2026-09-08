VEREDICTO: APROVADO

Portões
  ruff:   OK — `bash scripts/lint.sh` → exit 0, "All checks passed!"
  format: OK — mesmo script, "143 files already formatted"
  mypy:   N/A NESTA STACK — `.venv/bin/mypy` não existe e não há seção mypy em
          pyproject.toml. A norma 35 do projeto declara `mypy --strict` como
          item de roadmap, e o despacho da fase lista três portões, sem ele.
          Registrado como não medido, não como aprovado.
  pytest: OK — `env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q`
          → exit 0, "547 passed, 2 warnings in 41.15s" (coletou, não saiu 5)
  gates:  OK — `bash scripts/gates/gates_runner.sh` → exit 0,
          "✓ gates: limpos (árvore completa, 506 arquivo(s) considerados)"
          — 506 > 0, medição real, não passe falso

Nada de plano, spec, brief ou histórico chegou junto do despacho; só o arquivo de objetivo e critérios. Não abri `product/items/024-cartoes-como-entidade/`.

## Critérios de aceite

| # | Tipo | Passou | Evidência executada |
|---|---|---|---|
| 1 | estrutural | sim | Base nova em tmp por `apply_migrations`. `PRAGMA table_info('cards')` → `account_id`(pk=1, notnull=0), `limit_cents`, `monthly_rate_bp`, `closing_day`, `due_day`, nesta ordem, as quatro com notnull=0. `PRAGMA foreign_key_list('cards')` → uma linha só: `(0,0,'accounts','account_id','id',...)`. Varredura por regex `create table ... cards` em todos os `.sql` da pasta acusa só `013_cards.sql` |
| 2 | estrutural | sim | `len(FIELDS)==4`; nomes `limite/taxa/fechamento/vencimento` nesta ordem; colunas `limit_cents/monthly_rate_bp/closing_day/due_day`; rótulos `Limite/Taxa mensal/Dia do fechamento/Dia do vencimento`. `store` tem `reconcile/read/write`. `cards.typed.parse_money is settings.typed.parse_money` → True, idem `parse_rate`; `"def parse_money"`/`"def parse_rate"` ausentes de `app/cards/typed.py` |
| 3 | comportamental | sim | Pasta só com migrações `<013` copiada para tmp; base povoada com as duas contas e o degrau `card` de 900; `cards` não existia antes. Aplicando a pasta inteira: `applied full: ['013_cards.sql']`; `SELECT account_id, monthly_rate_bp FROM cards` → `[('acc-cartao-1', 900)]`; `SELECT monthly_rate_bp FROM debts WHERE name='Cartão Azul'` → `[(None,)]`; conta BANK produziu 0 linhas em `cards` |
| 4 | comportamental | sim | `rebuild #1 -> 1`; após as quatro escritas, `(1200000, 1250, 3, 10)`. Inserida `acc-cartao-2` e `rebuild #2 -> 2`: `SELECT account_id FROM cards ORDER BY account_id` → `['acc-cartao-1','acc-cartao-2']`; campos de `acc-cartao-1` → `(1200000, 1250, 3, 10)`; de `acc-cartao-2` → `(None,None,None,None)` |
| 5 | comportamental | sim | 1ª leitura: `ladder` = `[('Cartão Azul','card',1250), ('Conta corrente','overdraft',352)]`, `without_rate` = `[]` (nenhum `kind='card'`). Após taxa vazia: `ladder` = `[('Conta corrente','overdraft',352)]`, `without_rate` = `[('Cartão Azul','card')]` |
| 6 | comportamental | sim | `POST /dividas/taxa degrau=1 taxa=12,5` → **200**; `cards.monthly_rate_bp` → **1250**, `debts.monthly_rate_bp` → **None**. `GET /dividas` → 200; trecho `id="escada"`…`</section>` contém `data-taxa="1250"`; seção `id="sem-taxa"` deixou de ser renderizada (logo não contém `data-degrau="1"`). `POST /dividas/simular` → **200**, sem `Informe a taxa primeiro.` **Checagem contra vacuidade:** na mesma base *antes* da taxa, `sem-taxa` existe e contém `data-degrau="1"`, `escada` não tem `data-taxa="1250"`, e simular devolve **400** com `Informe a taxa primeiro.` |
| 7 | comportamental | sim | Com `cdc_safra_veiculo.json` no `DASH_MANUAL_DIR` e `today=date(2026,9,5)`: após 2º `rebuild`, `ladder` = `overdraft Conta corrente rate=352` e `vehicle CDC do veículo rate=163 term=45 balance=-3917636` |
| 8 | comportamental | sim | Boas escritas → `(1200000,1250,3,10)`. As quatro recusas levantam `InvalidValueError` com o valor digitado e a frase certa: `"Limite inválido: “5000.00”. Escreva na forma 1.234,56…"`, `"Taxa mensal fora da faixa: “200”. Use de 0 a 100% ao mês."`, `"Dia do fechamento inválido: “32”. Use um dia do mês, de 1 a 31."`, `"Dia do vencimento inválido: “3,5”. Use um dia do mês, de 1 a 31."`. Leitura depois das quatro → `(1200000,1250,3,10)`. `CHECK` exercida por SQL cru: `UPDATE cards SET closing_day=32` e `INSERT ... closing_day=32` → `sqlite3.IntegrityError: CHECK constraint failed: closing_day IS NULL OR closing_day BETWEEN 1 AND 31` |
| 9 | comando | sim | O comando exato saiu **0**, "55 passed" (coletou). `tests/test_cards.py` entra como `A` no `git log develop..HEAD --name-status`. `EXPECTED_MIGRATIONS` ganhou `013_cards.sql` e `EXPECTED_TABLES` ganhou `cards`. As quatro funções exigidas existem (`grep -c "def <nome>"` = 1 em cada). As cinco provas pedidas em `test_cards.py` estão nomeadas: migração sobre base povoada, reconciliação na reconstrução, leitura da escada, gramática dos quatro campos e recusa do `CHECK` |

## Minha própria caça à casa dupla

Base montada por mim, escrevendo pelos dois caminhos e lendo pelos quatro (`ladder`, `without_rate`, `step`, `cards.store.read`, mais as duas colunas cruas):

| Estado | ladder | store.read | cards cru | debts cru | concordam |
|---|---|---|---|---|---|
| escreveu por `cards.store.write` "9,75" | 975 | 975 | 975 | None | sim |
| escreveu por `POST /dividas/taxa` "14,25" | 1425 | 1425 | 1425 | None | sim |
| ...seguido de `rebuild` | 1425 | 1425 | 1425 | None | sim |
| limpou por `store.write ""` | fora da escada | None | None | None | sim |
| limpou por `POST /dividas/taxa` vazio | fora da escada | None | None | None | sim |

**Só uma casa escreve.** `grep` em `app/` acha um único `UPDATE ... monthly_rate_bp` em `debts` (`ladder.py:211`), e ele só é alcançado quando o degrau **não** é cartão-com-conta. `rebuild` recolhe as taxas de `SELECT ... FROM debts` cru, não da visão com `COALESCE` — por isso a reconstrução não copia a taxa do cartão de volta para `debts`.

**Degraus que não são cartão:** conta corrente 352 e veículo 163/45/−3917636 sobrevivem a duas reconstruções (critério 7), e a hipoteca continua coberta por `test_the_mortgage_never_enters_the_expensive_ladder`.

**Sem taxa informada:** cartão fica fora da `ladder` e aparece em `without_rate` — idêntico ao de antes.

**Quatro campos contra reconstrução e sincronização:** depois de `ingest(...)` com três contas (uma nova de crédito) e `rebuild`, `SELECT * FROM cards` → `('acc-cartao-1', 1200000, 1250, 3, 10)` intacto e `('acc-cartao-3', None, None, None, None)` nascido vazio. `app/sync/__init__.py:104` chama `rebuild`, que chama `reconcile` — conta nova sincronizada ganha cartão sem passo manual.

**Quebra:** 26 valores fora da gramática por `store.write` e 10 por HTTP. Nenhum 500, nenhum grava. HTTP: `taxa=200|abc|-1|nan|1.234.567` → 400; `degrau=999|abc|""` → 400; em todos, `cards` e `debts` inalterados.

**Guarda de sessão:** nenhuma rota nova nesta fase (`git diff` do merge-base não tem uma linha `@router.` ou `include_router` a mais). `tests/test_route_guard.py`, que varre as 41 rotas registradas, passa; à mão, `POST /dividas/taxa` e `GET /dividas` sem sessão → **302**.

## Achados que não reprovam

**1. Conta que muda de CREDIT para BANK deixa cartão órfão, e a escada engole a taxa que o dono digita.** É o achado sério. `_STEPS` casa `c.account_id = d.account_id` **sem exigir `d.kind = 'card'`**, e `reconcile` só faz `INSERT OR IGNORE`, nunca remove. Medido:

```
as CREDIT:        ladder = [('card', 'Conta X', 1250)]
após virar BANK:  ladder = [('overdraft', 'Conta X', 1250)]   <- taxa do cartão morto
dono digita 3,52 no degrau de cheque especial:
                  ladder = [('overdraft', 'Conta X', 1250)]   <- 200, e a tela mente
                  debts = 352   cards = 1250
```

O dono salva, recebe 200, e a tela devolve 12,50. É exatamente o defeito que a fase existe para fechar, reaparecido por outra porta. Conserto de uma linha: `LEFT JOIN cards c ON c.account_id = d.account_id AND d.kind = 'card'`.

**2. `cards.account_id` é `TEXT PRIMARY KEY` sem `NOT NULL`, e o SQLite aceita NULL nessa forma.** `cards.write(conn, None, "taxa", "5")` grava, e três chamadas gravam **três linhas** — `ON CONFLICT(account_id)` não dispara porque NULL ≠ NULL. Nenhuma leitura se corrompe hoje (as duas junções descartam NULL) e o caminho é inalcançável por HTTP, porque `set_rate` testa `account_id is not None`. É armadilha para a fase da tela de cartões. `NOT NULL` na coluna fecha.

**3. Dois cartões de mesmo nome colapsam em um degrau só.** `debts` tem `UNIQUE (kind, name)`; com `('acc-1','Cartão')` e `('acc-2','Cartão')`, `rebuild` grava 2 e a `ladder` mostra 1. `cards` guarda as duas taxas, e a do segundo cartão nunca chega a `/dividas`. **Pré-existente** — a restrição e o `INSERT OR REPLACE` não foram tocados nesta fase.

**4. A numeração das migrações pula o 012.** Vai de `011_payee_names.sql` para `013_cards.sql`; nada ignorado pelo git na pasta. Se outro ramo trouxer um `012_*.sql` depois, ele aplicará **após** o 013 nas bases já migradas, porque o runner registra versão por versão.

## Instrumentos do implementer

Só o critério 9, que é `comando` e por definição roda a suíte do avaliado. Os oito restantes foram provados em bases montadas por mim em diretório temporário, com `DASH_ENV_FILE=/dev/null`, `DASH_MANUAL_DIR` controlado e `DASH_TODAY=2026-09-05`. A base do dono não foi tocada.
