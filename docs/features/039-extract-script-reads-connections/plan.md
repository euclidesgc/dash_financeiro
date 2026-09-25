# PLAN 039 — extract-script-reads-connections

Branch: `feature/039-extract-script-reads-connections`

Decisões registradas aqui:

- **O primeiro commit da branch marca a 021 como `done`** (mergeada em `develop` no PR #28).
- **A 039 passa à frente da 022** na ordem da tabela de dívidas: termina o que a 021 começou, e enquanto não sai o script manual e a tela divergem; a 022 é só texto de documentação e não perde nada esperando.

## Fase 1 — Script de extração lê e grava a lista da tela

Ao final: `criar-item`, `status` e `extrair` usam a tabela de conexões, e nada no repositório lê `data/item_ids.txt` fora do comando de importação.

- [x] T1.1 — Script usa a base
  - Arquivos: `ingestao/pluggy_extract.py`, `ingestao/raw.py`, `app/sync/fetch.py`
  - O que fazer: D1 a D4 da SPEC; docstring do módulo e mensagens em pt-BR citando Conexões.
  - Skills: python-tratamento-de-erros, python-tipagem-estrita
  - Complexidade: baixa
- [x] T1.2 — Testes
  - Arquivos: `tests/test_pluggy_scripts.py`
  - O que fazer: `itens_salvos` devolve a lista da base em ordem de cadastro; `registrar_item` cadastra e é idempotente; `status` sem `--item` com base vazia sai com `NO_CONNECTIONS`; `status` sem `--item` consulta os ids da base (com `autenticar` e `status_de_um` substituídos); `--item` não cria a base.
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `bash scripts/lint.sh`, `uv run pytest` e `bash scripts/gates/gates_runner.sh` saem com código 0. (comando)
- [x] CA1.2 — `grep -rn "item_ids.txt\|item_id.txt\|PLUGGY_ITEM_ID" ingestao/ app/` não encontra nada. (estrutural)
- [x] CA1.3 — Com duas conexões cadastradas na base apontada por `DASH_DB_PATH`, `status` sem `--item` consulta exatamente esses dois ids, na ordem de cadastro; com a base vazia, sai com "Nenhuma conexão cadastrada. Cadastre em Conexões ou passe --item."; com `--item`, não cria o arquivo da base. (comportamental)
- [x] CA1.5 — `uv run python -c "import ingestao.pluggy_extract"` e `uv run python -m ingestao.pluggy_extract --help` saem com código 0, e a ajuda cita `python -m ingestao.pluggy_extract`. (comando)
- [x] CA1.4 — `registrar_item` com um id novo o põe em `list_item_ids`; chamado de novo com o mesmo id, não levanta erro e a lista continua com um só. (comportamental)

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
