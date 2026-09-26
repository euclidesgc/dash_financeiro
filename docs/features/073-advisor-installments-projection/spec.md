# SPEC 073 — Consultor de IA: projeção de parcelas, financiamentos e contas recorrentes

Desenho geral em `docs/consultor-chat.md`. Esta SPEC fixa o que a fatia 073 acrescenta às 070–072.

## Decisões

1. **Função `app/projection/schedule.py::schedule_by_month(conn, *, today, months=6)`**, pura sobre
   o banco, sem escrita. Janela de 1 a 24 meses a partir do mês seguinte à data de referência (o mês
   corrente já está parcialmente pago). Devolve `Schedule` com os meses (total por origem, total do
   mês, o que termina), as linhas rastreáveis, o que não se projetou e o total da janela.
2. **Compras parceladas** vêm de `app/commitments/live.py::charged` (séries do tipo parcela com
   cobrança dentro da janela viva). O número da parcela em cada mês sai da última parcela vista:
   `k = última_parcela + meses entre a última cobrança e o mês`, e conta enquanto `1 ≤ k ≤ n`. Não
   usa `installments_left`, porque a fatura do cartão lança todas as parcelas futuras de uma vez e a
   série "sem parcela restante" ainda tem cobranças datadas dentro da janela. Série sem número de
   parcela vai para `unprojected`.
3. **Financiamentos** vêm de `app/financings/store.py::read_all`: com valor de parcela e primeiro
   vencimento, `k = meses desde o primeiro vencimento + 1`, até o prazo. Sem valor de parcela (o
   imobiliário hoje), vai para `unprojected`: derivar a parcela de saldo e taxa escolheria um sistema
   de amortização que o painel não conhece (norma 26: o valor é parâmetro da tela Configuração).
4. **Contas recorrentes** vêm de `app/commitments/live.py::subscriptions`, só vivas e não
   dispensadas, com o valor médio da série em todos os meses. A série cujo valor fica a até 2%
   (`SAME_PURCHASE_DEVIATION` de `app/commitments/series.py`) da parcela de um financiamento é o
   boleto desse financiamento: sai das recorrentes e fica registrada em `replaces` da linha do
   contrato, que ganha porque sabe quando termina.
5. **Ferramenta `commitments_by_month`** em `app/advisor/tools.py`, entrada `months` (1 a 24, padrão
   6). Saída com cada valor em centavos e em reais (`brl`), para a guarda de números aceitar o que o
   modelo copiar: total por origem e do mês, total da janela, valor e total na janela de cada linha.
   `ToolContext` ganha `today` (a data de referência que `send` já recebe). A lista `TOOLS` é a mesma
   para os dois adaptadores, então Anthropic e Gemini recebem a ferramenta sem mudança neles.
6. **Prompt:** uma frase manda perguntas de parcela, financiamento ou conta recorrente dos próximos
   meses para `commitments_by_month`. As palavras "fixa" e "variável" ficam fora do texto do código
   por serem termos do vocabulário da taxonomia (`tests/test_taxonomy_literals.py`).
7. **Tela:** só o rótulo da ferramenta na nota da resposta ("consultou as parcelas e contas dos
   próximos meses"). Tabela estruturada fica fora: a resposta em texto com hífens já traz os meses.

## Arquivos

Backend: `app/projection/schedule.py` (criar), `app/advisor/tools.py`, `app/advisor/chat.py`.
Testes: `tests/test_projection_schedule.py` (criar), `tests/test_advisor_tools.py`,
`tests/test_advisor_chat.py`, `tests/test_advisor_providers.py`, `tests/test_advisor_proposals.py`.
Front: `src/features/advisor/components/chat-message-item.tsx` e o teste dele. Docs:
`docs/consultor-chat.md`.

## Skills

python-*, component-testing.
