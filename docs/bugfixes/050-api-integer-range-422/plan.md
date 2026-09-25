# PLAN 050 — api-integer-range-422

Branch: `bugfix/050-api-integer-range-422`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: todas as entradas inteiras e o fim do mês têm a mesma natureza (valor válido para o Python e inválido para o banco ou para o `date`), e a correção de cada uma é de poucas linhas.
- **O primeiro commit da branch marca a 049 como `done`** (mergeada em `develop` no PR #51).
- **A faixa mora num lugar só**, `app/db.py`, ao lado da conexão: é propriedade do SQLite, não de uma rota. Os leitores de texto das telas antigas passam a usar o mesmo `storable_int`.
- **API responde 422, tela antiga responde como a um texto que não é número.** Nas rotas JSON a FastAPI já responde 422 a um id que não é número; o id fora da faixa segue o mesmo caminho. Nas telas Jinja o número que não cabe é tratado como o texto que não é número, com a mensagem que a tela já tinha.
- **Dinheiro tem o teto de 12 algarismos**, o mesmo de `parse_money` (`MAX_DIGITS`), e não a faixa do SQLite: o teto é somado e comparado com gastos, e um valor de 19 algarismos não é teto de ninguém. A mensagem diz o maior valor em reais em vez de "12 algarismos".
- **A página tem teto `SQLITE_INTEGER_MAX // 100`**: com o maior tamanho de página (100), o deslocamento ainda cabe; o teto não depende do `page_size` pedido para a regra ser uma só.
- **O nome de categoria sem teto de tamanho vira item de roadmap** (065), não entra aqui: não é 500 nem inteiro.

## Fase 1 — Recusa limpa de inteiro fora da faixa e fim do último mês

Ao final: nenhuma das entradas listadas em `investigation.md` devolve 500; a API responde 422 e as telas antigas respondem como já respondiam a um texto que não é número.

- [x] T1.1 — Faixa do SQLite e leitor único
  - Arquivos: `app/db.py` (alterar)
  - O que fazer: `SQLITE_INTEGER_MIN`, `SQLITE_INTEGER_MAX` e `storable_int(text) -> int | None`.
  - Skills: python-tratamento-de-erros
  - Complexidade: baixa
- [x] T1.2 — Rotas da API com a faixa na entrada
  - Arquivos: `app/routers/row_id.py` (criar), `app/routers/transactions.py`, `app/routers/rules.py` (alterar)
  - O que fazer: `RowId = Annotated[int, Path(ge=SQLITE_INTEGER_MIN, le=SQLITE_INTEGER_MAX)]` em `row_id.py`, usado no id de lançamento e no id de regra; `page` com `le=SQLITE_INTEGER_MAX // MAX_PAGE_SIZE`; `_refused` usa `storable_int` no lugar de `_number`.
  - Skills: python-dependencies-para-validacao
  - Complexidade: baixa
- [x] T1.3 — Teto e limite com o maior valor aceito
  - Arquivos: `app/settings/limits.py`, `app/plan/ceiling.py`, `app/taxonomy/catalogue.py`, `app/routers/plan_api.py`, `app/routers/categories.py` (alterar)
  - O que fazer: `MAX_CENTS`; `set_ceiling` e `set_monthly_limit` recusam acima dele; os routers escolhem a mensagem pelo sinal do valor recusado.
  - Skills: python-tratamento-de-erros, python-schemas-pydantic-v2
  - Complexidade: baixa
- [x] T1.4 — Telas antigas e fim do mês
  - Arquivos: `app/routers/debts.py`, `app/routers/spending.py`, `app/queries/period.py` (alterar)
  - O que fazer: `_identifier` e `_as_int` usam `storable_int`; `month_end` com `calendar.monthrange`.
  - Complexidade: baixa
- [x] T1.5 — Roadmap
  - Arquivos: `docs/roadmap.md` (alterar)
  - O que fazer: item 065 para o teto de tamanho do nome de categoria, depois da 050 na precedência de quebra.
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `uv run pytest` sai com código 0, e no commit `e022fc3` os testes de `tests/test_integer_range.py` e `test_the_last_month_the_calendar_has_ends_on_its_last_day` falhavam. (comando)
- [x] CA1.2 — `bash scripts/lint.sh` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.3 — A faixa do SQLite aparece como número só em `app/db.py`; em `app/routers/rules.py`, `app/routers/debts.py` e `app/routers/spending.py` todo texto da requisição lido como inteiro passa por `storable_int` antes de chegar a uma consulta, e os ids de caminho de `transactions.py` e `rules.py` usam `RowId`. (estrutural)
- [x] CA1.4 — `PUT /api/plan/ceiling` com 1.000.000.000.000 centavos responde 422 com `O teto passa do maior valor aceito, R$ 9.999.999.999,99.`; com 999.999.999.999 responde 200. (comportamental)

## DoD da entrega

- [x] DoD1 — Todas as tarefas e critérios do plano marcados
- [x] DoD2 — Suíte de testes inteira passa
- [x] DoD3 — Lint do projeto inteiro sem erros nem avisos
- [x] DoD4 — Tipos de todos os `tsconfig` sem erros
- [x] DoD5 — Console dos testes sem erro nem aviso
- [x] DoD6 — `build` passa
- [x] DoD7 — Nenhum import entre features nem contra o fluxo compartilhado → features → app
- [x] DoD8 — Nenhum `console.log`, `TODO`, `// @debug`, `.only(` ou `.skip(` no diff da branch
- [x] DoD9 — Nenhuma worktree ou branch temporária sobrando
