# SPEC 024 — payee-filling-at-ingest

Vigésima quarta fatia. O recebedor normalizado de cada lançamento (`transactions.payee`, derivado da descrição por `normalize_description`) passa a ser gravado pela própria carga, `ingest`, na mesma transação do upsert e antes do registro em `sync_runs`. Hoje ele só nasce dentro de `classify_all`, que roda no pós-carga de `synchronise`; toda base carregada por outro caminho (a base do e2e, as bases de teste, `python -m app.ingest`) fica com `payee` nulo até a primeira troca de categoria, e "gastos parecidos" cai no ramo por descrição — estado que a produção nunca tem. A classificação (grupo, natureza, essencialidade) continua onde está. Sem interface.

O que o código já faz hoje, e que esta SPEC reaproveita (nada disto se recria):

- `app/ingest/loader.py` · `ingest(conn, *, transactions, accounts, source, now)`: mapeia, rejeita (`_fail` faz `rollback` e grava a falha em `sync_runs`), faz o upsert de contas e lançamentos dentro de um `try` cujo `except` também cai em `_fail`, confere presença, grava `sync_runs` com `ok` e dá `commit`. `payee` não está em `_TRANSACTION_COLUMNS`, então o upsert nunca o toca numa linha existente.
- `app/ingest/normalize.py` · `normalize_description(text: str | None) -> str` (devolve `""` para nulo).
- `app/taxonomy/classify.py:96` · `_fill_payees(conn)`: `UPDATE transactions SET payee = normalize_description(description)` para toda linha com `payee IS NULL OR payee = ''`; chamada na primeira linha de `classify_all`.
- `app/sync/__init__.py` · `synchronise` chama `ingest` e, se `ok`, `_after` (que roda `classify_all`); falha no pós-carga rebaixa a linha de `sync_runs` (`_demote`).
- `app/queries/similar.py` · `SIMILAR_IDS`: compara por `payee` quando a origem tem um; senão, por `fold(description)`. O comentário `# Reason:` diz que o ramo por descrição vale "enquanto a origem não tem payee (linha recém-ingerida ainda não classificada)".
- Todo `INSERT` em `transactions` passa por `ingest`: conferido em `app/` (único `INSERT INTO transactions` é o `_upsert` do loader), `app/ingest/__main__.py`, `app/sync/__init__.py`, `scripts/e2e-backend.sh` e os testes (`tests/conftest.py::load` e as chamadas diretas a `ingest`); nenhum teste insere lançamento por SQL cru.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `ingest` chama `_fill_payees(conn)` logo depois do upsert de lançamentos, dentro do mesmo `try`, antes das contagens, do `sync_runs` e do `commit` (D1, D2). Os três caminhos de carga (`synchronise`, `python -m app.ingest`, `scripts/e2e-backend.sh`) já passam por `ingest`. |
| R2 | `normalize_description(None)` devolve `""`; a função grava `NULL` quando a normalização sai vazia (D3). |
| R3 | O `WHERE payee IS NULL OR payee = ''` é mantido: linha com recebedor não é tocada; `payee` continua fora de `_TRANSACTION_COLUMNS`, então o upsert também não o toca (D1). |
| R4 | `classify_all` perde só a chamada a `_fill_payees`; continua rodando apenas em `_after` de `synchronise` (D4). |
| R5 | A base do e2e é carregada por `ingest` em `scripts/e2e-backend.sh`, então já nasce com `payee`; `count_similar` passa a usar o ramo por recebedor desde a primeira consulta. Provado no teste de `ingest` e no de `count_similar` com classificação desligada (D5). |

## Decisões técnicas

### D1 — `_fill_payees` sai de `classify.py` e vira privada de `app/ingest/loader.py`, chamada dentro da transação do upsert

- Escolha: mover a função, com o mesmo corpo, para `app/ingest/loader.py` como `_fill_payees(conn: sqlite3.Connection) -> None`, importando `normalize_description` de `app/ingest/normalize.py`. Em `ingest`, a chamada entra no bloco `try`, logo após o `executemany` de lançamentos e antes de `accounts_present`/`transactions_present`. Assim: falha de escrita dela cai no `except` que já existe (rollback + `sync_runs` com `failed`); rejeição e arquivo desatualizado retornam antes dela e nada é escrito; sucesso sai no mesmo `commit` que grava o `ok`. O pacote `app/ingest` é o dono da normalização na entrada, como já é do sinal (invariante 22).
- Alternativa descartada: módulo novo `app/ingest/payee.py` com função pública — motivo: só `ingest` a chama; os testes que a chamavam à mão deixam de precisar dela (D5). Um arquivo e um nome público a mais sem consumidor.
- Alternativa descartada: calcular `payee` em `_transaction_row` e pôr a coluna no upsert — motivo: o `ON CONFLICT DO UPDATE` sobrescreveria o recebedor de linhas existentes (quebra R3) ou exigiria um `CASE` a mais em `_TRANSACTION_OVERRIDES`; e deixaria de preencher linhas antigas com `payee` nulo que não vieram nesta carga.
- Alternativa descartada: manter a chamada também em `classify_all` "por garantia" — motivo: dois lugares para a mesma regra; `classify_all` só roda depois de um `ingest` com `ok`, que já preencheu tudo.

### D2 — Alcance: toda linha da tabela com `payee` nulo ou vazio, não só as da carga

- Escolha: o `UPDATE` continua sem filtro por lote (`WHERE payee IS NULL OR payee = ''`), a mesma semântica de hoje.
- Alternativa descartada: restringir aos `pluggy_id` da carga — motivo: exigiria o fatiamento em blocos de `_ID_CHUNK` de novo, e deixaria de curar linhas antigas; o custo do `UPDATE` total é o mesmo que `classify_all` já pagava a cada sincronização.

### D3 — Descrição nula ou normalização vazia grava `NULL`, não `""`

- Escolha: o parâmetro do `UPDATE` passa a ser `normalize_description(row["description"]) or None`. Hoje a função grava `""` para descrição nula; como o `WHERE` trata `''` e `NULL` como ausência, e `SIMILAR_IDS`/`expenses.py` testam `payee IS NULL` ou `payee != ''`, gravar `NULL` torna "sem recebedor" um único estado (R2) — mesma regra que o loader já aplica a `merchant_name` e `receiver_name` ("a string vazia é ausência").
- Alternativa descartada: manter `""` — motivo: `app/queries/expenses.py:52` usa `CASE WHEN t.payee IS NULL`, e uma linha com `""` sairia com nome de exibição vazio em vez de nulo; o teste de R2 teria de aceitar dois valores para "sem recebedor".

### D4 — Classificação fica no pós-carga

- Escolha: `classify_all` só perde a primeira linha; `_after` em `synchronise` segue igual. Rodar a classificação no seed do e2e é o item 032, fora desta fatia.
- Alternativa descartada: nenhuma considerada; é fora de escopo pelo PRD.

### D5 — Testes e comentário que ficaram falsos

- `app/queries/similar.py`: o `# Reason:` passa a dizer que o ramo por descrição cobre a origem sem recebedor derivável (descrição que normaliza para vazio) — deixa de citar "recém-ingerida ainda não classificada".
- `tests/test_similar.py::test_count_similar_falls_back_to_the_folded_description_when_the_payee_is_null`: depois de `prepared(..., classify=False)`, força `UPDATE transactions SET payee = NULL` nas linhas `o`, `s1`, `s2` e confere que `count_similar(o) == 2` — o ramo continua coberto sem depender de o `ingest` deixar nulo.
- `tests/test_expenses_api.py`: remove o import de `_fill_payees` e os quatro blocos `conn = connect(); _fill_payees(conn); conn.commit(); conn.close()` (linhas ~221, 858, 869, 1014); onde o `connect()` só existia para isso, sai junto. Os testes continuam iguais nas asserções, agora provando que a carga basta.
- Testes novos em `tests/test_ingest.py`: `ingest` preenche `payee` com `normalize_description(descricao)`; `ingest` repetido não sobrescreve `payee` já existente (grava um valor à mão entre as cargas); descrição nula deixa `payee` `NULL`; carga rejeitada (linha sem `id`) não deixa `payee` escrito em linha pré-existente com `payee` nulo e grava `failed` em `sync_runs`. Em `tests/test_sync.py`: `synchronise` termina com `payee` preenchido em toda linha com descrição.

## Contrato

Sem mudança de API nem de OpenAPI. `ingest` mantém assinatura e `IngestResult`.

## Interface

Sem interface.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `app/ingest/loader.py` | `_fill_payees` (movida, grava `NULL` para vazio); chamada dentro do `try` após o upsert de lançamentos; import de `normalize_description` (D1, D2, D3) | `python-tipagem-estrita` |
| alterar | `app/taxonomy/classify.py` | remove `_fill_payees`, sua chamada em `classify_all` e o import de `normalize_description` (D1, D4) | — |
| alterar | `app/queries/similar.py` | reescreve o `# Reason:` do ramo por descrição (D5) | — |
| alterar | `tests/test_ingest.py` | quatro testes novos de R1, R2, R3 e rejeição (D5) | `python-testes-unitarios` |
| alterar | `tests/test_sync.py` | `synchronise` termina com `payee` preenchido (D5) | `python-testes-unitarios` |
| alterar | `tests/test_similar.py` | teste do ramo por descrição força `payee` nulo explicitamente (D5) | `python-testes-unitarios` |
| alterar | `tests/test_expenses_api.py` | remove import e chamadas manuais de `_fill_payees` (D5) | `python-testes-unitarios` |

### Scripts e docs

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| — | `scripts/e2e-backend.sh` | nenhuma: já carrega por `ingest`, e herda o preenchimento | — |
| alterar | `docs/roadmap.md` | linha 024 reescrita no presente: slug `payee-filling-at-ingest`, "preencher `payee` na própria `ingest`, na transação da carga, para que toda base (sincronização, testes, e2e) nasça com recebedor; a classificação segue no pós-carga"; status inalterado | — |

## Estimativa de tamanho

Jornadas: 1 (conferir gastos numa base carregada fora da sincronização) · Telas novas: 0 · Linhas alteradas (sem testes): ~25 (`loader.py` ~12, `classify.py` ~10 removidas, `similar.py` ~3) + 1 no roadmap · Fases previstas: 1.

Sinais de "grande demais": 1 jornada, 0 telas novas, 1 fase, ~25 linhas — nenhum dispara.

## Dívida encontrada

- `docs/roadmap.md` item 032 descreve o sintoma como "`payee` fica nulo até a primeira escrita de categoria"; depois desta fatia a descrição fica falsa (o que resta ao 032 é só grupo, natureza e essencialidade no seed). Reescrever a linha do 032 no mesmo PR (norma 7).
