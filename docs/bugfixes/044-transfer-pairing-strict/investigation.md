# Investigação: transferência entre contas próprias pareada sem prova

## Relato
- **Sintoma:** em julho de 2026 o painel não mostra a compra de R$ 100,00 no posto (cartão Itaú, 22/07) no gasto nem o Pix de R$ 100,00 recebido de terceiro no Nubank (20/07) na entrada: os dois aparecem como "transferência entre contas próprias". Em dezembro de 2025 acontece o mesmo com um Pix de R$ 110,00 enviado a um pet shop e uma transferência de R$ 110,00 recebida de outra pessoa. Em novembro de 2025 é o contrário: o saque de R$ 2.000,00 na CAIXA conta como gasto, embora o mesmo dinheiro tenha sido depositado no Itaú no mesmo dia, e o depósito já esteja fora da entrada.
- **Esperado:** só sai de entrada e de gasto o par que tem sinal de que o dinheiro ficou com o dono: pagamento de fatura (o cartão diz "pagamento"), devolução de saldo credor do cartão, transferência que a Pluggy marca como da mesma pessoa ou que traz o nome do titular nos dois lados, e saque depositado em outra conta própria. Compra no cartão nunca casa com Pix recebido de terceiro. Entre vários pares possíveis, fica o mais próximo na data.
- **Como reproduzir:** consolidar os brutos atuais (`python ingestao/pluggy_consolidate.py`) e procurar "POSTO DE GASOLINA VIAITABORAIBRA" de 22/07/2026: `eh_transferencia` é `true`, com o motivo "transferência entre contas próprias".
- **Onde:** consolidação dos brutos da Pluggy (`ingestao/pluggy_consolidate.py`, pareamento em `marcar_transferencias`); afeta toda tela que soma entrada, gasto ou resultado do período.

## Causa raiz
O pareamento agrupa os lançamentos pelo valor e casa cada débito com o primeiro crédito de outra conta até 3 dias de distância. Não olha o que os lançamentos são: tipo de conta, descrição, categoria da Pluggy e titular não entram na decisão. Qualquer coincidência de valor vira transferência, e os dois lados somem das somas. O motivo também sai da coincidência: todo crédito em cartão vira "pagamento de fatura", até o reembolso de uma compra.

O primeiro crédito da lista, e não o mais próximo, é escolhido; com três lançamentos de mesmo valor, o par pode ficar trocado.

Depois do pareamento, a marcação pela categoria da Pluggy desfaz a transferência de todo saque, pareado ou não. O saque de R$ 2.000,00 depositado no Itaú no mesmo dia volta ao gasto, e o depósito continua fora da entrada: o mês perde R$ 2.000,00 que não saíram de casa.

## Evidência
- Testes de regressão (commit `ddca97f`), em `tests/test_pluggy_scripts.py`:
  - `test_a_card_purchase_never_pairs_with_a_pix_received_from_a_third_party` — a compra no posto e o Pix recebido saem como transferência.
  - `test_a_pix_to_a_shop_never_pairs_with_a_transfer_received_from_a_third_party` — o Pix ao pet shop e a transferência recebida saem como transferência.
  - `test_a_card_refund_never_pairs_with_a_bank_payment_to_a_third_party` — o reembolso no cartão vira "pagamento de fatura".
  - `test_cash_withdrawn_and_deposited_in_another_own_account_is_neither_spending_nor_income` — o saque pareado volta a `(False, '')`.
  - `test_a_debit_pairs_with_the_closest_credit_of_the_same_value` — o débito casa com o crédito de três dias antes, não com o do mesmo dia.
  - Os pares legítimos (Pix e TED entre contas do titular, com e sem a categoria da Pluggy; quatro formas de pagamento de fatura; devolução de saldo credor) já passavam e continuam passando: `test_a_transfer_between_own_accounts_still_pairs`, `test_a_bill_payment_still_pairs_with_the_card_credit`, `test_a_card_credit_balance_returned_to_the_bank_still_pairs`.
- Medição sobre os brutos atuais (05/09 + 22/09/2026): dos 76 pares de hoje, 74 continuam iguais; saem os de R$ 100,00 (07/2026) e R$ 110,00 (12/2025), e o par do saque de R$ 2.000,00 com o depósito (11/2025) deixa de ser desfeito. Entrada e gasto por mês:
  - 11/2025: gasto R$ 22.035,16 → R$ 20.035,16.
  - 12/2025: entrada R$ 14.490,75 → R$ 14.600,75; gasto R$ 18.027,94 → R$ 18.137,94.
  - 07/2026: entrada R$ 9.123,52 → R$ 9.223,52; gasto R$ 15.684,28 → R$ 15.784,28.
  - 09/2026: igual (entrada R$ 6.824,05, gasto R$ 25.219,09).
- Medição sobre o bruto de 05/09/2026 sozinho, o dos números congelados em `docs/plano.md`: gasto de 6 meses (03 a 08/2026) R$ 104.197,31 → R$ 104.297,31; déficit de 04 a 08/2026 igual, R$ 5.661,30/mês, porque o Pix de R$ 100,00 volta à entrada do mesmo mês.

## Correção proposta
- `ingestao/pluggy_consolidate.py` — `pair_reason` só aceita o par com prova de que o dinheiro ficou com o dono, e dá o motivo pelo que o par é:
  - **crédito no cartão** (pagamento de fatura): a descrição do lado do cartão diz "pagamento" ou "pagto".
  - **débito no cartão**: só a devolução de saldo credor ("DEVOLUCAO SALDO CREDOR"). Compra no cartão nunca casa.
  - **cartão com cartão**: nunca.
  - **entre contas bancárias**: os dois lados são do titular — categoria "Same person transfer" da Pluggy ou o nome do titular (campo `owner` das contas, com pelo menos dois nomes) na descrição ou no recebedor —, ou saque ("Same person transfer - CASH") casado com depósito em dinheiro ("Transfer - Cash").
- O pareamento monta todos os pares válidos de um valor e fica com os mais próximos na data, sem repetir lançamento.
- Saque pareado com depósito continua transferência e continua marcado como saque; o saque sem par segue como gasto.
- **Risco:** transferência entre contas próprias que a Pluggy não marca como da mesma pessoa e cuja descrição não traz o nome do titular deixa de ser pareada e passa a contar. Nos brutos atuais não há nenhuma; se aparecer, o dono já a tira da soma na tela de gastos ("Não é gasto").
- `docs/plano.md` e `tests/test_frozen_numbers.py` — o gasto de 6 meses passa a R$ 104.297,31 (norma 28), com a nota do número antigo e da causa. O número de transferências entre contas próprias (R$ 20.272,00) não se reproduz a partir do consolidado atual em nenhuma janela de meses e fica como está.

## Pontos em aberto
Nenhum.
