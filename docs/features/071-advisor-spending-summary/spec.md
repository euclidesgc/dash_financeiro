# SPEC 071 — Consultor de IA: resumo de gastos por categoria e mês a mês

Desenho geral em `docs/consultor-chat.md`. Esta SPEC fixa o que a fatia 071 acrescenta à 070.

## Decisões

1. **Função nova `monthly_totals`** em `app/queries/expenses.py`: uma consulta agrupada por
   `substr(t.date, 1, 7)` com os predicados `INCOME` e `SPENDING` de `app/queries/spending.py`
   (transferência, estorno e "não é gasto" fora, invariante 25), filtro de período e conta pelo mesmo
   `date_window`. Devolve `MonthTotal(month, income_cents, spending_cents, balance_cents)` só para
   meses com lançamento, em ordem crescente.
2. **Ferramenta `spending_summary`** em `app/advisor/tools.py`: entrada `date_from`, `date_to`,
   `account` (mesmas validações e resolução de conta de `search_transactions`); saída com `filters`,
   `income`/`spending`/`balance` do período por `period_result`, `by_category` por `sum_by_category`
   (rótulo, contagem, total) e `months` por `monthly_totals`, cada valor em centavos e escrito por
   `app/formatting.py::brl`. Entra em `TOOLS`, que os dois adaptadores já traduzem para o esquema de
   cada provedor.
3. **Menos chamadas por pergunta (causa raiz do excesso no Gemini).** Medido no teste manual da 070:
   "gastos com posto em agosto" custou 3 chamadas, porque o modelo não conhecia as categorias e tentou
   texto antes de categoria. `system_prompt(today, categories)` passa a listar os rótulos das
   categorias (de `list_categories`) e diz qual ferramenta serve a cada pergunta; pergunta por
   categoria ou mês a mês resolve com um `spending_summary` em vez de várias buscas. O limite que
   estourou é o da cota gratuita: 20 chamadas por dia para `gemini-3.8-flash`; com duas chamadas por
   pergunta, dá cerca de dez perguntas por dia.
4. **429 claro.** `app/advisor/gemini_provider.py` lê o corpo do erro: `RetryInfo.retryDelay` vira
   "tente de novo em N segundos"; cota diária (`quotaId` com `PerDay`) vira "a cota diária do Gemini
   acabou", com o modelo e as saídas (`DASH_ADVISOR_GEMINI_MODEL` ou a Anthropic), verificada antes do
   `retryDelay` porque o corpo da cota diária também traz uma espera de segundos. Sem detalhe, fica a
   mensagem genérica de excesso.
5. **Tela:** `chat-message-item.tsx` descreve as ferramentas consultadas por nome
   (`search_transactions` → "seus lançamentos", `spending_summary` → "o resumo de gastos").

## Arquivos

Backend: `app/queries/expenses.py`, `app/advisor/tools.py`, `app/advisor/chat.py`,
`app/advisor/gemini_provider.py`. Testes: `tests/test_advisor_tools.py`, `tests/test_advisor_chat.py`,
`tests/test_advisor_providers.py`, `tests/test_monthly_totals.py`. Front:
`src/features/advisor/components/chat-message-item.tsx` e teste. Docs: `docs/consultor-chat.md`.

## Skills

python-*, component-testing.
