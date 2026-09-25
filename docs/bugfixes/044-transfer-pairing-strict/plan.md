# PLAN 044 — transfer-pairing-strict

Branch: `bugfix/044-transfer-pairing-strict`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: a regra mora toda na consolidação; a carga já grava `is_transfer` e `transfer_reason` a cada reingestão.
- **O primeiro commit da branch marca a 043 como `done`** (mergeada em `develop` no PR #44).
- **O par exige prova, e o motivo sai da prova**: coincidência de valor e data não diz nada; o lado do cartão diz "pagamento", o cartão devolve saldo credor, ou os dois lados bancários são do titular.
- **O titular vem do campo `owner` das contas da Pluggy**, não de constante no código: o nome muda por instituição ("Euclides Catunda" no Nubank) e cada forma entra.
- **Fica o par mais próximo na data**, entre todos os válidos de um valor.
- **O saque depositado em outra conta própria entra junto**: é o mesmo pareamento desfeito pela marcação de categoria, achado na medição.

## Fase 1 — Transferência só com prova de conta própria

Ao final: compra no cartão e Pix de terceiro de mesmo valor contam no gasto e na entrada; os pagamentos de fatura, as transferências do titular e a devolução de saldo credor continuam fora das somas.

- [x] T1.1 — Regra de pareamento na consolidação
  - Arquivos: `ingestao/pluggy_consolidate.py` (alterar)
  - O que fazer: `pair_reason` aceita o par só com prova e devolve o motivo; o pareamento escolhe os pares mais próximos na data; o saque pareado com depósito não é desfeito pela marcação de categoria.
  - Skills: python-tipagem-estrita, python-ruff
  - Complexidade: baixa
- [x] T1.2 — Testes
  - Arquivos: `tests/test_pluggy_scripts.py` (alterar)
  - O que fazer: regressão dos pares falsos reais (posto × Pix de terceiro, Pix ao pet shop × transferência de terceiro, reembolso no cartão × Pix a loja), do saque depositado, do par mais próximo, e dos pares legítimos reais que continuam pareando.
  - Skills: python-testes-unitarios
  - Complexidade: baixa
- [x] T1.3 — Números congelados
  - Arquivos: `docs/plano.md` (alterar), `tests/test_frozen_numbers.py` (alterar)
  - O que fazer: gasto de 6 meses R$ 104.197,31 → R$ 104.297,31, com nota do número antigo e da causa; `10429731` e `104297` na varredura de números congelados.
  - Skills: —
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `uv run pytest tests/test_pluggy_scripts.py` sai com código 0, e no commit `ddca97f` falhava em `test_a_card_purchase_never_pairs_with_a_pix_received_from_a_third_party`, `test_a_pix_to_a_shop_never_pairs_with_a_transfer_received_from_a_third_party`, `test_a_card_refund_never_pairs_with_a_bank_payment_to_a_third_party`, `test_cash_withdrawn_and_deposited_in_another_own_account_is_neither_spending_nor_income` e `test_a_debit_pairs_with_the_closest_credit_of_the_same_value`. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh` e `uv run pytest` saem com código 0. (comando)
- [x] CA1.3 — Em `ingestao/pluggy_consolidate.py`, nenhum par débito × crédito é marcado sem passar por `pair_reason`, e nenhum crédito em cartão vira "pagamento de fatura" só por estar em cartão. (estrutural)
- [x] CA1.4 — Consolidando o bruto de 05/09/2026 sozinho, o gasto de 03/2026 a 08/2026 é R$ 104.297,31 e o déficit de 04 a 08/2026 é R$ 5.661,30/mês, e `docs/plano.md` traz o gasto novo ao lado do antigo. (comportamental)
- [x] CA1.5 — Depois de consolidar e carregar a base real pelo caminho normal, "POSTO DE GASOLINA VIAITABORAIBRA" de 22/07/2026 está no gasto e o Pix de R$ 100,00 de 20/07/2026 na entrada; julho de 2026 tem entrada R$ 9.223,52 e gasto R$ 15.784,28; setembro de 2026 segue com entrada R$ 6.824,05 e gasto R$ 25.219,09. (comportamental)

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
