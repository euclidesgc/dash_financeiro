# PLAN 042 — consolidation-latest-copy

Branch: `bugfix/042-consolidation-latest-copy`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: escolher a cópia e levar o descarte até o banco são a mesma correção; sem a segunda metade, a compra cancelada continua na tela.
- **O primeiro commit da branch marca a 041 como `done`** (mergeada em `develop` no PR #42).
- **A idade da cópia vem do dia no nome do arquivo**, não da ordem do nome: o id da conexão na frente muda quando a conexão é refeita.
- **Só o pendente é descartado.** Lançado que some da extração nova fica, porque a janela da extração pode ter encolhido.
- **A lista de descartados é um arquivo ao lado do consolidado** (`descartadas.json`), e a carga apaga só o que ela nomeia. Apagar tudo o que não veio no consolidado apagaria histórico sempre que alguém carregasse um arquivo parcial.
- **Contas entram junto**: o mesmo `dedup` ficava com a cópia mais antiga delas.

## Fase 1 — Cada lançamento vale pela cópia mais recente

Ao final: o painel mostra os lançamentos como a Pluggy os devolve hoje, e a compra pendente cancelada não soma mais.

- [x] T1.1 — Cópia mais recente e descarte do pendente na consolidação
  - Arquivos: `ingestao/pluggy_consolidate.py` (alterar)
  - O que fazer: trocar `carregar` + `dedup` por `load_snapshots`, `newest_copies` e `latest_transactions`; gravar `data/processed/descartadas.json`; contar `descartadas` no resumo e no que o comando imprime.
  - Skills: python-tipagem-estrita, python-ruff
  - Complexidade: média
- [x] T1.2 — Descarte chega ao banco
  - Arquivos: `app/ingest/source.py`, `app/ingest/loader.py`, `app/ingest/__main__.py`, `app/sync/__init__.py` (alterar)
  - O que fazer: `load_discarded(transactions_path)` lê a lista ao lado do consolidado (ausente = vazia); `ingest(..., discarded=...)` apaga essas linhas antes de contar e gravar, na mesma transação; o comando de carga e a sincronização passam a lista.
  - Skills: python-tipagem-estrita
  - Complexidade: baixa
- [x] T1.3 — Testes
  - Arquivos: `tests/test_pluggy_scripts.py`, `tests/test_ingest.py`, `tests/test_sync.py` (alterar)
  - O que fazer: regressão da cópia mais recente, do pendente descartado e do pendente sem extração mais nova; carga que apaga o descartado; leitura da lista; sincronização que remove o descartado do banco.
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `uv run pytest tests/test_pluggy_scripts.py tests/test_ingest.py tests/test_sync.py` sai com código 0, e no commit `f8bca11` falhava em `test_the_consolidation_keeps_the_latest_copy_of_each_transaction` e `test_a_pending_purchase_the_latest_snapshot_no_longer_returns_is_discarded`. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh` e `uv run pytest` saem com código 0. (comando)
- [x] CA1.3 — Nenhum `dedup` nem `carregar` em `ingestao/`. (estrutural)
- [x] CA1.4 — Consolidando o bruto de 05/09/2026 sozinho, o fluxo de 03/2026 a 08/2026 sai idêntico ao de antes da correção, e `docs/plano.md` fica como está. (comportamental)
- [x] CA1.5 — Depois de consolidar e carregar a base real pelo caminho normal, as três pendentes (R$ 125,88) não estão no banco, que fica com 2.070 lançamentos, e "OTICA BARDASSON E 05/10" está em 06/09/2026. (comportamental)

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
