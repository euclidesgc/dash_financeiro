# SPEC 002 — atualizar registros

Segunda fatia da SPA. Acrescenta à página de saldos (`/app/`) um painel com a última atualização dos registros bancários e o botão "Atualizar agora", sobre a sincronização que já existe em `app/sync/`.

O que o código já faz hoje, e que esta SPEC reaproveita:

- `app/sync/__init__.py` · `synchronise(conn, *, today)` — recusa sem credencial da Pluggy (`MissingCredentialError`, sem gravar linha), lê `data/processed/transacoes.json` e `data/raw/accounts_*.json`, chama `ingest`, roda a pós-carga (classificação, compromissos, escada de dívida) e rebaixa a execução se a pós-carga falha. `last_runs(conn)` lê a última tentativa e o último sucesso; `readable(message)` traduz a mensagem técnica para pt-BR. `python -m app.sync` é o comando da atualização diária.
- `sync_runs` (migração `001`, ajustada na `006`) — `started_at`, `finished_at`, `source`, `status` (`ok` | `failed`), `transactions_count`, `accounts_count`, `transactions_present`, `accounts_present`, `message`. Toda linha é gravada com `finished_at` preenchido; `source` guarda o caminho do arquivo lido. **Nenhuma migração é necessária**: data/hora, sucesso/falha e motivo já estão nas colunas `finished_at`, `status` e `message`.
- O que **não** existe: nenhuma chamada à Pluggy dentro de `app/`. A busca real vive nos scripts manuais `ingestao/pluggy_extract.py` (autentica, lê `/items/{id}`, `/accounts`, `/v2/transactions`, grava `data/raw/*.json`) e `ingestao/pluggy_consolidate.py` (lê `data/raw`, escreve `data/processed/transacoes.json`). O item `037` do `product/` especificou um cliente Pluggy direto em três fases e nunca foi implementado. Com `DASH_SYNC_SOURCE=pluggy`, `synchronise` só confere a credencial e continua lendo o arquivo — R4 não é atendido hoje.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `GET /api/sync/status` devolve `last_run.finished_at` (ISO, UTC) da última linha de `sync_runs`; `SyncPanel` mostra "Última atualização: {formatDateTime}" (já converte para o fuso do navegador em pt-BR). |
| R2 | `last_run` é `null` quando `sync_runs` está vazia; o painel mostra "Nunca atualizado". |
| R3 | `last_run.status` (`ok` \| `failed`) vira selo "Concluída" ou "Falhou"; `last_run.reason` traz `readable(message)` e o painel mostra "A última atualização falhou: {reason}" num `Alert`. |
| R4 | `POST /api/sync/run` chama `exclusive_synchronise`. Com `DASH_SYNC_SOURCE=pluggy`, `synchronise` passa a chamar `fetch_from_pluggy` (D2) antes de ler os arquivos: autentica, lê cada conexão de `data/item_ids.txt`, suas contas e todos os lançamentos, grava o bruto em `data/raw`, consolida em `data/processed` e só então `ingest` grava contas, saldos e lançamentos na base. |
| R5 | `useRunSync().isPending` desabilita o botão com o texto "Atualizando…" e mostra `<p role="status">` "Atualização em andamento. Isso pode levar alguns minutos."; `status.running` (outra aba ou o comando dentro do mesmo processo) produz o mesmo estado. |
| R6 | `onSuccess` da mutation invalida `['sync','status']` e `['accounts','balances']`; o React Query refaz as duas consultas sem recarregar a página. |
| R7 | Credencial ausente → 503 com a frase de `MissingCredentialError`; rede fora, credencial recusada e conexão expirada → execução `failed` gravada com motivo em pt-BR (D2). Nos dois casos o painel mostra `Alert` com "Tentar de novo", que dispara a mutation de novo. |
| R8 | `threading.Lock` em `app/sync/exclusive.py`, adquirido sem bloquear; segundo `POST` responde 409 "Já existe uma atualização em andamento." sem gravar linha. No cliente, o botão fica desabilitado enquanto `isPending` ou `status.running`. |
| R9 | O comando `python -m app.sync` grava na mesma `sync_runs`; `GET /api/sync/status` lê a tabela, não memória. A consulta refaz sozinha a cada 5 s enquanto `running` for verdadeiro e ao focar a janela (padrão do React Query). |

## Decisões técnicas

### D1 — Rota da sincronização é `def` (threadpool), não `async def`

- Escolha: `POST /api/sync/run` e `GET /api/sync/status` são `def`. O trabalho é todo bloqueante — `httpx.Client` síncrono, escrita em `data/raw`, `sqlite3`, pós-carga em SQL — e o FastAPI já despacha `def` para o threadpool, o que mantém o event loop livre (norma 31). Os demais endpoints `/api/*` da fatia 001 já são `def`; a fatia não mistura formas.
- Alternativa descartada: `async def` com `run_in_threadpool(synchronise, …)` — motivo: mesma thread de execução, uma camada a mais para ler, e `connect()`/`conn.close()` teriam de ir junto para dentro da chamada. Só compensaria se a rota fizesse algum `await` real, e não faz.

### D2 — A busca na Pluggy reaproveita a cadeia extrair → consolidar → ingerir, dentro de `synchronise`

- Escolha: novo módulo `app/sync/fetch.py` com `fetch_from_pluggy(config, *, transport=None) -> None`, cliente `httpx.Client` (dependência já declarada; transporte injetável para o teste, como o `conftest` exige — `httpx.get/post` de módulo são bloqueados na suíte). Passos: `POST /auth` com `config.pluggy`; para cada id de `ingestao.pluggy_extract.itens_salvos()`: `GET /items/{id}`, `GET /accounts?itemId=`, `GET /v2/transactions?accountId=&pageSize=500` seguindo o cursor `next`; cada resposta gravada em `data/raw` por `ingestao.pluggy_extract.salvar` (mesmos nomes de arquivo que o consolidador lê: `accounts_*.json`, `*transactions_*.json`); ao fim, `ingestao.pluggy_consolidate.main()`. `synchronise` chama `fetch_from_pluggy` logo depois da checagem de credencial, só quando `config.sync_source == PLUGGY`, e converte `PluggyFetchError` em linha `failed` (via um `_record_failed(conn, source, message)` extraído do `_record_failure` atual). Nenhum segredo entra na mensagem.
  - Falhas mapeadas (mensagem gravada em `sync_runs.message`, já em pt-BR, com prefixo `pluggy: ` que `readable` remove):
    - `POST /auth` ≠ 200 → "a Pluggy recusou as credenciais; confira PLUGGY_CLIENT_ID e PLUGGY_CLIENT_SECRET."
    - `httpx.HTTPError` (sem rede, tempo esgotado) → "a Pluggy não respondeu; verifique a conexão com a internet e tente de novo."
    - `GET /items/{id}` com `status` ou `executionStatus` em `LOGIN_ERROR`, `WAITING_USER_INPUT`, `USER_AUTHORIZATION_REVOKED`, ou resposta 404 → "a conexão {connector.name} pede novo login em meu.pluggy.ai."
    - qualquer outra resposta ≠ 200 → "a Pluggy respondeu {status} em {caminho}."
    - lista de ids vazia → "nenhuma conexão registrada em data/item_ids.txt."
  - Uma falha em qualquer conexão falha a execução inteira e não grava lançamento: mantém o "tudo ou nada" que `ingest` já tem.
- Alternativa descartada: implementar o cliente direto da spec do item 037 (`pluggy_items`, religação, lápides, rotina em thread) — motivo: são 73 requisitos e três fases; esta fatia precisa do caminho feliz de ponta a ponta, e os scripts manuais já sabem falar com a API. O 037 continua no `product/` como evolução (Dívida encontrada).
- Alternativa descartada: chamar `ingestao/pluggy_extract.py` por `subprocess` — motivo: ele lê `.env` direto do disco (ignora `DASH_ENV_FILE`), imprime no stdout e sai com `SystemExit`; não dá para testar sem rede nem para mapear o motivo da falha.

### D3 — Uma sincronização por vez: `threading.Lock` no processo, 409 quando ocupado

- Escolha: `app/sync/exclusive.py` com `_LOCK = threading.Lock()`, `SyncBusyError`, `exclusive_synchronise(conn, *, today)` (`acquire(blocking=False)`; se falhar, levanta `SyncBusyError` sem tocar o banco) e `is_synchronising() -> bool` (`_LOCK.locked()`). O router traduz `SyncBusyError` em 409.
- Alternativa descartada: coluna `status = 'running'` em `sync_runs` (RF-56 do 037) — motivo: exige migração, tratamento de linha órfã ao subir o painel e leitura especial no Jinja; a trava de processo resolve R8 para o único processo que serve a tela. Limite conhecido: `python -m app.sync` roda em outro processo e não vê a trava (a mesma escolha da discovery do 037); o dono roda a rotina diária de madrugada, fora do horário em que aperta o botão.

### D4 — Contratos JSON

- `GET /api/sync/status` · 200 `{"running": bool, "last_run": {"finished_at": str|null, "status": "ok"|"failed", "reason": str|null} | null}`. `last_run` vem da última linha de `sync_runs` (`last_runs(conn)["latest"]`); `reason` é `readable(message)` quando `status == "failed"`, senão `null`.
- `POST /api/sync/run` · sem corpo · 200 com o mesmo `SyncStatus` já lido depois da execução (com `ok` ou `failed`; a falha registrada é resultado, não erro de HTTP) · 409 `{"detail": "Já existe uma atualização em andamento."}` · 503 `{"detail": "<texto de MissingCredentialError>"}`.
- Modelos Pydantic no router (`SyncRun`, `SyncStatus`); o `/openapi.json` gerado é o contrato (norma 3). A rota lê `today` de `reference_date()` como o comando.
- Alternativa descartada: `POST` responder 202 e o cliente fazer polling — motivo: a tela precisa de "terminou, renove a lista" e a resposta síncrona dá isso sem estado extra; o `refetchInterval` cobre o caso de outra aba.
- Alternativa descartada: 400 para credencial ausente, como o Jinja faz — motivo: a falta é de configuração do servidor, não do pedido; 503 diz isso e o cliente só mostra o `detail`.

### D5 — Estado da sincronização mora no React Query

- Escolha: `syncStatusQueryOptions` (queryKey `['sync','status']`, `refetchInterval: (query) => query.state.data?.running ? 5_000 : false`) e `useRunSync` (`useMutation` que, em `onSuccess`, faz `setQueryData(['sync','status'], resposta)` e `invalidateQueries({ queryKey: ['accounts','balances'] })`; em `onError`, invalida `['sync','status']` para o 409 refletir o `running`). Nenhum Zustand: tudo é estado de servidor.
- Alternativa descartada: guardar "atualizando" num store — motivo: duplicaria `isPending` da mutation e `running` do servidor.

### D6 — Feature `sync` separada de `accounts`

- Escolha: `src/features/sync/` (api, types, components). A rota `dashboard.tsx` monta `<SyncPanel />` entre o texto de apoio e `<BalancesList />`; a feature não importa de `accounts` — a invalidação usa a queryKey literal `['accounts','balances']`, que é contrato de cache, não import. Zona nova no `eslint.config.js`.
- Alternativa descartada: pôr o painel dentro de `features/accounts` — motivo: a sincronização vai servir também à lista de gastos (fatia 003); nascer separada evita mover depois.

### D7 — O e2e sincroniza da fonte de arquivo

- Escolha: `scripts/e2e-backend.sh` passa a exportar `DASH_TRANSACTIONS_PATH=tests/data/sync_transactions.json` e `DASH_ACCOUNTS_GLOB=tests/data/sync_accounts.json` e a semear a taxonomia (`seed_taxonomy`) antes de subir o uvicorn, para a pós-carga não falhar num banco novo. `DASH_SYNC_SOURCE` fica em `arquivo`: a jornada prova botão → API → `sync_runs` → tela renovada, sem rede. A busca na Pluggy se prova em `tests/test_sync_fetch.py` com `httpx.MockTransport`.
- Alternativa descartada: e2e com um servidor Pluggy falso — motivo: um processo a mais no Playwright para provar o que o teste unitário do transporte já prova.

## Interface

Receitas do `docs/design.md` usadas: subtítulo (`h2`), texto de apoio, selo de status, botão principal, carregando, erro (via `Alert`), botão de erro.

Receitas novas a acrescentar em "Padrões acrescentados pelas entregas":

| Padrão | Classes | Fatia |
|---|---|---|
| Painel de situação | `<section className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-md border border-gray-200 p-4">`; texto à esquerda em `min-w-0`, ação à direita | 002 |
| Selo de erro | par `bg-red-100 text-red-800` para o selo de status | 002 |

### Tela: Saldos (`/app/`) — painel de atualização

Entra entre o texto de apoio "Contas e cartões sincronizados da Pluggy." e a lista de saldos. De cima para baixo:

- `<h2>` "Atualização dos registros" (receita subtítulo).
- Painel de situação (`SyncPanel`):
  - esquerda, empilhado:
    - linha 1, `text-gray-900`: "Última atualização: {data e hora}" (ex.: "Última atualização: 22/09/2026 08:15") ou "Nunca atualizado".
    - linha 2: selo de status — "Concluída" (`bg-green-100 text-green-800`), "Falhou" (selo de erro), "Em andamento" (`bg-amber-100 text-amber-800`, quando `running` ou `isPending`).
  - direita: botão principal `type="button"` "Atualizar agora"; `disabled` com texto "Atualizando…" enquanto `isPending` ou `status.running`.
- Abaixo do painel, conforme o estado:
  - carregando o status (`role="status"`): "Carregando situação da atualização…" — no lugar do painel.
  - erro ao carregar o status (`Alert`): "Não foi possível carregar a situação da atualização." + "Tentar de novo" (refetch) — no lugar do painel.
  - em andamento (`<p role="status" className="mt-2 text-gray-600">`): "Atualização em andamento. Isso pode levar alguns minutos."
  - última execução falhou (`Alert`): "A última atualização falhou: {reason}" + "Tentar de novo" (dispara a mutation).
  - mutation com erro (`Alert`, tem precedência sobre a anterior): 409 e 503 mostram o `detail` do servidor; outro erro mostra "Não foi possível atualizar. Verifique se o servidor está no ar e tente de novo."; sempre com "Tentar de novo".
- Depois do sucesso: nada de aviso extra — a data, o selo "Concluída" e a lista de saldos renovados são o feedback.
- Textos do servidor que chegam à tela (pt-BR): "Já existe uma atualização em andamento."; "Sincronização com a Pluggy exige PLUGGY_CLIENT_ID e PLUGGY_CLIENT_SECRET no ambiente. Enquanto não houver, o painel lê o arquivo já consolidado." (texto atual de `MissingCredentialError`); os motivos de D2.

## Arquivos

### Python (backend)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `app/sync/fetch.py` | `PluggyFetchError`, `fetch_from_pluggy(config, *, transport=None)`: auth, itens, contas, lançamentos por cursor, `salvar` em `data/raw`, `pluggy_consolidate.main()`; mensagens de D2; nunca loga credencial ou `apiKey` | `security`, `error-handling` |
| alterar | `app/sync/__init__.py` | `synchronise` chama `fetch_from_pluggy` quando `sync_source == PLUGGY` e grava `failed` em `PluggyFetchError`; `_record_failed(conn, source, message)` extraído; `readable` reconhece o prefixo `pluggy: ` | `error-handling` |
| criar | `app/sync/exclusive.py` | `SyncBusyError`, `exclusive_synchronise(conn, *, today)`, `is_synchronising()` (D3) | `component-robustness` |
| criar | `app/routers/sync.py` | `GET /api/sync/status`, `POST /api/sync/run`; modelos `SyncRun`, `SyncStatus`; 409/503; só traduz HTTP (norma 30) | `api-requests`, `error-handling` |
| alterar | `app/main.py` | inclui `sync.router` | — |
| alterar | `scripts/e2e-backend.sh` | exporta `DASH_TRANSACTIONS_PATH` e `DASH_ACCOUNTS_GLOB` para `tests/data/sync_*.json`; `seed_taxonomy(conn)` antes de subir (D7) | `e2e-testing` |
| criar | `tests/test_sync_fetch.py` | `MockTransport`: caminho feliz grava `data/raw` num `tmp_path` e consolida; auth 401 → credenciais recusadas; `httpx.ConnectError` → não respondeu; item `LOGIN_ERROR` e 404 → pede novo login; nenhuma mensagem contém o secret | `unit-testing`, `security` |
| criar | `tests/test_sync_api.py` | sem sessão 401; status em base vazia `last_run: null`; status depois de `ingest` mostra `ok` e `finished_at`; `run` com fonte arquivo devolve 200 `ok` e a linha nova; segundo `run` com a trava presa responde 409 sem linha nova; sem credencial e `DASH_SYNC_SOURCE=pluggy` responde 503; `failed` gravado vira `reason` legível | `api-requests`, `error-handling` |
| alterar | `tests/test_sync.py` | caso: `DASH_SYNC_SOURCE=pluggy` com credencial e `fetch_from_pluggy` falso levantando `PluggyFetchError` grava linha `failed` com o motivo | `unit-testing` |

### Ferramental (raiz)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| alterar | `eslint.config.js` | zona `{ target: './src/features/sync', from: './src/features', except: ['./sync'] }` | `project-structure` |
| alterar | `docs/design.md` | duas receitas novas (seção Interface) | `interface-design` |

### `src/` (SPA)

| Ação | Caminho | O que muda | Skills |
|---|---|---|---|
| criar | `src/features/sync/types/sync-status.ts` | `SyncRun { finished_at: string \| null; status: 'ok' \| 'failed'; reason: string \| null }`, `SyncStatus { running: boolean; last_run: SyncRun \| null }` | — |
| criar | `src/features/sync/api/get-sync-status.ts` | `getSyncStatus()`, `syncStatusQueryOptions` (`['sync','status']`, `refetchInterval` de D5), `useSyncStatus()` | `api-requests` |
| criar | `src/features/sync/api/run-sync.ts` | `runSync()` (`POST /api/sync/run`), `useRunSync()` com `onSuccess`/`onError` de D5 | `api-requests`, `error-handling` |
| criar | `src/features/sync/components/sync-panel.tsx` | `SyncPanel`: quatro estados do status, selo, botão, avisos e `Alert`s da seção Interface; usa `formatDateTime`, `Button`, `Alert` | `interface-design`, `error-handling`, `component-robustness` |
| criar | `src/features/sync/components/__tests__/sync-panel.test.tsx` | carregando; "Nunca atualizado"; data + "Concluída"; "Falhou" com motivo e "Tentar de novo"; clique em "Atualizar agora" desabilita com "Atualizando…" e ao terminar invalida `['accounts','balances']` (espiar `queryClient.invalidateQueries`); 409 mostra o `detail`; `running: true` desabilita o botão (MSW) | `component-testing`, `api-mocking` |
| alterar | `src/app/routes/dashboard.tsx` | monta `<SyncPanel />` entre o texto de apoio e `<BalancesList />` | `routing` |
| alterar | `src/testing/mocks/handlers.ts` | `GET /api/sync/status` (`running: false`, `last_run` ok com `finished_at: '2026-09-22T11:15:00+00:00'`) e `POST /api/sync/run` (200 com o mesmo formato); `fakeSyncStatus` exportado | `api-mocking` |
| alterar | `src/app/__tests__/login-to-balances.test.tsx` | depois do login, a tela mostra "Última atualização" | `integration-testing` |
| criar | `e2e/sync.spec.ts` | login → painel mostra "Nunca atualizado" → clica "Atualizar agora" → selo "Concluída", "Última atualização" com data e "Conta de sincronização" na lista sem recarregar | `e2e-testing` |

## Estimativa de tamanho

Jornadas: 1 (ver a última atualização e atualizar agora) · Telas novas: 0 (painel dentro da tela de saldos) · Linhas alteradas (sem testes): ~180 Python (`fetch.py` ~90, `exclusive.py` ~25, router ~45, `__init__.py` ~20) + ~190 em `src/` + ~15 de script/config · Fases previstas: 2 (busca na Pluggy + API de sincronização; painel na tela + e2e).

Nenhum sinal de "grande demais" dispara.

## Dívida encontrada

- `app/sync/__init__.py` grava `sync_runs.source` com o caminho do arquivo lido, não com quem disparou (`botao`/`comando`, como o item 037 previa). A tela não precisa disso; fica como está e vira item de roadmap junto do 037.
- O item `037-sincronizacao-real-com-a-pluggy` (`product/items/`) especifica o cliente Pluggy direto — `pluggy_items`, janela por conta, religação, lápides, `PATCH /items`, rotina em thread — e nunca foi implementado. Esta fatia entrega o caminho feliz por cima dos scripts de `ingestao/`; o 037 continua pendente como evolução e deve entrar no roadmap com dependência desta fatia.
- `ingestao/pluggy_extract.py` lê `.env` direto do disco (`ENV_PATH = ".env"`), ignorando `DASH_ENV_FILE`; `cmd_extrair` sai com `SystemExit` em vez de levantar exceção. `fetch.py` contorna usando só `salvar` e `itens_salvos`; os subcomandos manuais continuam com o defeito.
- `POST /sincronizar` (Jinja, `app/routers/summary.py`) não passa pela trava de D3: botão Jinja e botão React podem rodar ao mesmo tempo. Some quando o Resumo Jinja for desligado (fatias seguintes); registrado para o roadmap.
- `data/item_ids.txt` é a lista de conexões (D-008 do 037 recomendou registro editável na tela, norma 26). Fora de escopo aqui; item de roadmap.
- `docs/setup-secrets.md` descreve variáveis de outro projeto (`DATABASE_URL`, Postgres); não cita `PLUGGY_CLIENT_ID`, `PLUGGY_CLIENT_SECRET` nem `DASH_SYNC_SOURCE`. Reconciliação de doc a fazer no PR desta fatia (norma 8) ou como item.
