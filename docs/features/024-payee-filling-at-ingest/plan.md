# PLAN 024 — payee-filling-at-ingest

Branch: `feature/024-payee-filling-at-ingest`

Decisões registradas aqui (a SPEC deixou ao plano, ou o plano encontrou ao ler o código; escolhido o mais simples):

- **Uma fase só**: a mudança de produção tem ~25 linhas em três arquivos e os testes que a provam mexem nos mesmos caminhos; separar não deixaria nada utilizável no meio.
- **`scripts/e2e-backend.sh` não muda**: já carrega por `ingest` e herda o preenchimento.
- **A linha 032 do roadmap é reescrita junto com a 024** (dívida da SPEC, acréscimo aprovado pela orquestração): depois desta fatia o recebedor já nasce preenchido na carga; ao 032 resta aplicar a classificação (grupo, natureza, essencialidade) no seed de `scripts/e2e-backend.sh`. Dependências e status das duas linhas não mudam.

## Fase 1 — `payee` preenchido pela própria `ingest`, na transação da carga

Python e duas linhas de `docs/roadmap.md`. Ao final: toda carga por `ingest` (sincronização, `python -m app.ingest`, seed do e2e, testes) deixa `transactions.payee = normalize_description(description)` em toda linha que estava sem recebedor, no mesmo `commit` do `ok` em `sync_runs`; descrição que normaliza para vazio fica `NULL`; recebedor existente não é sobrescrito; carga rejeitada ou com falha não escreve recebedor; `classify_all` não preenche mais `payee`.

- [ ] T1.1 — Mover `_fill_payees` para a carga, gravando `NULL` para vazio, e tirá-la da classificação
  - Arquivos: `app/ingest/loader.py` (alterar); `app/taxonomy/classify.py` (alterar); `app/queries/similar.py` (alterar)
  - O que fazer:
    - `loader.py`: importa `normalize_description` de `app.ingest.normalize`; nova função privada `def _fill_payees(conn: sqlite3.Connection) -> None` com o mesmo corpo da de `classify.py` (seleciona as linhas com `payee IS NULL OR payee = ''` e faz `UPDATE transactions SET payee = ? WHERE id = ?`), mas o valor gravado passa a ser `normalize_description(row["description"]) or None`. Em `ingest`, a chamada `_fill_payees(conn)` entra dentro do `try` do upsert, logo depois do `executemany` de lançamentos e antes das contagens de presença (`accounts_present`/`transactions_present`), do registro em `sync_runs` e do `commit`. Falha nela cai no `except` existente (`_fail`: rollback + `sync_runs` com `failed`). Rejeição e arquivo desatualizado continuam retornando antes do upsert. `payee` continua fora de `_TRANSACTION_COLUMNS`. Assinatura de `ingest` e `IngestResult` não mudam.
    - `classify.py`: remove `_fill_payees`, a chamada dela na primeira linha de `classify_all` e o import de `normalize_description` (se não restar outro uso). O resto de `classify_all` não muda.
    - `similar.py`: o comentário `# Reason:` do ramo por descrição de `SIMILAR_IDS` passa a dizer que o ramo cobre a origem sem recebedor derivável (descrição que normaliza para vazio); deixa de citar "recém-ingerida ainda não classificada". O SQL não muda.
  - Skills: python-tipagem-estrita
  - Complexidade: média

- [ ] T1.2 — Roadmap: linhas 024 e 032 no presente
  - Arquivos: `docs/roadmap.md` (alterar)
  - O que fazer:
    - Linha 024: slug passa de `payee-filling-post-sync` a `payee-filling-at-ingest`; descrição vira "preencher `payee` na própria `ingest`, na transação da carga, para que toda base (sincronização, testes, e2e) nasça com recebedor; a classificação segue no pós-carga". Dependência `003`, coluna `—` e status `in-progress` não mudam.
    - Linha 032 (`e2e-seed-classifies`): descrição reescrita no presente: o recebedor já nasce preenchido na carga; o seed de `scripts/e2e-backend.sh` não roda `classify_all`, então grupo, natureza e essencialidade ficam sem classificação automática; aplicar a classificação no seed. Deixa de dizer que `payee` fica nulo. Dependências `011` e `024` e status `planned` não mudam.
    - Nenhuma outra linha muda.
  - Skills: —
  - Complexidade: baixa

- [ ] T1.3 — Testes da fase 1
  - Arquivos: `tests/test_ingest.py` (alterar); `tests/test_sync.py` (alterar); `tests/test_similar.py` (alterar); `tests/test_expenses_api.py` (alterar)
  - O que fazer (python-testes-unitarios; reaproveita os helpers e fixtures existentes de cada arquivo):
    - `tests/test_ingest.py`, quatro testes novos:
      - `test_ingest_fills_the_payee_from_the_normalized_description` — carga com lançamentos de descrição preenchida; para cada linha, `payee == normalize_description(description)`; `sync_runs` com `ok`.
      - `test_ingest_again_does_not_overwrite_an_existing_payee` — carga; `UPDATE transactions SET payee = 'MANUAL'` numa linha e `commit`; mesma carga de novo; essa linha continua `'MANUAL'`.
      - `test_ingest_leaves_the_payee_null_when_the_description_is_null` — lançamento com descrição nula; `payee IS NULL` (não `''`).
      - `test_a_rejected_ingest_writes_no_payee_and_records_failed` — carga válida; `UPDATE transactions SET payee = NULL` numa linha e `commit`; nova carga com uma linha sem `id` (rejeitada); a linha continua com `payee IS NULL` e a última linha de `sync_runs` tem status `failed`.
    - `tests/test_sync.py`:
      - `test_synchronise_ends_with_the_payee_filled_on_every_row_with_a_description` — `synchronise` com a fonte fake existente; `SELECT count(*) FROM transactions WHERE description IS NOT NULL AND (payee IS NULL OR payee = '')` é `0`.
    - `tests/test_similar.py`:
      - `test_count_similar_falls_back_to_the_folded_description_when_the_payee_is_null` (mesmo nome) — depois de `prepared(..., classify=False)`, força `UPDATE transactions SET payee = NULL` nas linhas `o`, `s1` e `s2`, `commit`, e confere `count_similar(o) == 2`.
    - `tests/test_expenses_api.py`: remove o import de `_fill_payees` e os quatro blocos `conn = connect(); _fill_payees(conn); conn.commit(); conn.close()`; onde o `connect()` só existia para isso, sai junto. Nomes e asserções dos testes não mudam.
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [ ] CA1.1 — `bash scripts/lint.sh` sai com código 0; `uv run pytest` sai com código 0; `bash scripts/gates/gates_runner.sh` sai com código 0. (comando)
- [ ] CA1.2 — `uv run pytest tests/test_ingest.py tests/test_sync.py tests/test_similar.py tests/test_expenses_api.py` sai com código 0. (comando)
- [ ] CA1.3 — `app/ingest/loader.py` define `def _fill_payees(conn: sqlite3.Connection) -> None`, importa `normalize_description` de `app.ingest.normalize` e contém `normalize_description(row["description"]) or None`; dentro de `ingest`, a chamada `_fill_payees(conn)` está no mesmo bloco `try` do upsert, depois do `executemany` de lançamentos e antes das contagens de presença, da escrita em `sync_runs` e do `commit(`; `_TRANSACTION_COLUMNS` não contém `"payee"`; a assinatura de `ingest` e a definição de `IngestResult` não mudam (`git diff develop -- app/ingest/loader.py` não altera a linha `def ingest(` nem `class IngestResult`). (estrutural)
- [ ] CA1.4 — `rg -n "_fill_payees" app/ tests/` devolve só linhas de `app/ingest/loader.py` (definição e uma chamada); `app/taxonomy/classify.py` não contém `_fill_payees` nem `normalize_description`; `classify_all` continua existindo e sendo chamada em `app/sync/__init__.py`; `git diff develop -- scripts/e2e-backend.sh app/sync/__init__.py` é vazio. (estrutural)
- [ ] CA1.5 — Em `app/queries/similar.py`, o `# Reason:` do ramo por descrição não contém "recém-ingerida" nem "ainda não classificada" e menciona descrição que normaliza para vazio; o SQL de `SIMILAR_IDS` não muda. (estrutural)
- [ ] CA1.6 — Comportamento: carga preenche o recebedor normalizado; recarga não sobrescreve recebedor existente; descrição nula deixa `NULL`; carga rejeitada não escreve recebedor e grava `failed` (os 4 novos de `tests/test_ingest.py`: `test_ingest_fills_the_payee_from_the_normalized_description`, `test_ingest_again_does_not_overwrite_an_existing_payee`, `test_ingest_leaves_the_payee_null_when_the_description_is_null`, `test_a_rejected_ingest_writes_no_payee_and_records_failed`); `synchronise` termina sem linha com descrição e sem recebedor (`tests/test_sync.py::test_synchronise_ends_with_the_payee_filled_on_every_row_with_a_description`); o ramo por descrição continua coberto com `payee` forçado a nulo (`tests/test_similar.py::test_count_similar_falls_back_to_the_folded_description_when_the_payee_is_null`); `tests/test_expenses_api.py` passa sem nenhuma chamada manual de preenchimento e com os mesmos nomes de teste de antes (`git diff develop -- tests/test_expenses_api.py` não contém linha começando por `+def test_` nem `-def test_`). (comportamental)
- [ ] CA1.7 — `uv run pytest --cov=app.ingest.loader --cov=app.taxonomy.classify --cov=app.queries.similar --cov-report=term tests/test_ingest.py tests/test_sync.py tests/test_similar.py tests/test_expenses_api.py` reporta ≥ 80% em cada um dos três módulos. (comando)
- [ ] CA1.8 — `docs/roadmap.md`: a linha 024 é `| 024 | \`payee-filling-at-ingest\` |`, fala em preencher `payee` na própria `ingest`, na transação da carga, e termina com `| 003 | — | in-progress |`; a linha `| 032 | \`e2e-seed-classifies\` |` diz que o recebedor já nasce preenchido na carga e que resta aplicar a classificação (grupo, natureza, essencialidade) no seed de `scripts/e2e-backend.sh`, não diz que `payee` fica nulo e termina com `| 011 | 024 | planned |`; nenhuma outra linha do roadmap muda. (estrutural)

## DoD da entrega

- [ ] DoD1 — Todas as tarefas e critérios do plano marcados
- [ ] DoD2 — Suíte de testes inteira passa
- [ ] DoD3 — Lint do projeto inteiro sem erros nem avisos
- [ ] DoD4 — Tipos de todos os `tsconfig` sem erros
- [ ] DoD5 — Console dos testes sem erro nem aviso
- [ ] DoD6 — `build` passa
- [ ] DoD7 — Nenhum import entre features nem contra o fluxo compartilhado → features → app
- [ ] DoD8 — Nenhum `console.log`, `TODO`, `// @debug`, `.only(` ou `.skip(` no diff da branch
- [ ] DoD9 — Nenhuma worktree ou branch temporária sobrando
