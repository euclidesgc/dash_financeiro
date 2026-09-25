# SPEC 060 — plain-language-copy

## Contexto

- `app/routers/summary.py` passa `COMMAND = "python -m app.sync"` ao fragmento `resumo_sincronizacao.html`, que o imprime em `<code>`.
- `app/templates/configuracao.html` imprime `item['screen']` como texto do link; `app/templates/consultor.html` faz o mesmo com `question['where']` e escreve `/configuracao` à mão.
- `app/settings/catalog.py` é a fonte única das linhas da Configuração e das perguntas do Consultor (`app/advisor/gaps.py`).
- `app/advisor/gemini.py` recusa sem chave citando `/configuracao`.
- Na SPA: `sync-panel.tsx`, `category-totals.tsx`, `balance-item.tsx`, `balances-list.tsx`, `routes/dashboard.tsx`, `routes/connections.tsx`.

## Decisões

### D1 — O nome da tela mora no catálogo, ao lado do endereço

`SCREEN_LABELS` em `app/settings/catalog.py` mapeia cada endereço usado pelo catálogo para o nome que o menu dá à tela; cada entrada ganha `screen_label`, e `gaps.wanted()` repassa como `where_label`.

- Alternativa descartada: filtro Jinja que busca o nome em `app/routers/navigation.SCREENS` — motivo: `navigation` importa os routers e os routers carregam os filtros; o import circular custaria mais que quatro nomes. Além disso `/app/expenses` não está no menu antigo.

### D2 — O comando some da resposta do Resumo

`COMMAND` sai de `summary.py`; o botão "Sincronizar agora" já está logo abaixo da frase.

### D3 — Só texto na tela de saldos

Nenhuma mudança de estrutura em `dashboard.tsx` além da frase de subtítulo, porque a fatia 055 acrescenta um cartão à mesma tela em paralelo.

## Arquivos afetados

| Ação | Arquivo | O quê |
|---|---|---|
| alterar | `app/settings/catalog.py`, `app/advisor/gaps.py` | `SCREEN_LABELS`, `screen_label`, `where_label` |
| alterar | `app/templates/configuracao.html`, `consultor.html`, `fragments/gastos_correcao.html`, `fragments/resumo_sincronizacao.html` | nome da tela no link; frase sem comando |
| alterar | `app/routers/summary.py`, `app/advisor/gemini.py` | sem `COMMAND`; recusa cita a tela pelo nome |
| alterar | `src/features/sync/components/sync-panel.tsx`, `src/features/expenses/components/category-totals.tsx`, `src/features/accounts/components/{balance-item,balances-list}.tsx`, `src/app/routes/{dashboard,connections}.tsx` | textos |
| alterar | testes que afirmam o texto antigo (`tests/`, `src/**/__tests__/`, `e2e/`) | texto novo |

## Riscos

- Conflito textual com a 055 em `dashboard.tsx`: uma linha só.
