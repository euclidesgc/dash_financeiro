# Investigação: estorno casado com débito de outra conta

## Relato
- **Sintoma:** o estorno da anuidade do cartão Passai de 30/10/2025 (R$ 16,65) aparece anulando o pagamento de boleto "Pagamento de boleto INT PASSAI ITAU" de 26/10/2025, lançado na conta corrente Itaú. Um estorno no cartão não devolve dinheiro de um boleto pago no banco: se esse débito fosse um gasto de verdade, ele sumiria do total, e a anuidade que o estorno de fato devolve continuaria contando como gasto.
- **Esperado:** o estorno só anula um gasto da mesma conta, lançado antes dele. Entre vários possíveis, fica o do mesmo estabelecimento e, depois, o mais recente. Transferência entre contas próprias e pagamento de fatura nunca são anulados por estorno. Sem débito que sirva, o estorno fica sozinho e continua fora de entrada e de gasto.
- **Como reproduzir:** consolidar os brutos atuais (`python ingestao/pluggy_consolidate.py`) e procurar "ESTORNO ANUIDADE DIFERENCIADA M RENOV" de 30/10/2025: `estornada_por` aponta para o boleto do Itaú de 26/10/2025.
- **Onde:** consolidação dos brutos da Pluggy (`ingestao/pluggy_consolidate.py`, casamento em `netar_estornos`); a carga grava o resultado em `is_refund` e `refunded_by`, que tiram o par das somas de entrada e de gasto.

## Causa raiz
O casamento procura, em todas as contas, o débito de mesmo valor lançado até a data do estorno e fica com o mais recente. Não olha a conta nem o que o débito é: um boleto pago no banco, um Pix a terceiro ou uma transferência entre contas próprias servem, desde que o valor bata e a data seja a mais próxima. A descrição também não entra: com dois débitos de mesmo valor na conta, ganha o mais recente, mesmo que o estorno cite o outro estabelecimento.

## Evidência
- Testes de regressão (commit `2f1b777`), em `tests/test_pluggy_scripts.py`:
  - `test_a_card_refund_never_cancels_a_bill_payment_in_the_bank` — o caso real de 10/2025: o estorno no cartão anula o boleto do Itaú.
  - `test_a_card_refund_cancels_the_charge_of_its_own_card_not_a_later_bank_debit` — com a anuidade no cartão e um Pix de mesmo valor no banco depois dela, o estorno anula o Pix e a anuidade fica no gasto.
  - `test_a_refund_prefers_the_debit_of_the_same_merchant_over_a_later_one` — "Estorno de compra débito QUICOPAO" anula a compra de outra loja, por ser mais recente.
  - `test_a_refund_never_cancels_a_transfer_in_its_own_account` — o estorno anula o Pix a conta própria em vez da compra.
  - Os casamentos reais corretos de hoje continuam iguais: `test_a_refund_still_cancels_the_charge_it_returns` (anuidade 04/12 × estorno de 29/11/2025, Selfit × "Estorno de compra" no cartão, pizzaria × estorno no débito do Itaú, prestação habitacional × estorno na CAIXA).
- Medição sobre os brutos atuais (05/09 + 22/09/2026): dos 9 estornos, 8 continuam com o mesmo par; o de 30/10/2025 fica sem par, porque a anuidade que ele devolve (parcela 03/12) é anterior ao primeiro lançamento do cartão Passai que a Pluggy entrega (06/10/2025). O boleto do Itaú já estava fora das somas como pagamento de fatura, e o estorno sem par também fica fora: entrada e gasto de todos os meses ficam iguais.
- Medição sobre o bruto de 05/09/2026 sozinho, o dos números congelados em `docs/plano.md`: gasto de 6 meses (03 a 08/2026) R$ 104.297,31 e déficit de 04 a 08/2026 R$ 5.661,30/mês, iguais aos de hoje. `docs/plano.md` não muda.

## Correção proposta
- `ingestao/pluggy_consolidate.py` — `netar_estornos` só considera débito da mesma conta do estorno, que não seja transferência nem pagamento de fatura, lançado até a data do estorno. Entre os possíveis, prefere o que tem na descrição ou no nome do estabelecimento uma palavra do estorno (fora "estorno", "compra", "débito" e "crédito"), aceitando uma ser o começo da outra porque o banco corta os dois lados em larguras diferentes; depois, o mais recente.
- **Risco:** estorno lançado numa conta diferente da do gasto (por exemplo, compra no débito devolvida no cartão) deixa de anular o gasto. Nos brutos atuais não há nenhum; se aparecer, o dono tira o gasto da soma na tela de gastos ("Não é gasto").

## Pontos em aberto
Nenhum.
