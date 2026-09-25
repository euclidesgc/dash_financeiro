# SPEC 020 — jinja-sync-button-exclusive-lock

Estado atual:

- `app/sync/exclusive.py` · `exclusive_synchronise` tenta a trava do processo sem esperar; ocupada, levanta `SyncBusyError(BUSY_MESSAGE)`. `POST /api/sync/run` (`app/routers/sync.py`) usa essa função e responde 409.
- `app/routers/summary.py` · `synchronise_now` (`POST /sincronizar`, tela Jinja de resumo) chama `synchronise` direto, sem a trava, e devolve o resultado no mesmo campo `notice` da recusa de data.
- `app/templates/resumo.html` só mostra `notice` com a base preenchida e sempre acrescenta "A tela responde pela data de hoje.". O resultado da atualização some com a base vazia, justamente quando o dono mais atualiza, e aparece com uma frase sobre data que não se aplica.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `synchronise_now` passa a chamar `exclusive_synchronise` (D1). |
| R2 | `SyncBusyError` vira aviso na própria tela, com a mensagem da exceção (D2), no painel "Os dados" (D3). |
| R3 | O caminho feliz continua em `_said(outcome)`, sem mudança. |

## Decisões

- **D1** — `app/routers/summary.py` importa `SyncBusyError` e `exclusive_synchronise` de `app.sync.exclusive` e deixa de importar `synchronise`. A dependência já corre de `app/routers` para `app/sync`; nada novo entre pacotes.
- **D2** — Trava ocupada: `_answer(request, conn, reference, notice=str(busy), status_code=409)`, o mesmo formato da recusa por credencial ausente (tela re-renderizada com aviso, status de erro). 409 é o status que a API da tela nova já usa para o mesmo caso.
- **D3** — O resultado do botão ganha campo próprio, `sync_notice` (com `sync_done` para o sucesso), mostrado em `app/templates/fragments/resumo_sincronizacao.html`, acima do botão e fora do `if empty`. `notice` volta a ser só a recusa de data, repassada também no `POST`. Sem isso o aviso de R2 não aparece numa base vazia.
- Alternativa descartada: redirecionar a tela antiga para a nova — muda o comportamento combinado da tela e está fora do escopo.

## Arquivos afetados

- `app/routers/summary.py`, `app/templates/fragments/resumo_sincronizacao.html` (alterar)
- `tests/test_sync_api.py` (alterar)

## Skills aplicáveis

python-tratamento-de-erros, python-testes-de-integracao-httpx.
