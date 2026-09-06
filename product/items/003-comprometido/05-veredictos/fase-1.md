# Veredicto — 003-comprometido, fase 1

VEREDICTO: APROVADO

> Segunda rodada, validador novo. A primeira reprovou por dois critérios errados
> — um dependia de `calendar`, que é entrega da fase 3, e outro exigia 155 séries
> onde a própria aritmética do bloco dá 151. Ver `fase-1-reprovada-1.md`.

Portões: `pytest -q` → `281 passed`, exit 0; `gates_runner.sh` → limpo (189
arquivos). Lint N/A — o projeto não registra linter nem typechecker.

Critérios (todos os catorze cumpridos, com a saída real):
  [x] RF-01 tabelas e colunas → `2 14`; migrações anteriores intactas (`0 0 0`)
  [x] RF-02/26/37 vocabulário fora do código → nenhuma linha, com controle
      provando que o grep varria de fato
  [x] RF-03 → `6 0`: a mesma base lida em 2026-09-05 e em 2027-03-01 devolve
      conjuntos diferentes de parcelamento vivo
  [x] RF-04 → `152 9 0 0`
  [x] RF-05 → `1 otica bardasson e 1`
  [x] RF-06/07 → duas recomputações, `diff` vazio, `wc -l` `151`, marca de
      dispensa sobrevivendo (`1`)
  [x] RF-08 atomicidade → `2 passed`, e o validador reproduziu o rollback por
      fora: `before 151 / raised / after 151 / rows identical: True`, conferido
      em conexão nova reaberta — o rollback é real em disco
  [x] RF-09/10 → `55 -1242782 -246720 9 4 2026-08 DEBITO PRESTACAO HAB`
  [x] RF-11 → `1 0 -224569`
  [x] RF-12/13/16/17 → `96 6 -37482 0 2 0`
  [x] RF-14/15 → `22 2028-06 2 2026-10 2`
  [x] RF-18 → `0 0`
  [x] RF-19/20 → `13 passed`, com `median_day([10,12,20,22]) = 12` e
      `on_month(31, 2026-11-01) = 2026-11-30` avaliados também por fora

Apontamentos
  **O envelope vazou.** O branch sob revisão carrega `01-brief.md`, `03-plan.md`
  e — pior — `05-veredictos/fase-1-reprovada-1.md`, o veredicto anterior desta
  mesma fase. O validador não abriu nenhum, só leu os nomes no `git diff --stat`.
  A cegueira valeu por disciplina dele, não por construção: um validador menos
  disciplinado passaria a conferir "corrigiram o que reprovou?" no lugar de "o
  critério foi cumprido?". O ponteiro precisa ser o diff restrito aos caminhos de
  código, não o branch inteiro.

  Sobre a data, sem defeito: a base nasceu com `reference=2026-09-06` (relógio do
  ambiente) e o validador a reconstruiu com `DASH_TODAY=2026-09-05` — todos os
  números congelados deram exatamente as mesmas linhas. Testou ainda
  `DASH_TODAY=2026-11-15`, e RF-09/10 seguiu em `55 -1242782`.
