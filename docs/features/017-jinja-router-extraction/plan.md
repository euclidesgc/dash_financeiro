# PLAN 017 — jinja-router-extraction

Branch: `feature/017-jinja-router-extraction`

Decisões registradas aqui (escolhido o mais simples):

- **Trilha de feature, não de bugfix**: a origem do item diz "bug", mas nenhuma tela mostra número errado hoje; o risco é de divergência futura, e a entrega muda estrutura, não comportamento.
- **Uma fase só**: mover consultas sem o portão deixaria a regra sem cobrança; o portão sem a mudança reprovaria a árvore. Juntos, são a menor entrega que se sustenta.
- **O primeiro commit da branch marca a 028 como `done`** (mergeada em `develop` no PR #20).

## Fase 1 — Telas antigas sem consulta própria

Ao final: nenhum router Jinja monta SQL, executa consulta ou dá commit; as consultas moram em `app/queries`, o vocabulário da taxonomia e o resíduo existem uma vez só, e o G7 recusa a volta do padrão.

- [x] T1.1 — Módulos de consulta
  - Arquivos: `app/queries/rules.py`, `app/queries/vocabulary.py`, `app/queries/payees.py`, `app/queries/transactions.py` (criar); `app/queries/crossings.py`, `app/queries/reach.py`, `app/taxonomy/classify.py` (alterar)
  - O que fazer: funções de D1, D2 e D3 da SPEC, com o texto SQL levado sem mudança dos routers; `residue` com janela opcional por `date_window`.
  - Skills: python-tipagem-estrita
  - Complexidade: média
- [x] T1.2 — Routers só traduzem HTTP
  - Arquivos: `app/routers/spending.py`, `app/routers/rules.py`, `app/routers/summary.py`, `app/routers/settings.py`, `app/routers/commitments.py`, `app/commitments/mark.py` (alterar)
  - O que fazer: trocar cada constante SQL e `conn.execute` pela função de consulta; tirar `conn.commit()` do router e dar o commit em `dismiss`/`resume`.
  - Complexidade: média
- [x] T1.3 — G7 cobre o driver sqlite3
  - Arquivos: `scripts/gates/gate7_layer_boundary.sh` (alterar), `scripts/gates/__tests__/gate7.test.sh` (criar), `.github/workflows/harness.yml` (alterar)
  - O que fazer: padrão de D5; teste com três casos acusados (execute, commit, texto SQL) e três limpos (marca de escape, router que delega, consulta fora de router); passo no job `portoes`.
  - Complexidade: baixa
- [x] T1.4 — Testes
  - Arquivos: `tests/test_screen_queries.py` (criar), `tests/test_classify.py`, `tests/test_override.py` (alterar)
  - O que fazer: cada função nova com caminho feliz e borda (id inexistente, recebedor desconhecido, base vazia, limite); resíduo sem janela conta a base inteira; `dismiss`/`resume` visíveis por outra conexão sem commit de quem chama.
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.2 — `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` e `pnpm test:e2e` saem com código 0. (comando)
- [x] CA1.3 — `bash scripts/gates/__tests__/gate7.test.sh` sai com código 0, e sai com código diferente de 0 contra o `gate7_layer_boundary.sh` de `develop`. (comando)
- [x] CA1.4 — `grep -nE '\.(execute|executemany|commit)\(|"(SELECT|INSERT|UPDATE|DELETE) ' app/routers/*.py` não encontra nada. (estrutural)
- [x] CA1.5 — `groups`, `natures` e `terms` têm uma definição só (`app/queries/vocabulary.py`), usada por `app/routers/spending.py` e `app/routers/rules.py`; `residue` tem uma definição só (`app/queries/rules.py`), usada pelas duas telas. (estrutural)
- [x] CA1.6 — Os testes de tela existentes passam sem alteração; o resíduo sem janela conta a base inteira e com janela só o período; `dismiss`/`resume` ficam visíveis por outra conexão; tirar o `commit` de `dismiss` faz o teste de durabilidade falhar. (comportamental)

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
