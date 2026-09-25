# PLAN 045 — refund-same-account

Branch: `bugfix/045-refund-same-account`

Decisões registradas aqui (a causa está em `investigation.md`):

- **Uma fase só**: a regra mora toda na consolidação; a carga já grava `is_refund` e `refunded_by` a cada reingestão.
- **O primeiro commit da branch marca a 044 como `done`** (mergeada em `develop` no PR #45).
- **Estorno só anula gasto da mesma conta**: o banco devolve o dinheiro onde cobrou.
- **Transferência e pagamento de fatura não são gasto**, então não há o que estornar neles; ficam fora do casamento.
- **O estabelecimento vem antes da data**: com dois débitos de mesmo valor, o que o estorno cita ganha do mais recente.
- **O estorno sem par continua fora de entrada e de gasto**, como hoje: devolve um gasto anterior ao que a Pluggy entrega.

## Fase 1 — Estorno casado só na mesma conta

Ao final: o estorno da anuidade de 30/10/2025 não anula mais o boleto do Itaú; os estornos que casam certo hoje continuam iguais.

- [x] T1.1 — Regra de casamento de estorno
  - Arquivos: `ingestao/pluggy_consolidate.py` (alterar)
  - O que fazer: `netar_estornos` filtra por conta e tira transferências; escolhe primeiro o débito que compartilha uma palavra de estabelecimento com o estorno, depois o mais recente.
  - Skills: python-tipagem-estrita, python-ruff
  - Complexidade: baixa
- [x] T1.2 — Testes
  - Arquivos: `tests/test_pluggy_scripts.py` (alterar)
  - O que fazer: regressão do caso real (estorno no cartão × boleto no banco), da anuidade no próprio cartão contra Pix posterior no banco, da preferência pelo estabelecimento, da transferência na mesma conta, e dos quatro casamentos reais corretos.
  - Skills: python-testes-unitarios
  - Complexidade: baixa

### Critérios de aceite da fase 1

- [x] CA1.1 — `uv run pytest tests/test_pluggy_scripts.py` sai com código 0, e no commit `2f1b777` falhava em `test_a_card_refund_never_cancels_a_bill_payment_in_the_bank`, `test_a_card_refund_cancels_the_charge_of_its_own_card_not_a_later_bank_debit`, `test_a_refund_prefers_the_debit_of_the_same_merchant_over_a_later_one` e `test_a_refund_never_cancels_a_transfer_in_its_own_account`. (comando)
- [x] CA1.2 — `bash scripts/lint.sh`, `bash scripts/gates/gates_runner.sh` e `uv run pytest` saem com código 0. (comando)
- [x] CA1.3 — Em `ingestao/pluggy_consolidate.py`, `netar_estornos` só aceita candidato com o mesmo `conta_id` do estorno e com `eh_transferencia` falso. (estrutural)
- [x] CA1.4 — Consolidando o bruto de 05/09/2026 sozinho, o gasto de 03/2026 a 08/2026 segue R$ 104.297,31 e o déficit de 04 a 08/2026 segue R$ 5.661,30/mês. (comportamental)
- [x] CA1.5 — Depois de consolidar e carregar a base real pelo caminho normal, "Pagamento de boleto INT PASSAI ITAU" de 26/10/2025 tem `refunded_by` vazio, o estorno de 30/10/2025 segue com `is_refund` 1, e entrada e gasto de todos os meses são os mesmos de antes da carga. (comportamental)

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
