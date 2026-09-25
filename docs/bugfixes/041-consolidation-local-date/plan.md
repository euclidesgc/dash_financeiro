# PLAN 041 — consolidation-local-date

Branch: `bugfix/041-consolidation-local-date`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: uma função de conversão e dois pontos de uso.
- **O primeiro commit da branch marca a 040 como `done`** (mergeada em `develop` no PR #41).
- **`zoneinfo` da biblioteca padrão**, sem dependência nova: o fuso vem da base de fusos do sistema, presente no ambiente local e no CI.
- **O inventário da extração entra junto**: é o mesmo corte em UTC, no arquivo ao lado.
- **Reconciliação medida sobre o bruto de 05/09/2026**, com a mesma conta que produziu os números congelados (reproduzida ao centavo antes da mudança).

## Fase 1 — A data do lançamento é o dia em São Paulo

Ao final: um lançamento feito às 23:59 do dia 31 entra no dia 31 e no mês dele, em toda tela.

- [x] T1.1 — Conversão do instante para o dia local
  - Arquivos: `ingestao/pluggy_consolidate.py` (alterar), `ingestao/pluggy_extract.py` (alterar)
  - O que fazer: `local_date(instant: str | None) -> str` devolve `""` para ausência, converte instante com fuso para `America/Sao_Paulo` e devolve o `date().isoformat()`; instante sem fuso é tomado como local. Mora na consolidação, que roda como script sem importar outro módulo do projeto. A coluna `data` da consolidação e a primeira e última data do inventário passam a usá-la.
  - Skills: python-tipagem-estrita, python-ruff
  - Complexidade: baixa
- [x] T1.2 — Reconciliação dos números de referência
  - Arquivos: `docs/plano.md` (alterar), `tests/test_frozen_numbers.py` (alterar)
  - O que fazer: trocar déficit, gasto de 6 meses e faixa de renda pelos valores medidos, com nota do número antigo, do novo e da causa; incluir `10419731` e `104197` na varredura de números congelados.
  - Complexidade: baixa
- [x] T1.3 — Testes
  - Arquivos: `tests/test_pluggy_scripts.py` (alterar)
  - O que fazer: o teste de regressão parametrizado cobre fim de mês às 23:59, noite do dia 31, meia-noite local e madrugada; um teste de `local_date` cobre ausência e valor sem fuso.
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `uv run pytest tests/test_pluggy_scripts.py -k sao_paulo` sai com código 0, e o mesmo comando antes da correção falhava em `2026-04-01T02:59:00.000Z` e `2026-09-01T01:25:35.091Z`. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh` e `uv run pytest` saem com código 0. (comando)
- [x] CA1.3 — Nenhum `[:10]` sobre data da Pluggy em `ingestao/`. (estrutural)
- [x] CA1.4 — Consolidando o bruto de 05/09/2026, o fluxo de 03/2026 a 08/2026 dá gasto R$ 104.197,31 e déficit de 04 a 08/2026 de R$ 5.661,30/mês, e `docs/plano.md` traz esses valores ao lado dos antigos. (comportamental)
- [x] CA1.5 — Depois de consolidar e carregar a base real pelo caminho normal, o salário de R$ 2.928,46 aparece em 31/03/2026 no banco. (comportamental)

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
