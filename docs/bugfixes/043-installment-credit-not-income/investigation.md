# Investigação: crédito de parcelamento e empréstimo contam como entrada

## Relato
- **Sintoma:** em setembro de 2026 o painel mostra R$ 47.403,32 de entrada e resultado positivo de R$ 19.758,64 até o dia 25, num mês de déficit. Dentro dessa entrada estão o empréstimo consignado (R$ 32.000,00), o crédito do parcelamento de fatura do Itaú (R$ 8.579,27) e o crédito de um saldo em atraso do cartão platinum (R$ 2.425,59), cujo débito gêmeo de mesmo valor soma no gasto. O mesmo tipo de evento é tratado de três jeitos conforme a redação do banco: o crédito "CREDITO PARCELAM. TODAS FATURAS" (09/2026) e o "Crédito de parcelamento" (10/2025) contam como entrada, o "CREDITO PARCELAMENTO DA FATURA" (10/2025) fica fora; as parcelas "PARCELAM. TODAS FA01/04" contam como gasto, e as "PARCELAMEN FATURA 02/04" e "Parcelamento de Fatura" somem como se fossem pagamento de fatura.
- **Esperado:** dinheiro emprestado não é entrada. Crédito de parcelamento de fatura e de empréstimo ficam fora de entrada e de gasto; cada parcela é saída real do mês em que é cobrada, uma vez, qualquer que seja a redação. Saldo em atraso levado de uma fatura para a outra não é entrada nem gasto: só multa, juros e IOF são.
- **Como reproduzir:** consolidar os brutos atuais (`python ingestao/pluggy_consolidate.py`) e olhar a linha "Entrada CREDITO CONSIGNADO": `eh_transferencia` é `false`, e a carga a põe na entrada do mês.
- **Onde:** consolidação dos brutos da Pluggy (`ingestao/pluggy_consolidate.py`, marcação de transferências); afeta toda tela que soma entrada, gasto ou resultado do período, e o comprometido (que lê as parcelas do gasto).

## Causa raiz
A consolidação só conhece duas classes de lançamento fora do gasto: transferência entre contas próprias e pagamento de fatura. Um crédito de financiamento não é nenhuma das duas, então cai no que sobrar: vira entrada quando não acha par, e vira pagamento de fatura quando a Pluggy o põe na categoria "Credit card payment". A mesma categoria decide as parcelas: "Credit card payment" as tira do gasto, "Shopping" as deixa. Nenhuma regra olha o que o lançamento é; a classificação depende da categoria que a Pluggy escolheu para aquela redação.

O saldo em atraso do cartão chega como um crédito ("Crédito de atraso") e um débito ("Saldo em atraso") de mesmo valor na mesma conta. O pareamento só casa contas diferentes, então o crédito vira entrada e o débito vira gasto, e as compras daquela fatura, já contadas quando feitas, entram de novo.

## Evidência
- Testes de regressão (commits `0f1b995` e `8d9627d`):
  - `tests/test_pluggy_scripts.py` › `test_an_invoice_plan_credit_is_neither_income_nor_spending_whatever_its_wording` — falha nas três redações (`False` ou motivo "pagamento de fatura (categoria Pluggy)").
  - `tests/test_pluggy_scripts.py` › `test_a_payroll_loan_credit_is_not_income` — falha com `(False, '')`.
  - `tests/test_pluggy_scripts.py` › `test_an_invoice_plan_installment_is_spending_whatever_its_wording` — falha em "PARCELAMEN FATURA 02/04" e "Parcelamento de Fatura".
  - `tests/test_pluggy_scripts.py` › `test_an_invoice_plan_installment_never_pairs_with_a_credit_of_the_same_value` — a parcela casa com um Pix recebido de mesmo valor.
  - `tests/test_pluggy_scripts.py` › `test_an_overdue_balance_carried_to_the_next_bill_is_neither_income_nor_spending` — o crédito e o saldo em atraso contam.
- Medição sobre os brutos atuais (05/09 + 22/09/2026), entrada e gasto por mês:
  - 10/2025: entrada R$ 18.138,09 → R$ 14.161,71; gasto R$ 16.139,35 → R$ 17.644,45.
  - 11/2025: gasto R$ 19.002,67 → R$ 22.035,16. 12/2025: R$ 14.995,45 → R$ 18.027,94. 01/2026: R$ 22.063,83 → R$ 23.591,22.
  - 09/2026 (até 25/09): entrada R$ 47.403,32 → R$ 6.824,05; gasto R$ 27.644,68 → R$ 25.219,09; resultado +R$ 19.758,64 → −R$ 18.395,04.
- Medição sobre o bruto de 05/09/2026 sozinho, o dos números congelados em `docs/plano.md`: março a agosto de 2026 saem idênticos ao centavo (gasto de 6 meses R$ 104.197,31, déficit R$ 5.661,30/mês). Nenhum parcelamento, empréstimo ou saldo em atraso cai nessa janela.

## Correção proposta
- `ingestao/pluggy_consolidate.py` — `debt_role` classifica cada lançamento pelo que ele é, na descrição normalizada (sem acento, dígito e pontuação), antes de qualquer pareamento:
  - **crédito de financiamento**: entrada cuja descrição diz "crédito de parcelamento", "crédito consignado" ou "empréstimo", ou que a Pluggy põe em "Loans and financing". Fica fora de entrada e de gasto, com o motivo "crédito de financiamento (parcelamento de fatura ou empréstimo)".
  - **parcela de parcelamento de fatura**: saída de cartão cuja descrição começa por "parcelam… (de) (todas) fa…". É gasto, nunca pagamento de fatura nem par de transferência.
  - **saldo em atraso transportado**: "Crédito de atraso" e "Saldo em atraso" em cartão. Os dois ficam fora, com o motivo "saldo em atraso levado para a fatura seguinte"; multa, juros e IOF de atraso continuam gasto.
  - Os três ficam fora do pareamento por valor e da marcação pela categoria da Pluggy. A entrada à vista do parcelamento ("Entrada de parcelamento cartão" no banco e "pagamento parcelam. todas faturas" no cartão) não casa nenhum padrão e continua pagamento de fatura.
- **Decisão contábil:** a parcela é saída real do mês que a paga, como já são as parcelas do CDC do Duster e do financiamento imobiliário; o crédito que financia não entra em lugar nenhum. Nada conta duas vezes no mesmo lançamento: o crédito some das duas somas, cada parcela conta uma vez, a entrada à vista segue transferência. As compras da fatura parcelada continuam no mês em que foram feitas, como toda compra de cartão.
- **Fora da regra automática:** o dono já pode tirar da entrada, na tela de gastos ("Não é gasto", motivo "outro"), um crédito de empréstimo que o banco escreva de outro jeito.
- **Risco:** um Pix de terceiro com "empréstimo" na descrição sai da entrada. É o comportamento certo (dinheiro emprestado não é renda) e é reversível pela reclassificação manual.
- **Fora da correção:** `docs/plano.md` não muda (medido acima).

## Pontos em aberto
Nenhum.
