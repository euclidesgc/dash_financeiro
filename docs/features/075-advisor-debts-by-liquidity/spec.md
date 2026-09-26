# SPEC 075 — Consultor de IA: quais dívidas quitar para liberar dinheiro no mês

Desenho geral em `docs/consultor-chat.md`. Esta SPEC fixa o que a fatia 075 acrescenta às 070–074.

## Decisões

1. **`rank_by_liquidity(debts, *, today, budget_cents=None)`** em `app/debts/payoff.py`, pura sobre a
   lista de `list_debts`. O valor para quitar é o alvo de `payoff_at(debt, today)` da 074 (saldo de
   quitação informado, ou a soma nominal das parcelas que faltam); a parcela e o mês da última vêm do
   mesmo `Debt`, que lê `app/commitments/live.py::charged` e o contrato do veículo — a mesma fonte da
   projeção `schedule_by_month` da 073. Nenhuma conta de parcela ou de quitação é refeita.
2. **Entra no ranking** a dívida com primeiro vencimento, parcela, parcela a vencer e alvo maior que
   zero. O resto (cheque especial, saldo de cartão, imobiliário sem parcela) vai para `unranked` com
   o valor para quitar. O saldo de cartão fica fora porque pode conter as compras parceladas já
   listadas: somar os dois contaria o mesmo real duas vezes.
3. **Ordem:** razão parcela ÷ alvo comparada como fração exata (`Fraction`), decrescente; empate pelo
   menor alvo, depois pela chave. `freed_bp` é a razão em pontos-base arredondada meio para cima, só
   para exibição. `ceiling` marca o alvo pela soma nominal (valor para quitar nulo).
4. **Seleção com valor disponível:** gulosa na ordem do ranking, pulando o que não cabe e tentando a
   próxima; devolve escolhidas, gasto, sobra, parcela liberada no total e se alguma é estimativa pelo
   teto. Valor ≤ 0 levanta `InvalidBudgetError`.
5. **Ferramenta `debts_by_liquidity`** em `app/advisor/tools.py`, só leitura: `available_cents` e
   `limit` (1 a 50, padrão 20; a seleção considera a lista inteira). Cada valor em centavos e em
   reais, a razão em porcentagem com duas casas, a marca "estimativa pelo teto — informe o saldo de
   quitação", a lista à parte com o motivo e as parcelas sem número. Mesma lista `TOOLS` para os dois
   adaptadores.
6. **Prompt:** uma frase manda "o que quitar para liberar dinheiro" para `debts_by_liquidity`, na
   ordem que ela devolve, repetindo a marca de estimativa.
7. **Tela:** só o rótulo da ferramenta na nota da resposta.

## Arquivos

Backend: `app/debts/payoff.py`, `app/advisor/tools.py`, `app/advisor/chat.py`. Testes:
`tests/test_debts_payoff.py`, `tests/test_advisor_tools.py`, `tests/test_advisor_chat.py`,
`tests/test_advisor_providers.py`. Front: `src/features/advisor/components/chat-message-item.tsx` e o
teste dele. Docs: `docs/consultor-chat.md`, `docs/roadmap.md`.

## Skills

python-*, component-testing.
