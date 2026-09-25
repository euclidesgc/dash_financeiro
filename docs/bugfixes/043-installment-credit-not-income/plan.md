# PLAN 043 — installment-credit-not-income

Branch: `bugfix/043-installment-credit-not-income`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: a regra mora toda na consolidação; a carga já grava `is_transfer` e `transfer_reason` a cada reingestão.
- **O primeiro commit da branch marca a 042 como `done`** (mergeada em `develop` no PR #43).
- **Classifica-se pelo que o lançamento é, não pela categoria da Pluggy**: a Pluggy põe o mesmo evento em três categorias conforme a redação do banco.
- **O crédito fica fora pelo mesmo caminho das transferências** (`is_transfer` com motivo próprio): é o predicado que já tira um lançamento de entrada e de gasto em todas as consultas, e não pede migração.
- **A parcela é gasto**, como as parcelas dos outros financiamentos; o crédito que a financia não entra em lugar nenhum.
- **O saldo em atraso transportado entra junto**: é o mesmo defeito ao lado (crédito que não é entrada somado com um débito que não é gasto), achado na medição.

## Fase 1 — Dinheiro emprestado não é entrada

Ao final: o resultado de setembro de 2026 deixa de contar o consignado, o crédito do parcelamento e o crédito do saldo em atraso como entrada, e toda parcela de parcelamento de fatura conta como gasto no mês em que é cobrada.

- [x] T1.1 — Regra de financiamento na consolidação
  - Arquivos: `ingestao/pluggy_consolidate.py` (alterar)
  - O que fazer: `debt_role` classifica crédito de financiamento, parcela de parcelamento de fatura e saldo em atraso transportado; o pareamento por valor e a marcação pela categoria da Pluggy os ignoram; `marcar_financiamentos` tira o crédito e o saldo em atraso de entrada e de gasto com motivo próprio; o resumo conta os créditos de financiamento.
  - Skills: python-tipagem-estrita, python-ruff
  - Complexidade: baixa
- [x] T1.2 — Testes
  - Arquivos: `tests/test_pluggy_scripts.py` (alterar)
  - O que fazer: regressão das três redações do crédito, do consignado, das três redações da parcela, da parcela que não casa com Pix de mesmo valor, do saldo em atraso e da entrada à vista que continua pagamento de fatura.
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `uv run pytest tests/test_pluggy_scripts.py` sai com código 0, e no commit `0f1b995` falhava em `test_an_invoice_plan_credit_is_neither_income_nor_spending_whatever_its_wording`, `test_a_payroll_loan_credit_is_not_income`, `test_an_invoice_plan_installment_is_spending_whatever_its_wording` e `test_an_invoice_plan_installment_never_pairs_with_a_credit_of_the_same_value`. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh` e `uv run pytest` saem com código 0. (comando)
- [x] CA1.3 — Nenhuma regra de `ingestao/pluggy_consolidate.py` decide crédito de financiamento ou parcela de parcelamento pela categoria "Credit card payment". (estrutural)
- [x] CA1.4 — Consolidando o bruto de 05/09/2026 sozinho, o fluxo de 03/2026 a 08/2026 sai idêntico ao de antes da correção, e `docs/plano.md` fica como está. (comportamental)
- [x] CA1.5 — Depois de consolidar e carregar a base real pelo caminho normal, a entrada de setembro de 2026 até 25/09 é R$ 6.824,05 e o gasto R$ 25.219,09; "Entrada CREDITO CONSIGNADO" e "CREDITO PARCELAM. TODAS FATURAS" estão fora das duas somas, e as quatro "PARCELAM. TODAS FA0n/04" estão no gasto. (comportamental)

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
