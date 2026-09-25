# SPEC 039 — extract-script-reads-connections

Estado atual:

- `ingestao/pluggy_extract.py` · `itens_salvos()` junta `data/item_ids.txt`, `data/item_id.txt` e `PLUGGY_ITEM_ID`; `registrar_item(item_id)` reescreve `data/item_ids.txt`. `cmd_status` e `cmd_extrair` usam `itens_salvos()` quando falta `--item`; `cmd_criar_item` chama `registrar_item`.
- `app/sync/connections.py` · `add_connection` (normaliza e grava, `DuplicateConnectionError`); `app/queries/pluggy_connections.py` · `list_item_ids` (ordem de cadastro).

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `itens_salvos(conn)` devolve `list_item_ids(conn)` (D1, D2). |
| R2 | `_ids_pedidos` levanta `SystemExit(NO_CONNECTIONS)` com lista vazia (D2). |
| R3 | `registrar_item(conn, item_id)` chama `add_connection` e ignora `DuplicateConnectionError` (D1). |
| R4 | Constantes `ITEM_FILE`, `ITENS_FILE` e a leitura de `PLUGGY_ITEM_ID` saem; `--item` não abre a base (D2). |
| R5 | Docstring com a forma de rodar (D4). |

## Decisões

- **D1** — `itens_salvos(conn) -> list[str]` e `registrar_item(conn, item_id) -> None` recebem a conexão SQLite; o script não repete SQL nem regra de formato, usa `list_item_ids` e `add_connection`.
- **D2** — `_abrir_base()` roda `run_migrations()` e devolve `connect()`, como `python -m app.sync.connections`; a base vem de `DASH_DB_PATH` (padrão `data/dash.sqlite`). `_ids_pedidos(args)` devolve `[args.item]` sem abrir a base; senão abre, lê e fecha. `NO_CONNECTIONS = "Nenhuma conexão cadastrada. Cadastre em Conexões ou passe --item."`.
- **D3** — `salvar` (grava a resposta bruta em `data/raw/`) sai de `ingestao/pluggy_extract.py` para `ingestao/raw.py`, que não importa nada do projeto; `app/sync/fetch.py` passa a importá-lo de lá. Sem isso, o script importando `app.sync.connections` fecha um ciclo (`app.sync` → `app.sync.fetch` → `ingestao.pluggy_extract` → `app.sync`) que quebra quando o script é carregado primeiro.
- **D4** — O script passa a importar `app`, então roda como módulo, da raiz do projeto: `uv run python -m ingestao.pluggy_extract <subcomando>`. A docstring, que é a ajuda do comando, diz isso; o shebang sai.
- Alternativa descartada: manter o arquivo como segunda fonte, lido quando a tabela está vazia — é a divergência que a fatia existe para acabar.

## Arquivos afetados

- `ingestao/pluggy_extract.py`, `app/sync/fetch.py` (alterar)
- `ingestao/raw.py` (criar)
- `tests/test_pluggy_scripts.py` (alterar)

## Skills aplicáveis

python-testes-unitarios, python-tipagem-estrita, python-tratamento-de-erros.
