# Veredicto — 003-comprometido, fase 1 (primeira rodada)

VEREDICTO: REPROVADO

Portões: `pytest -q` → `277 passed`, exit 0; `gates_runner.sh` → limpo.
Lint não executável — o projeto não registra linter nem typechecker.

Doze dos catorze critérios cumpridos, medidos por execução direta contra o banco:
tabelas e colunas (`2 14`), migrações anteriores intactas, vocabulário fora do
código, sinal e exclusões (`152 9 0 0`), chave de série normalizada, atomicidade
com rollback, recorrentes (`55 -1242782 -246720 9 4 2026-08 DEBITO PRESTACAO
HAB`), assinaturas (`1 0 -224569`), janela e precedência (`96 6 -37482 0 2 0`),
término e restantes (`22 2028-06 2 2026-10 2`), dia sempre observado (`0 0`),
mediana e dia inexistente.

  [ ] RF-03 — o comando do critério aborta:
      `ImportError: cannot import name 'calendar' from 'app.commitments.schedule'`.
      A metade que existe responde certo — `installments(today=2026-09-05)` → 6 e
      `installments(today=2027-03-01)` → 0 —, mas `calendar` não foi escrita.
      **O critério é que estava errado**: `calendar` é entrega da fase 3, e o
      critério da fase 1 não podia depender dela.

  [ ] RF-06/07 — `wc -l` imprime `151`; o critério exigia `155`.
      Contradição aritmética dentro do próprio bloco: RF-09 exige 55 recorrentes
      e RF-12 exige 96 parcelamentos, e 55 + 96 = 151. Conferido no banco:
      `installment 96 / recurring 55`, total `151`, arquivo sem cabeçalho.
      **O 155 é que precisava ser reconciliado.**

Apontamento aproveitado: `app/commitments/engine.py:70` — `main()` chama
`recompute(conn)` sem `today`, então a janela de vida do CLI segue o relógio da
máquina. Hoje coincide com a data de referência; num dia diferente o mesmo
comando produz outro conjunto de série viva sem nada ter mudado no banco.
