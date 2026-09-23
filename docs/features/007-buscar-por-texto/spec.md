# SPEC 007 — buscar por texto

Sétima fatia da SPA. Acrescenta à página "Gastos" (`/app/expenses`) um campo "Buscar" que restringe a lista aos gastos cuja descrição ou nome do recebedor contenha o texto, sem distinguir maiúsculas nem acentos, guardado na URL e aplicado em SQL junto com período e conta, antes da ordenação e da paginação. Nenhum endpoint novo: a fatia estende `GET /api/transactions/expenses` com `q`.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/db.py` · `connect(path)` é o único lugar que abre SQLite (`sqlite3.connect`); app, testes e `scripts/e2e-backend.sh` passam por ele. É onde uma função SQL registrada vale para todo mundo.
- `app/queries/expenses.py` · `_where(date_from, date_to, account_id) -> (sql, params)` monta `WHERE {SPENDING}` mais os predicados; `_SELECT` já faz `LEFT JOIN accounts AS a`; `_TOTAL` conta e soma com o mesmo `where`; `list_expenses(conn, *, page, page_size, sort, order, date_from, date_to, account_id)`; o nome do recebedor é resolvido em Python por `app.payees.names.labels(conn)` a partir de `t.payee`.
- `app/payees/names.py` · o nome exibido é uma precedência por `payee` (`_chosen`): apelido do dono (`payee_names.source = 'dono'`) > `transactions.merchant_name` > nome consultado por CNPJ (`payee_names.source = 'cnpj'`) > `transactions.merchant_legal_name` ou `transactions.receiver_name`; sem nenhum, o nome é a própria chave e `labels()` o omite (a tela mostra só a descrição). Não há tabela `payees`: os nomes da Pluggy são colunas de `transactions` (migração `011_payee_names.sql`) e os do dono/CNPJ estão em `payee_names (payee, source, name)` com chave primária `(payee, source)`.
- `app/ingest/normalize.py` · `normalize_description` tira acento e caixa, mas também apaga dígitos, datas e parcelas — serve para a chave `payee`, não para busca ("GASTO 42" perderia o 42).
- `app/routers/transactions.py` · parâmetros em `Annotated[..., Query(...)]`; `account_id` repassado direto a `list_expenses`.
- `src/features/expenses/types/expense.ts` · `ExpensesQuery { page, sort, order, from, to, account }`.
- `src/features/expenses/api/get-expenses.ts` · só acrescenta ao `URLSearchParams` o que não é nulo; `queryKey: ['expenses', query]`; `keepPreviousData`.
- `src/features/expenses/components/expenses-list.tsx` · `readX`/`writeX` sobre `useSearchParams`; toda escrita parte de `new URLSearchParams(searchParams)` e apaga `page`; barra `mt-6 flex flex-wrap items-end gap-3` com `AccountSelect`, `PeriodControls`, `SortControls` fora dos ramos de estado; vazio "Nenhum gasto para esse filtro." quando `period.kind !== 'all' || account !== null`.
- `src/features/expenses/components/period-controls.tsx` · `<input type="date">` com as classes da receita "Barra de controles de lista"; `Button` secundário para limpar ("Todo o período").
- `src/components/ui/button.tsx` · `Button` com `variant`, `min-h-10`, `type="button"` por padrão.
- `src/testing/mocks/handlers.ts` · `fakeExpenses` (45 gastos; o de `id` 45 é "MERCADO DO BAIRRO" com `payee_name: 'Mercado do Bairro'`; os demais "GASTO n" sem recebedor), handler que filtra por `from`/`to`/`account_id`, ordena e fatia.
- `tests/test_expenses_api.py` · `_transaction(id, date, amount, **overrides)` aceita `nome_fantasia`, `razao_social`, `recebedor`; `_load(rows)`; `_fill_payees(conn)` preenche `t.payee` (o ingest não o faz); `_descriptions(client, query)`.
- `tests/data/e2e_transactions.json` + `scripts/e2e-backend.sh` · 5 lançamentos, sem classificação (`t.payee` fica nulo, então nenhum recebedor aparece no e2e).

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `SearchInput` (novo, na feature) renderiza, como primeiro controle da barra, `<label>` "Buscar" + `<input type="search">` com placeholder "Descrição ou recebedor" e botão "Limpar busca" (D5). |
| R2 | `q` na URL vira `q` na chamada; o servidor soma ao `_where` `AND (fold(t.description) LIKE ? ESCAPE '\' OR fold(<nome do recebedor>) LIKE ? ESCAPE '\')` com o termo entre `%` (D1, D2, D3). |
| R3 | `fold` (função SQL registrada em `connect()`) decompõe em NFKD, descarta as marcas combinantes e aplica `casefold()`; o termo passa pelo mesmo `fold` antes de virar padrão, então "acougue" e "AÇOUGUE" viram o mesmo texto dos dois lados (D1). |
| R4 | `SearchInput` guarda um rascunho local; um `setTimeout` de 300 ms (reiniciado a cada tecla, limpo ao desmontar) chama `onCommit`; o `<form role="search">` faz Enter chamar `onCommit` na hora (D5). |
| R5 | Cliente: `writeSearch(params, text)` apaga `q` quando o texto sem espaços tem menos de 2 caracteres, então a chamada sai sem `q`. Servidor: `q` com menos de 2 caracteres após `strip()` é tratado como ausente (`search=None`), status 200, nunca 422 (D4). |
| R6 | Botão "Limpar busca" (visível quando o rascunho não está vazio) zera o rascunho e chama `onCommit('')` na hora; `writeSearch` apaga `q` (D5). O Esc nativo do `type="search"` só limpa o campo no navegador e é coberto pelo debounce. |
| R7 | `search` entra em `ExpensesQuery` e, portanto, em toda chamada e na chave da query; "Anterior"/"Próxima" só trocam `page`. |
| R8 | `q` mora na URL (`client-state`); escrita com `replace: true` como os demais filtros; ao abrir `?q=mercado`, o rascunho nasce com "mercado" (D6). |
| R9 | `writeSearch` só grava quando o `q` efetivo muda (`next !== current`), e quando grava apaga `page`. Digitar "a" a partir de uma URL sem `q` não escreve nada, e a página não se mexe (D6). |
| R10 | `writeSearch` toca só `q` e `page`; `writeAccount`, `writePeriod`, `writeSorting` não conhecem `q`. Todos partem de `new URLSearchParams(searchParams)`. |
| R11 | `total` e `total_cents` vêm do mesmo `SELECT count(*), coalesce(sum(...))` com o mesmo `where`, agora com o predicado de busca (D2). `Pagination` não muda. |
| R12 | `filtered = period.kind !== 'all' \|\| account !== null \|\| search !== null`; com `total === 0`, o vazio diz "Nenhum gasto para esse filtro.". |
| R13 | Os quatro estados de `ExpensesList` não mudam de forma; a chave `['expenses', { …, search }]` faz "Tentar de novo" refazer com a busca atual e a troca de termo mostrar a lista anterior com paginação desabilitada (`keepPreviousData`). O campo fica na barra, fora dos ramos. |

## Decisões técnicas

### D1 — `fold` é função SQL registrada na conexão, em `app/db.py`

- Escolha: `fold(value: str | None) -> str | None` em `app/db.py`: `None` devolve `None`; senão `unicodedata.normalize("NFKD", value)`, descarta `unicodedata.combining(char)`, `casefold()`. `connect()` chama `conn.create_function("fold", 1, fold, deterministic=True)` logo depois do `PRAGMA`. Como toda conexão do projeto nasce em `connect()`, a função existe no app, nos testes e no e2e sem passo extra. `deterministic=True` deixa o SQLite usá-la em índice e expressão constante.
- Alternativa descartada: coluna gerada/normalizada por migração (`description_fold`) — motivo: o nome do recebedor vem de cinco lugares (três colunas de `transactions` e duas linhas de `payee_names`) com precedência; seriam cinco colunas geradas ou um gatilho em `payee_names`, e cada apelido novo do dono teria de reescrever a coluna. Um índice não faz falta: a base é de um usuário e a lista já filtra por `SPENDING` sem índice.
- Alternativa descartada: buscar em Python depois de ler as linhas — motivo: paginação e total são em SQL (norma 33); filtrar depois quebra `total`/`total_cents` ou obriga a ler tudo.
- Alternativa descartada: reusar `normalize_description` — motivo: ela apaga dígitos, datas e parcelas; "GASTO 42" não seria encontrado por "42" e "10/12" sumiria. O `fold` só mexe em caixa e acento.
- Alternativa descartada: `LOWER()` + `REPLACE()` encadeados no SQL — motivo: uma cadeia de `REPLACE` por vogal acentuada é longa, incompleta (ç, ü, maiúsculas) e diverge do `unicodedata` que o resto do projeto usa.

### D2 — O nome do recebedor entra no SQL pela mesma precedência de `_chosen`, com dois `LEFT JOIN` em `payee_names`

- Escolha: `_FROM` (constante nova, usada por `_SELECT` e `_TOTAL`) passa a ser `FROM transactions AS t LEFT JOIN accounts AS a ON a.id = t.account_id LEFT JOIN payee_names AS own ON own.payee = t.payee AND own.source = 'dono' LEFT JOIN payee_names AS lk ON lk.payee = t.payee AND lk.source = 'cnpj'`. A chave primária `(payee, source)` garante que cada junção traz no máximo uma linha, então contagem e soma não se multiplicam. `_PAYEE_NAME_SQL = "CASE WHEN t.payee IS NULL THEN NULL ELSE COALESCE(NULLIF(own.name, ''), NULLIF(t.merchant_name, ''), NULLIF(lk.name, ''), NULLIF(t.merchant_legal_name, ''), NULLIF(t.receiver_name, '')) END"` reproduz `_chosen` linha a linha: `NULLIF(..., '')` faz o papel do `if name:`; o `CASE` sobre `t.payee` faz o papel do `WHERE payee IS NOT NULL` de `_FROM_PLUGGY` (linha sem chave não tem recebedor na tela, então também não tem na busca). As junções ficam sempre no `FROM`, com ou sem `q`: uma forma só de SQL, e o custo é desprezível nesta base.
- Diferença assumida: `labels()` toma `MIN(merchant_name)` por grupo de `payee`; o SQL usa o valor da própria linha. O comentário em `names.py` registra que nenhum `payee` da base carrega dois valores no mesmo nível, então hoje o resultado é o mesmo. Se um dia divergir, a busca acha a linha pelo nome que ela mesma carrega — comportamento aceitável e documentado, não bug.
- Alternativa descartada: buscar em todas as cinco fontes com `OR` (sem precedência) — motivo: acharia um gasto por uma razão social que a tela não mostra; R2 fala do "nome de quem recebeu" que o usuário vê.
- Alternativa descartada: resolver `labels(conn)` em Python, achar as chaves que casam e passar `t.payee IN (?, ?, …)` — motivo: a lista de chaves cresce com a base (limite de variáveis do SQLite) e a consulta deixaria de ser uma só.
- Alternativa descartada: trocar `payee_name` do item para vir de `_PAYEE_NAME_SQL` e apagar `labels()` daqui — motivo: muda o que já está entregue e testado (003) por um ganho que não é desta fatia; fica registrado em "Dívida encontrada".

### D3 — Padrão `LIKE` com escape, montado em Python a partir do termo já dobrado

- Escolha: `_like_pattern(term: str) -> str` em `app/queries/expenses.py`: `folded = fold(term)`; escapa `\`, `%` e `_` (nessa ordem) prefixando `\`; devolve `f"%{escaped}%"`. `_where(date_from, date_to, account_id, search: str | None)` soma `" AND (fold(t.description) LIKE ? ESCAPE '\\' OR fold(" + _PAYEE_NAME_SQL + ") LIKE ? ESCAPE '\\')"` e o padrão duas vezes nos `params` (ordem: data, conta, busca). `fold(NULL)` é `NULL`, `NULL LIKE …` é falso: descrição nula não quebra nada. O `LIKE` do SQLite só ignora caixa em ASCII; como os dois lados já passaram por `fold`, isso não importa. Importa `fold` de `app.db` (queries → db é sentido permitido: db é infraestrutura).
- Alternativa descartada: `instr(fold(...), ?) > 0` sem escape — motivo: funciona, mas `LIKE` com `ESCAPE` é a forma que o leitor de SQL reconhece e o escape custa três `replace`; empate técnico, `LIKE` documenta a intenção.
- Alternativa descartada: FTS5 — motivo: tabela virtual, gatilhos de sincronização e tokenizador para uma base de um usuário com milhares de linhas; a fatia pede "contém".

### D4 — O router recebe `q` como `str` opcional; menos de 2 caracteres é "sem busca", não 422

- Escolha: `q: Annotated[str | None, Query()] = None`; `term = q.strip() if q is not None else ""`; `search = term if len(term) >= 2 else None`; `list_expenses(..., search=search)`. Sem `min_length` no `Query`: R5 diz que texto curto não filtra, e um 422 no meio da digitação (o cliente já não manda, mas um link à mão manda) seria erro onde o PRD pede "lista sem esse filtro". O `/openapi.json` passa a listar `q` como `string` opcional (norma 3). Nome `q`: é o nome usual de busca em query string e o mesmo que o app usa na URL.
- Alternativa descartada: `Query(min_length=2)` — motivo: 422 contradiz R5.
- Alternativa descartada: `max_length` — motivo: limite sem requisito; um `LIKE` com termo longo só devolve vazio.

### D5 — `SearchInput` é componente da feature, com rascunho local, debounce e Enter

- Escolha: `src/features/expenses/components/search-input.tsx` · `SearchInput({ value, onCommit })`, `value: string | null` (o `q` da URL), `onCommit: (text: string) => void`. Estrutura: `<form role="search" className="flex flex-col gap-1" onSubmit>` com `<label htmlFor={useId()}>` "Buscar", uma linha `flex items-center gap-2` com `<input type="search" placeholder="Descrição ou recebedor" autoComplete="off">` (classes do `<input type="date">` de `PeriodControls`, mais `min-w-48`) e, quando o rascunho não é vazio, `<Button variant="secondary" aria-label="Limpar busca">` com o texto "Limpar". Estado: `draft` (`useState(value ?? '')`); `useEffect` sobre `draft` arma `setTimeout(() => onCommit(draft), 300)` e devolve `clearTimeout` (assim tecla nova reinicia e desmontar não dispara); `onSubmit` faz `preventDefault()` e chama `onCommit(draft)`; "Limpar" faz `setDraft('')` e `onCommit('')`. Sincronização de fora (voltar do navegador, link): `useEffect` sobre `value` que, se `value !== lastCommittedRef.current`, faz `setDraft(value ?? '')`; `onCommit` local atualiza o ref com o texto efetivo (`trim`, `< 2` → `null`) para não sobrescrever o que o usuário está digitando quando a própria escrita volta pela URL. O componente não decide o que é "efetivo": entrega o texto cru e `writeSearch` aplica a regra dos 2 caracteres (uma regra só, no mesmo lugar dos outros `writeX`).
- Alternativa descartada: campo controlado direto pela URL com debounce na escrita — motivo: cada tecla passaria por `setSearchParams`, o `trim` e a regra dos 2 caracteres apagariam o que a pessoa está digitando ("a" some do campo).
- Alternativa descartada: hook `useDebounce` em `src/hooks/` — motivo: um consumidor só; `project-structure` manda subir quando o segundo aparecer.
- Alternativa descartada: React Hook Form + Zod (`forms`) — motivo: um campo sem validação de envio; o formulário é só para o Enter.
- Alternativa descartada: só o "x" nativo do `type="search"` — motivo: não existe em todo navegador e não tem nome acessível; o botão "Limpar" é o R6.

### D6 — `q` mora na URL; a regra dos 2 caracteres e o reset de página ficam em `writeSearch`

- Escolha: em `expenses-list.tsx`: `readSearch(value: string | null): string | null` — `trim()`; vazio ou com menos de 2 caracteres → `null`. `writeSearch(params, text)`: `next = text.trim().length >= 2 ? text.trim() : null`; `current = readSearch(params.get('q'))`; se `next === current`, não faz nada (devolve `false`); senão `params.delete('page')` e grava `q` ou o apaga. `handleSearchCommit(text)` só chama `setSearchParams(params, { replace: true })` quando `writeSearch` devolveu `true`. `ExpensesQuery` ganha `search: string | null`; `getExpenses` acrescenta `q` quando não nulo; `SearchInput value={search}`.
- Alternativa descartada: mandar `q` de qualquer tamanho e deixar o servidor ignorar — motivo: a URL ganharia `q=a` e a chave da query mudaria a cada letra, refazendo a chamada sem mudar nada.
- Alternativa descartada: `useState` para a busca — motivo: R8 exige sobreviver a recarga e link; `client-state` manda filtro para a URL.

### D7 — Contrato JSON

- `GET /api/transactions/expenses?page=1&page_size=20&sort=date&order=desc&from=…&to=…&account_id=…&q=<texto>` · `q` opcional, string; após `strip`, menos de 2 caracteres equivale a ausente. Combina com os demais por `AND`. Resposta inalterada (`items`, `page`, `page_size`, `total`, `total_cents`; item sem campo novo). Não se ecoa `q`.

## Interface

Receitas do `docs/design.md` usadas: contêiner de página, título de página, texto de apoio, barra de controles de lista (o `<input>` com as classes do campo de formulário mais `min-h-10`, sem `w-full`, como o `<input type="date">` do grupo de período), botão secundário, lista, linha de lançamento, paginação, carregando, vazio, erro. Nenhuma receita nova.

### Tela: Gastos (`/app/expenses`)

- Título do documento, `<h1>` "Gastos" e texto de apoio "Todos os gastos das suas contas e cartões." não mudam.
- Barra de controles, sempre visível, nesta ordem, quebrando de linha em 360px:
  1. Campo "Buscar": `<label>` + `<input type="search">` com placeholder "Descrição ou recebedor"; à direita, quando há texto, botão secundário "Limpar" com `aria-label="Limpar busca"`. O campo tem `min-w-48` para caber "Descrição ou recebedor" sem cortar.
  2. Campo "Conta" (inalterado, 006).
  3. Grupo "Mês" e campos "De"/"Até" (inalterados, 005).
  4. "Ordenar por" + botão "Decrescente"/"Crescente" (inalterados, 004).
- Carregando (`role="status"`): "Carregando gastos…" — inalterado; troca de termo mostra a lista anterior com "Anterior"/"Próxima" desabilitados (`keepPreviousData`).
- Vazio sem filtro: "Nenhum gasto registrado ainda." — inalterado.
- Vazio com filtro (busca, conta, período ou combinação): "Nenhum gasto para esse filtro." — inalterado no texto; passa a valer também para a busca.
- Erro (`role="alert"`): "Não foi possível carregar os gastos." + "Tentar de novo" — inalterado.
- Com dados: lista da 003 na ordem da 004; resumo "Página 1 de 1 · 1 gasto · R$ 84,90 no período" reflete a busca; "Anterior"/"Próxima" mantêm `q`/`account`/`month`/`from`/`to`/`sort`/`order`.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `app/db.py` | função `fold(value)` (NFKD, sem combinantes, `casefold`; `None` → `None`); `connect()` registra `conn.create_function("fold", 1, fold, deterministic=True)` (D1) | — |
| alterar | `app/queries/expenses.py` | `_FROM` com os dois `LEFT JOIN payee_names`; `_SELECT` e `_TOTAL` usam `_FROM`; `_PAYEE_NAME_SQL`; `_like_pattern(term)`; `_where(date_from, date_to, account_id, search)` com o predicado `OR` entre descrição e recebedor; `list_expenses(..., search: str \| None = None)` (D2, D3) | — |
| alterar | `app/routers/transactions.py` | `q: Annotated[str \| None, Query()] = None`; `strip` e regra dos 2 caracteres; repassa `search` (D4, D7) | `api-requests` |
| alterar | `tests/test_db.py` | `SELECT fold('Açougue São JORGE')` → `"acougue sao jorge"`; `SELECT fold(NULL)` → `None`; `fold` disponível numa segunda conexão ao mesmo arquivo | `unit-testing` |
| alterar | `tests/test_expenses_api.py` | testes: `q=acougue` acha `descricao="AÇOUGUE SÃO JORGE"` e não acha "GASTO x"; `q=MERCADO` acha `descricao="Pagamento mercado"` (caixa); `q=bairro` acha por `nome_fantasia="Mercado do Bairro"` após `_fill_payees`; apelido do dono via `name_it(conn, payee, "Padaria da Esquina", "dono")` é achado por `q=padaria` e vence o `nome_fantasia` (o texto do `nome_fantasia` deixa de casar); sem `_fill_payees` (`payee` nulo) o `nome_fantasia` não é achado; `q=100%` acha "GASTO 100%" e não "GASTO 1000" (escape de `%`); `q=to_1` acha "GASTO_1" e não "GASTOX1" (escape de `_`); `q=a` e `q=%20a%20` devolvem o mesmo que sem `q`, status 200; `q` combina com `account_id` e `from`/`to` por `AND`; `total` e `total_cents` com `page_size=1` refletem a busca inteira; transferência cuja descrição casa fica fora; o `/openapi.json` lista `q` como `string` opcional | `api-requests`, `unit-testing` |

### Ferramental (raiz)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `tests/data/e2e_transactions.json` | sexto objeto `e2e-t-6`: `"data": "2026-08-20"`, `"conta_id": "acc-fixture-1"`, `"descricao": "AÇOUGUE SÃO JORGE"`, `"valor": -60.0`, `"tipo": "DEBIT"`, `"categoria_pluggy": "Groceries"`, `"categoria": "Groceries"`, demais campos como em `e2e-t-1` (em agosto, para não mexer nas contagens de setembro da 005). O recebedor não entra no e2e porque `t.payee` fica nulo sem classificação; esse caminho é coberto pelo teste de API e pelo de componente | `e2e-testing` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `src/features/expenses/types/expense.ts` | `ExpensesQuery.search: string \| null` (D6) | — |
| alterar | `src/features/expenses/api/get-expenses.ts` | acrescenta `q` ao `URLSearchParams` só quando `query.search` não é nulo | `api-requests` |
| criar | `src/features/expenses/components/search-input.tsx` | `SearchInput` (D5): label "Buscar", `<input type="search">`, debounce 300 ms, Enter, "Limpar", sincronização com `value` | `interface-design`, `component-robustness` |
| criar | `src/features/expenses/components/__tests__/search-input.test.tsx` | com `vi.useFakeTimers`: digitar "acougue" não chama `onCommit` antes de 300 ms e chama uma vez com "acougue" depois; digitar "ac", "aco" em sequência rápida chama uma vez com "aco"; Enter chama na hora com o rascunho; "Limpar busca" some com o campo vazio, aparece com texto, zera o campo e chama `onCommit('')`; `value="mercado"` inicial preenche o campo; mudar `value` de fora (rerender com `"posto"`) troca o rascunho; desmontar antes dos 300 ms não chama `onCommit` | `component-testing` |
| alterar | `src/features/expenses/components/expenses-list.tsx` | `readSearch`/`writeSearch` (devolve se gravou); `handleSearchCommit`; `SearchInput` como primeiro controle da barra; `search` em `useExpenses`; `filtered` inclui `search !== null` (D6) | `client-state`, `interface-design`, `component-robustness` |
| alterar | `src/testing/mocks/handlers.ts` | `foldText(value)` exportado (`normalize('NFD')`, remove `̀–ͯ`, `toLowerCase`); `fakeExpenses`: o gasto de `id` 42 (`index === 3`) ganha `payee_name: 'Açougue São Jorge'` (descrição "GASTO 42" mantida); handler lê `q`, ignora se `trim().length < 2`, senão filtra por `foldText(description ?? '').includes(term) \|\| foldText(payee_name ?? '').includes(term)` junto com `from`/`to`/`account_id` | `api-mocking` |
| alterar | `src/features/expenses/components/__tests__/expenses-list.test.tsx` | `filterForSpy` ganha `q` (usa `foldText` de `handlers`); padrão: campo "Buscar" vazio, sem "Limpar busca", API sem `q`; `?q=mercado` → API com `q=mercado`, campo com "mercado", "1 gasto", item "MERCADO DO BAIRRO"; digitar "acougue" e avançar 300 ms → URL `q=acougue`, 1 item com "Açougue São Jorge"; digitar "a" → URL sem `q`, nenhuma chamada nova; digitar "Gasto 4" + Enter → chamada imediata com `q=Gasto 4`; a partir de `?page=2&account=acc-bank-1&sort=amount`, digitar "gasto" → URL sem `page`, com `q=gasto`, `account` e `sort` mantidos; "Limpar busca" → URL sem `q`, "45 gastos"; `?q=zzzz` → "Nenhum gasto para esse filtro." com os controles visíveis; "Próxima" com `?q=gasto` (44 gastos) → `?q=gasto&page=2` | `component-testing`, `api-mocking` |
| alterar | `e2e/expenses.spec.ts` | ajustes: regex `[34] gastos` → `[45] gastos`; alternativas do resumo sem filtro → "4 gastos · R$ 339,90 no período" / "5 gastos · R$ 389,90 no período". Teste novo: login → "Gastos" → `getByLabel('Buscar')` vazio → `fill('acougue')` → URL contém `q=acougue`, 1 item "AÇOUGUE SÃO JORGE" com "-R$ 60,00", resumo "1 gasto · R$ 60,00 no período" → `page.reload()` mantém o item e o campo com "acougue" → `fill('a')` → URL sem `q` e ≥ 4 itens → `fill('mercado')` + `press('Enter')` → URL `q=mercado`, 1 item "MERCADO DO BAIRRO" → `getByRole('button', { name: 'Limpar busca' })` → URL sem `q`, ≥ 4 itens → `page.goto('/app/expenses?q=mercado&month=2026-08')` → "Nenhum gasto para esse filtro." → "Todo o período" → 1 item e URL ainda com `q=mercado` | `e2e-testing` |

## Estimativa de tamanho

Jornadas: 1 (encontrar um gasto por texto) · Telas novas: 0 · Linhas alteradas (sem testes): ~45 Python (`db.py` ~12, `queries/expenses.py` ~28, `routers/transactions.py` ~5) + ~140 em `src/` (tipos ~1, `get-expenses.ts` ~3, `search-input.tsx` ~85, `expenses-list.tsx` ~30, mocks ~20) + ~20 de fixture · Fases previstas: 2 (`fold` na conexão, `q` no endpoint com junção do recebedor + testes de API e de `db`; `SearchInput`, URL, mocks, testes de componente e e2e).

Nenhum sinal de "grande demais" dispara.

## Dívida encontrada

- A precedência do nome do recebedor passa a existir em dois lugares: `app/payees/names.py:_chosen` (Python, por grupo de `payee`, com `MIN`) e `app/queries/expenses.py:_PAYEE_NAME_SQL` (SQL, por linha). Hoje dão o mesmo resultado (nenhum `payee` carrega dois valores no mesmo nível). Item de roadmap: o item de `list_expenses` passar a ler `payee_name` de `_PAYEE_NAME_SQL` e `labels()` sair daqui, deixando uma fonte só — a fazer junto com a subida de `_where` para `spending.py` (dívida da 005), antes da fatia 008.
