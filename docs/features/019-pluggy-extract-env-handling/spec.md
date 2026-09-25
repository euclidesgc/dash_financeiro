# SPEC 019 — pluggy-extract-env-handling

Os scripts de `ingestao/` foram escritos para o terminal e o serviço de sincronização os reaproveita:

- `ingestao/pluggy_extract.py` · `autenticar` lê `ENV_PATH = ".env"` por `carregar_env`, ignorando `DASH_ENV_FILE` e o ambiente do processo; credencial ausente vira `KeyError`. Os `cmd_*` sinalizam erro com `SystemExit`, o que é certo num comando. O serviço (`app/sync/fetch.py`) só usa `itens_salvos` e `salvar` daqui.
- `ingestao/pluggy_consolidate.py` · `main` faz o trabalho, imprime o resumo e levanta `SystemExit` quando não há `data/raw/accounts_*.json`. `app/sync/fetch.py` chama esse `main` e apanha `SystemExit` para não matar a thread do servidor.

## Cobertura dos requisitos

| Requisito | Como é atendido |
|---|---|
| R1 | `read_credentials` (D1) usado por `autenticar`. |
| R2 | `MissingCredentialsError` traduzido para `SystemExit` só no `main` do comando (D1, D3). |
| R3 | `consolidate()` levanta `NoRawAccountsError`; `fetch_from_pluggy` o converte em `PluggyFetchError(CONSOLIDATION_FAILED)` (D2, D4). |
| R4 | `consolidate()` devolve as contagens; só `main` imprime (D2). |

## Decisões

- **D1** — `ingestao/pluggy_extract.py`: `class MissingCredentialsError(RuntimeError)`, `CREDENTIALS = ("PLUGGY_CLIENT_ID", "PLUGGY_CLIENT_SECRET")` e `read_credentials(env: Mapping[str, str] | None = None) -> tuple[str, str]`. Sem `env`, carrega `os.environ.get("DASH_ENV_FILE", ".env")` com `python-dotenv` (`override=False`, a mesma regra de `app/config.py::_environment`) e lê `os.environ`. A mensagem cita só os nomes das variáveis que faltam. `carregar_env` e `ENV_PATH` saem. `ingestao` não importa `app`: a dependência corre de `app` para `ingestao`, e inverter criaria ciclo.
- **D2** — `ingestao/pluggy_consolidate.py`: `class NoRawAccountsError(RuntimeError)` e `consolidate() -> dict[str, int]`, com o corpo atual de `main` sem os `print`, devolvendo as contagens do resumo (`transacoes`, `transferencias`, `inferidas`, `saques`, `estornadas`, `recorrentes`, `parcelamentos`). `main()` chama `consolidate()`, imprime o mesmo resumo de hoje e traduz `NoRawAccountsError` em `SystemExit` com a mensagem atual.
- **D3** — `ingestao/pluggy_extract.py::main` apanha `MissingCredentialsError` e o traduz em `SystemExit(str(erro))`. Os demais `SystemExit` dos `cmd_*` e das travas de `chamar` ficam: são do comando e o serviço não os alcança.
- **D4** — `app/sync/fetch.py` importa `consolidate` e `NoRawAccountsError` e apanha só `NoRawAccountsError`; nenhum `SystemExit` resta em `app/sync/`.
- Alternativa descartada: `ingestao` ler `app.config.load_config()` — inverte a direção da dependência entre os pacotes.

## Arquivos afetados

- `ingestao/pluggy_extract.py`, `ingestao/pluggy_consolidate.py`, `app/sync/fetch.py` (alterar)
- `tests/test_pluggy_scripts.py` (criar), `tests/test_sync_fetch.py` (alterar)

## Skills aplicáveis

python-tratamento-de-erros, python-tipagem-estrita, python-testes-unitarios.
