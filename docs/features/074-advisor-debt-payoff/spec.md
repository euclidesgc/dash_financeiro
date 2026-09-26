# SPEC 074 — Consultor de IA: quanto juntar para quitar uma dívida

Desenho geral em `docs/consultor-chat.md`. Esta SPEC fixa o que a fatia 074 acrescenta às 070–073.

## Decisões

1. **Módulo `app/debts/payoff.py`**, sem escrita. `list_debts(conn, *, today)` junta as dívidas da
   escada (`ladder` e `without_rate` de `app/debts/ladder.py`), o contrato do veículo de
   `app/financings/store.py` com o saldo de quitação `quitacao-cdc` de `plan_facts`, e as compras
   parceladas de `app/commitments/live.py::charged` com parcela numerada e parcela a vencer. Cada
   dívida tem uma chave estável na conversa: `debt-<id>` ou `installment-<id>`.
2. **`payoff_at(debt, day, *, today)`** devolve o valor para quitar na data, a soma nominal das
   parcelas que faltam, quantas faltam, o mês da última e a base do valor:
   - cheque especial, saldo de cartão e imobiliário: o saldo (`balance`), igual em qualquer data,
     porque o painel não sabe como ele muda;
   - compra parcelada: a soma nominal das parcelas que faltam (`nominal`); o desconto de antecipação
     só o emissor informa;
   - financiamento do veículo: o saldo de quitação informado (`informed`) só no mês corrente e dentro
     da validade; fora disso, valor nulo, a soma nominal como alvo e o pedido para informar o saldo
     na tela Dívidas (norma 26). O valor presente pela taxa do contrato (`present_value_cents`) não
     entra: seria um desconto estimado pelo painel.
   As parcelas vencidas até a data contam como pagas, por `app/financings/math.py::remaining_months`;
   a compra parcelada ganha um primeiro vencimento datado para trás a partir da última parcela vista.
3. **`saving_plan(debt, *, today, target_date=None, monthly_saving_cents=None)`**, um dos dois.
   Com data: depósitos = meses entre hoje e a data; data no mês corrente pede o valor inteiro agora;
   data no passado levanta `PastTargetError`; valor mensal arredondado para cima. Com valor mensal:
   o primeiro mês em que `valor × meses` cobre o valor para quitar do fim daquele mês, até 600 meses;
   zero ou negativo levanta `InvalidSavingError`. As parcelas seguem sendo pagas à parte.
4. **Valores positivos** nesta saída: são quanto juntar, não um lançamento.
5. **Ferramenta `debt_payoff`** em `app/advisor/tools.py`: sem `debt`, lista as dívidas e o que não
   se listou (parcela sem número); com `debt` (chave ou parte do nome), o valor de hoje e, com
   `target_date`, `months` (1 a 360) ou `monthly_saving_cents`, o plano. Cada valor em centavos e em
   reais para a guarda de números. Mesma lista `TOOLS` para os dois adaptadores.
6. **Prompt:** uma frase manda as perguntas de quitação para `debt_payoff` e proíbe estimar desconto.
7. **Tela:** só o rótulo da ferramenta na nota da resposta.

## Arquivos

Backend: `app/debts/payoff.py` (criar), `app/advisor/tools.py`, `app/advisor/chat.py`. Testes:
`tests/test_debts_payoff.py` (criar), `tests/test_advisor_tools.py`, `tests/test_advisor_chat.py`,
`tests/test_advisor_providers.py`. Front: `src/features/advisor/components/chat-message-item.tsx` e
o teste dele. Docs: `docs/consultor-chat.md`, `docs/roadmap.md`.

## Skills

python-*, component-testing.
