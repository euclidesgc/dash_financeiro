# SPEC 012 — limite por categoria

Décima segunda fatia da SPA. Na página "Categorias" (`/app/categories`, fatia 010), cada linha ganha o limite mensal da categoria: um valor em reais que o dono define, edita ou apaga direto na linha, guardado em centavos inteiros na coluna `categories.monthly_limit_cents`. A fatia 013 lê essa coluna para dizer se a categoria está dentro ou acima do limite; aqui só se grava e se mostra.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/migrations/sql/020_category_labels.sql` · `categories (id, name, group_id, label, is_system)`. `NUMBERING.md` diz que a próxima é `021`. `tests/test_migrations.py`: `EXPECTED_MIGRATIONS` (18 arquivos), `test_a_fresh_base_applies_the_eighteen_real_migrations` afirma `"migrations applied: 18"`, fatias `[:-2]`/`[:-1]` para migrar "até a anterior".
- `app/queries/categories.py` · `_SELECT` (`c.name, c.label, c.is_system, count(t.id)`), `CategoryRow(key, label, is_system, usage_count)`, `_row`, `list_categories`, `get_category`.
- `app/taxonomy/catalogue.py` · exceções `InvalidLabelError`, `DuplicateLabelError`, `CategoryNotFoundError`, `SystemCategoryError`, `CategoryInUseError`; `_require(conn, key)` (recusa `UNCATEGORISED` e chave inexistente); `rename_category` é o modelo de escrita (`_require` → `UPDATE` → `commit`).
- `app/routers/categories.py` · `CategoryOut`, `CategoryInput { label }`, `_out`, `_translated()` (exceção → `HTTPException` com `detail` em pt-BR), `_fetch(conn, key)`, handlers `GET ""`, `POST ""`, `PATCH "/{key}"`, `DELETE "/{key}"`; `connect()` em `try/finally`.
- `tests/test_categories_api.py` (20 testes, com `client` logado e `/openapi.json`), `tests/test_catalogue.py`.
- `src/features/categories/types/category.ts` (`CatalogueCategory { key; label; is_system; usage_count }`), `types/category-label-schema.ts` (Zod + `z.infer`), `api/rename-category.ts` (modelo de mutation: `apiRequest` + `useMutation` invalidando `['categories']` e `['expenses']`), `components/category-item.tsx` (`mode: 'view' | 'rename' | 'confirm-delete' | 'in-use'`; coluna direita `flex shrink-0 flex-col items-end gap-1` com contagem e botões "Renomear"/"Apagar"), `components/rename-category-form.tsx` (modelo de formulário em linha: `useForm` + `zodResolver`, `useId`, `autoFocus`, `Escape` → `onDone`, `setError` no 422, `Alert` no erro genérico, "Salvando…"/`disabled`).
- `src/utils/format-money.ts:formatMoney(cents)` · `Intl` pt-BR, centavos → "R$ 1.200,00".
- `src/testing/mocks/handlers.ts` · `generateFakeCategories()` (6 itens), `fakeCategories`, `resetCategories()`, handlers `GET`/`POST`/`PATCH`/`DELETE` de `/api/categories`; `src/testing/setup.ts` já chama `resetCategories()` no `afterEach`.
- `src/features/categories/components/__tests__/{categories-list,create-category-form}.test.tsx`, `e2e/categories.spec.ts` (login → "Categorias" → cria "Pet shop" → … → apaga).
- `src/components/ui/alert.tsx` (`role="alert"`, `mt-6`, ação opcional), `button.tsx` (`primary | secondary | danger`, `min-h-10`).

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `CategoryItem` ganha o botão secundário "Limite" (`aria-label` "Definir limite de {rótulo}") e o modo `'limit'`, que monta `CategoryLimitForm` no lugar da coluna direita: `<input type="number" step="0.01" min="0.01" inputMode="decimal">` com `<label>` "Limite mensal (R$)", na mesma linha da lista (D5, D6). |
| R2 | Campo vazio é válido no Zod (`categoryLimitSchema`) e vira `monthly_limit_cents: null` por `toCents('')` (D5); a coluna é `INTEGER NULL` (D1). |
| R3 | O valor só é enviado no `submit` do formulário (Enter no campo ou botão "Salvar"); não há `onChange` que chame a API (D6). |
| R4 | `mutation.isPending` → botão "Salvando…" e `disabled` nos dois botões (D6). |
| R5 | Sem atualização otimista: o cache `['categories']` só é invalidado no `onSuccess`; em erro, a linha mostra `Alert` "Não foi possível salvar o limite. Tente de novo." e o formulário fica aberto com o valor digitado; o banco não muda porque a validação do domínio ocorre antes do `UPDATE` e o `CHECK` protege o resto (D3, D6). |
| R6 | `GET /api/categories` devolve `monthly_limit_cents` (D2, D4); em modo `'view'` a linha mostra `Limite: ${formatMoney(cents)}` ou "Sem limite" (D6). |
| R7 | Campo apagado + Enter → `PUT … { monthly_limit_cents: null }` → `UPDATE … SET monthly_limit_cents = NULL`; a lista refaz a chamada e mostra "Sem limite" (D3, D5). |
| R8 | Um único valor por categoria: coluna escalar em `categories`, sem tabela por mês (D1). |
| R9 | Zod: `^\d+([.,]\d{1,2})?$` e valor `> 0` → mensagens "Informe um valor maior que zero." e "Use no máximo duas casas decimais." junto do campo, sem chamar a API e sem limpar o campo; no servidor, `set_monthly_limit` recusa `<= 0` com `InvalidLimitError` → 422 "O limite precisa ser maior que zero.", que o front põe no campo por `setError` (D3, D5). |
| R10 | `set_monthly_limit` usa só `_require` (existe e não é `UNCATEGORISED`); não consulta `is_system`. O botão "Limite" aparece em toda linha (D3, D6). |

## Decisões técnicas

### D1 — Migração `021_category_limit.sql`: coluna `monthly_limit_cents INTEGER NULL` com `CHECK`

- Escolha: `ALTER TABLE categories ADD COLUMN monthly_limit_cents INTEGER NULL CHECK (monthly_limit_cents IS NULL OR monthly_limit_cents > 0);`. Centavos inteiros (invariante 22); `NULL` = sem limite (R2); um valor por categoria (R8). `NUMBERING.md` passa a dizer que a próxima é `022`.
- Alternativa descartada: tabela `category_limits (category_id, month, cents)` — motivo: o PRD (R8) exclui limite por mês; tabela à parte é estrutura ociosa e obriga `JOIN` em toda leitura.
- Alternativa descartada: guardar em reais (`REAL`) — motivo: viola a invariante 22 e a soma da fatia 013 ganharia erro de ponto flutuante.

### D2 — Leitura: `CategoryRow` ganha `monthly_limit_cents: int | None`

- Escolha: `_SELECT` de `app/queries/categories.py` acrescenta `c.monthly_limit_cents`; `CategoryRow` e `_row` ganham o campo; `list_categories`/`get_category` não mudam de forma. `CategoryOut` do router ganha `monthly_limit_cents: int | None` e `_out` o repassa.
- Alternativa descartada: endpoint `GET /api/categories/{key}/limit` — motivo: a lista já é carregada pela tela; um campo a mais na resposta custa nada e evita N chamadas.

### D3 — Escrita em `catalogue.set_monthly_limit(conn, key, cents)`; `InvalidLimitError` → 422

- Escolha: em `app/taxonomy/catalogue.py`, `class InvalidLimitError(ValueError)` (atributo `cents`) e `def set_monthly_limit(conn, key, cents: int | None) -> None`: `_require(conn, key)`; se `cents is not None and cents <= 0` → `InvalidLimitError(cents)`; `UPDATE categories SET monthly_limit_cents = ? WHERE name = ?`; `commit`. Não chama `classify_all` (nenhum lançamento muda). O router traduz `InvalidLimitError` → 422 `"O limite precisa ser maior que zero."` (constante `INVALID_LIMIT`) dentro de `_translated()`.
- Alternativa descartada: só `Field(gt=0)` no Pydantic — motivo: o 422 do Pydantic tem `detail` em lista, que `ApiError` descarta (vira `statusText`); a mensagem em pt-BR precisa vir do domínio, como as demais. O tipo Pydantic fica `int | None` e o domínio decide, como em `rename_category`.
- Alternativa descartada: confiar só no `CHECK` do banco e capturar `IntegrityError` — motivo: exceção genérica do driver não diz qual regra falhou; o `CHECK` fica como defesa, não como validação.

### D4 — Endpoint dedicado `PUT /api/categories/{key}/limit`, não extensão do `PATCH`

- Escolha: handler `set_limit(key, body: CategoryLimitInput)` com `CategoryLimitInput { monthly_limit_cents: int | None }` (campo obrigatório, aceitando `null`), 200 com `CategoryOut` atualizado (`_fetch`), mesmos 404/422 por `_translated()`. `PUT` porque a operação é idempotente e substitui o valor inteiro do recurso `limit`. `CategoryInput`, `PATCH` e `rename_category` ficam intocados.
- Alternativa descartada: `PATCH /api/categories/{key}` com `label` e `monthly_limit_cents` opcionais — motivo: Pydantic não distingue "campo ausente" de `"monthly_limit_cents": null` sem `model_fields_set` ou sentinela, e "ao menos um campo" vira regra a mais para testar; além disso, um `PATCH` só de limite passaria por `_check_label` ou exigiria ramificação no handler. O endpoint dedicado tem uma regra, um teste por caso e um hook próprio no front.

### D5 — Contrato JSON

- `GET /api/categories` · cada item passa a ter `"monthly_limit_cents": 150000` ou `null`. `POST` e `PATCH` devolvem o mesmo `CategoryOut` (criada nasce com `null`).
- `PUT /api/categories/{key}/limit` · body `{ "monthly_limit_cents": 150000 }` ou `{ "monthly_limit_cents": null }` → 200 `{ "key": "Shopping", "label": "Compras", "is_system": true, "usage_count": 40, "monthly_limit_cents": 150000 }`; 404 `{ "detail": "Categoria não encontrada." }` (chave inexistente ou `"Não classificado"`); 422 `{ "detail": "O limite precisa ser maior que zero." }` para `0` ou negativo; 422 do Pydantic sem o campo ou com número não inteiro; sem sessão → 401.
- Front: `src/features/categories/types/category.ts` — `CatalogueCategory` ganha `monthly_limit_cents: number | null`; `types/category-limit-schema.ts` — `categoryLimitSchema = z.object({ limit: z.string().trim().refine(v => v === '' || /^\d+([.,]\d{1,2})?$/.test(v), 'Use no máximo duas casas decimais.').refine(v => v === '' || Number(v.replace(',', '.')) > 0, 'Informe um valor maior que zero.') })`, `CategoryLimitInput`; `utils/limit-cents.ts` — `toCents(value: string): number | null` (`''` → `null`; senão `Math.round(Number(value.replace(',', '.')) * 100)`) e `fromCents(cents: number | null): string` (`null` → `''`; senão `(cents / 100).toFixed(2)`, o valor inicial do campo). O campo é `type="number"`, então o navegador já entrega ponto; a troca de vírgula é só para o texto colado.
- Alternativa descartada: `z.coerce.number()` no schema — motivo: `''` coage para `0` e some a distinção "vazio = sem limite" de "zero = inválido" (R2 vs R9). O schema valida a string; `toCents` converte uma vez.

### D6 — `CategoryItem` ganha o modo `'limit'`, o texto do limite e o botão "Limite"; formulário em `CategoryLimitForm`

- Escolha: `mode` passa a `'view' | 'rename' | 'limit' | 'confirm-delete' | 'in-use'`. Em `'view'`, a coluna direita empilha, de cima para baixo: `Limite: {formatMoney(cents)}` ou "Sem limite" (`text-sm text-gray-600 tabular-nums`), a contagem de gastos (como hoje) e a linha de botões "Limite" · "Renomear" · "Apagar". Em `'limit'`: `<CategoryLimitForm key={String(category.monthly_limit_cents)} category={category} onDone={() => setMode('view')} />`, no mesmo lugar do `RenameCategoryForm`. `category-limit-form.tsx` copia a forma de `rename-category-form.tsx`: `useForm<CategoryLimitInput>({ resolver: zodResolver(categoryLimitSchema), defaultValues: { limit: fromCents(category.monthly_limit_cents) } })`, `useId`, `<label>` "Limite mensal (R$)", `<input type="number" step="0.01" min="0.01" inputMode="decimal" autoComplete="off" autoFocus>`, `aria-invalid`/`aria-describedby`, `Escape` → `onDone`, `onSubmit` com retorno antecipado se `isPending` e `mutate({ key, monthly_limit_cents: toCents(input.limit) })`; `onSuccess` → `onDone`; `onError` → 422 → `setError('limit', { message: error.detail })`, senão `Alert` "Não foi possível salvar o limite. Tente de novo.". `api/set-category-limit.ts`: `setCategoryLimit({ key, monthly_limit_cents })` (`PUT`), `useSetCategoryLimit` invalidando só `['categories']` (gasto não mostra limite; a fatia 013 decidirá se `['expenses']` entra).
- Alternativa descartada: campo sempre visível em cada linha (R1 lido ao pé da letra) — motivo: 76 `<input>` montados e 76 botões "Salvar"; o modo por linha, já usado para renomear, mostra um campo por vez e mantém a linha legível. "Editável direto na linha, sem abrir outra tela" continua verdadeiro.
- Alternativa descartada: reutilizar `RenameCategoryForm` com prop de modo — motivo: schema, tipo do input, conversão e mutation diferentes; um `if` por linha em quatro lugares custa mais que um componente de 70 linhas.

## Interface

Receitas do `docs/design.md` usadas: lista, linha de lançamento (coluna direita `flex shrink-0 flex-col items-end gap-1`), botão principal/secundário, campo de formulário e erro de campo, formulário em linha (010), erro. Receita nova a acrescentar ao `docs/design.md` nesta entrega:

| Padrão | Classes | Fatia |
|---|---|---|
| Campo numérico em reais | `<input type="number" step="0.01" min="0.01" inputMode="decimal">` com as classes do `<input>` da receita "Campo de formulário" mais `min-h-10 tabular-nums`; rótulo termina em "(R$)" | 012 |

### Tela: Categorias (`/app/categories`) — só o que muda

Linha da lista em modo normal, coluna direita (`flex shrink-0 flex-col items-end gap-1`), de cima para baixo:

1. `text-sm text-gray-600 tabular-nums`: "Limite: R$ 1.500,00" ou "Sem limite".
2. Contagem: "Nenhum gasto" / "1 gasto" / "40 gastos" (como hoje).
3. Ações `flex gap-2`: botão secundário "Limite" (`aria-label` "Definir limite de {rótulo}"), "Renomear", e "Apagar" só em "Criada por você".

Linha em modo limite: a coluna direita dá lugar ao **formulário em linha** com `<label>` "Limite mensal (R$)" (visível), campo numérico em reais já com o valor atual (`"1500.00"`) ou vazio, com foco; botão principal "Salvar" ("Salvando…" e `disabled` enquanto salva) e secundário "Cancelar" (`disabled` enquanto salva). Enter envia; `Escape` cancela. Erros de campo (`mt-1 text-sm text-red-700`, `aria-describedby`): "Informe um valor maior que zero.", "Use no máximo duas casas decimais.", ou o `detail` 422 do servidor "O limite precisa ser maior que zero.". Erro genérico (500, rede): `Alert` dentro da linha "Não foi possível salvar o limite. Tente de novo."; o campo mantém o que foi digitado. No sucesso a linha volta ao modo normal e, com a resposta da lista, mostra o limite novo ou "Sem limite".

Em 360px: a coluna direita empilha limite, contagem e ações; o formulário em linha quebra (`flex-wrap`), campo na largura toda e botões abaixo.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `app/migrations/sql/021_category_limit.sql` | `ALTER TABLE categories ADD COLUMN monthly_limit_cents INTEGER NULL CHECK (…)` (D1) | — |
| alterar | `app/migrations/NUMBERING.md` | "a próxima migração é `022`" | — |
| alterar | `app/queries/categories.py` | `c.monthly_limit_cents` em `_SELECT`; `CategoryRow.monthly_limit_cents: int \| None`; `_row` (D2) | — |
| alterar | `app/taxonomy/catalogue.py` | `InvalidLimitError`, `set_monthly_limit(conn, key, cents)` (D3) | — |
| alterar | `app/routers/categories.py` | `CategoryOut.monthly_limit_cents`; `_out`; `INVALID_LIMIT`; `InvalidLimitError` em `_translated`; `CategoryLimitInput`; `PUT "/{key}/limit"` (D3, D4, D5) | `api-requests` |
| alterar | `tests/test_migrations.py` | `"021_category_limit.sql"` em `EXPECTED_MIGRATIONS`; `eighteen` → `nineteen`, `"migrations applied: 19"`; teste novo: base migrada até `020` com uma categoria, aplicar `021` → coluna `NULL`; `UPDATE … = 0` levanta `IntegrityError`; `= 100` grava | `unit-testing` |
| alterar | `tests/test_catalogue.py` | `set_monthly_limit`: grava `150000`; `None` apaga; `0` e `-1` → `InvalidLimitError` e o valor anterior fica; chave inexistente e `UNCATEGORISED` → `CategoryNotFoundError`; categoria do sistema aceita | `unit-testing` |
| alterar | `tests/test_categories_api.py` | `GET` traz `monthly_limit_cents: None` para todas após o seed; `PUT` 200 com `150000` e o `GET` reflete; `PUT null` volta a `None`; `PUT 0` → 422 "O limite precisa ser maior que zero." e o `GET` mantém o anterior; `PUT` sem campo → 422 Pydantic; chave inexistente e `"Não classificado"` → 404; categoria do sistema aceita; sem sessão → 401; `/openapi.json` lista `put` em `/api/categories/{key}/limit` | `api-requests`, `unit-testing` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `src/features/categories/types/category.ts` | `monthly_limit_cents: number \| null` (D5) | — |
| criar | `src/features/categories/types/category-limit-schema.ts` | `categoryLimitSchema`, `CategoryLimitInput` (D5) | `forms` |
| criar | `src/features/categories/utils/limit-cents.ts` | `toCents`, `fromCents` (D5) | — |
| criar | `src/features/categories/api/set-category-limit.ts` | `setCategoryLimit` (`PUT`), `useSetCategoryLimit` invalidando `['categories']` (D6) | `api-requests` |
| criar | `src/features/categories/components/category-limit-form.tsx` | formulário em linha do limite; RHF + Zod; `setError` no 422; `Escape`/"Cancelar" → `onDone` (D6) | `forms`, `interface-design`, `error-handling`, `component-robustness` |
| alterar | `src/features/categories/components/category-item.tsx` | modo `'limit'`; texto "Limite: R$ X"/"Sem limite"; botão "Limite"; monta `CategoryLimitForm` (D6) | `interface-design`, `client-state` |
| alterar | `src/testing/mocks/handlers.ts` | `generateFakeCategories` com `monthly_limit_cents` (Compras `150000`, Alimentação `80000`, demais `null`); `POST` cria com `null`; `PUT /api/categories/:key/limit` (404; `<= 0` → 422 "O limite precisa ser maior que zero."; senão grava e devolve o item) | `api-mocking` |
| criar | `src/features/categories/utils/__tests__/limit-cents.test.ts` | `toCents('')` → `null`; `'12.5'` → `1250`; `'0.1'` → `10`; `'1,99'` → `199`; `'19.99'` → `1999` (sem erro de ponto flutuante); `fromCents(null)` → `''`; `fromCents(150000)` → `'1500.00'` | `unit-testing` |
| criar | `src/features/categories/components/__tests__/category-limit-form.test.tsx` | abre com o valor atual (`'1500.00'`) e foco; vazio + Enter → `PUT` com `null`; `'250.5'` + "Salvar" → `PUT` com `25050`, "Salvando…" enquanto pendente, `onDone` chamado; `'0'` → "Informe um valor maior que zero." sem chamada e o campo mantém `'0'`; `'1.999'` → "Use no máximo duas casas decimais."; 422 do servidor no campo; 500 → `Alert` genérico e valor mantido; `Escape` → `onDone` sem chamada; Enter duas vezes → uma chamada | `component-testing`, `forms`, `api-mocking` |
| alterar | `src/features/categories/components/__tests__/categories-list.test.tsx` | "Compras" mostra "Limite: R$ 1.500,00" e "Pet shop" mostra "Sem limite"; botão "Definir limite de Supermercado" presente em linha do sistema; clicar abre o campo; salvar `'300'` → lista mostra "Limite: R$ 300,00" e `invalidateQueries(['categories'])` espiado | `component-testing`, `api-mocking` |
| alterar | `e2e/categories.spec.ts` | depois de criar "Pet shop": "Sem limite" visível; "Limite" → `'120.50'` → Enter → "Limite: R$ 120,50"; abrir de novo, apagar, Enter → "Sem limite"; `'0'` → erro junto do campo; `reload` mantém | `e2e-testing` |
| alterar | `docs/design.md` | linha "Campo numérico em reais" (fatia 012) | `interface-design` |
| alterar | `docs/roadmap.md` | item 012 → `review` ao abrir o PR | — |

## Estimativa de tamanho

Jornadas: 1 (o dono define, altera ou remove o limite de uma categoria na página que já existe) · Telas novas: 0 · Linhas alteradas (sem testes e sem mocks): ~65 Python (migração 1, `NUMBERING.md` 1, `queries/categories.py` ~5, `catalogue.py` ~15, `routers/categories.py` ~25) + ~175 em `src/` (tipo 1, schema ~15, `limit-cents.ts` ~10, `set-category-limit.ts` ~25, `category-limit-form.tsx` ~80, `category-item.tsx` ~25) + ~1 em `docs/design.md`; ~240 no total · Fases previstas: 2 (1: migração `021`, `CategoryRow`, `set_monthly_limit`, `PUT /limit`, `GET` com o campo, testes de migração, domínio e API, handler MSW; 2: tipo, schema, `limit-cents`, mutation, `CategoryLimitForm`, `CategoryItem`, testes de componente, e2e, `design.md`).

Sinais de "grande demais": 1 jornada, 0 telas novas, 2 fases, ~240 linhas — nenhum dispara.

## Dívida encontrada

- `src/features/expenses/api/get-categories.ts` (`Category { key; label }`) continua chamando `GET /api/categories` em paralelo ao da feature `categories`; o campo novo passa a viajar nas duas respostas. Item já registrado no roadmap (`shared-categories-query`, SPEC 010); nada novo aqui.
- `useRenameCategory` invalida `['expenses']` mesmo sem mudar gasto; `useSetCategoryLimit` invalida só `['categories']`. Quando a fatia 013 mostrar limite em "Gastos", a invalidação de `['expenses']` entra no hook de limite na mesma tarefa.
