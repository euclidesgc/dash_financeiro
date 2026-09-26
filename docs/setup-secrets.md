# Segredos e configuração

O painel lê a configuração do arquivo `.env` na raiz do projeto (ou do
arquivo apontado por `DASH_ENV_FILE`); variável já definida no ambiente
vale sobre o arquivo. Esta página é a lista de tarefas para preencher o
`.env`.

```bash
cp .env.example .env
```

## Acesso ao painel

| Variável | Segredo | Para que serve e onde obter |
|---|---|---|
| `LOGIN` | não | nome do único usuário do painel, à sua escolha |
| `PASSWORD` | sim | senha desse usuário, à sua escolha. `uv run python -m app.auth.seed` grava o usuário (ou troca a senha) na base; sem `LOGIN` ou `PASSWORD` o comando para e diz qual falta |
| `SESSION_SECRET` | sim | assina o cookie de sessão. Opcional: vazio, o painel gera um na primeira subida e o guarda em `data/session.key` (ou em `DASH_KEY_PATH`). Para fixar, gere com `openssl rand -hex 32` |
| `DASH_DB_PATH` | não | caminho do arquivo SQLite; vazio, `data/dash.sqlite` |

## Sincronização com a Pluggy

| Variável | Segredo | Para que serve e onde obter |
|---|---|---|
| `DASH_SYNC_SOURCE` | não | de onde a atualização lê os registros: `arquivo` (padrão, o consolidado em `data/processed/`) ou `pluggy` (busca na Pluggy as conexões cadastradas na tela Conexões) |
| `PLUGGY_CLIENT_ID` | sim | identificador da aplicação no painel da Pluggy (dashboard.pluggy.ai → Applications) |
| `PLUGGY_CLIENT_SECRET` | sim | segredo da mesma aplicação, na mesma tela |

Com `DASH_SYNC_SOURCE=pluggy` e alguma das duas credenciais vazia, a
atualização não roda e a tela diz qual variável falta. O script manual
(`uv run python -m ingestao.pluggy_extract`) usa as mesmas duas.

## Opcionais

| Variável | Segredo | Para que serve e onde obter |
|---|---|---|
| `ANTHROPIC_API_KEY` | sim | chave da Anthropic para o Consultor (chat em `/app/advisor`), criada em platform.claude.com → API keys. Com ela, o chat usa a Anthropic; sem ela, usa a chave do Gemini |
| `DASH_ADVISOR_MODEL` | não | modelo da Anthropic usado pelo chat; vazio, `claude-opus-5` |
| `GEMINI_API_KEY` | sim | chave do Gemini, criada no Google AI Studio (aistudio.google.com → Get API key). Serve à tela antiga do Consultor e ao chat quando não há `ANTHROPIC_API_KEY`. A chave cadastrada na tela Configuração vale sobre esta |
| `DASH_ADVISOR_GEMINI_MODEL` | não | modelo do Gemini usado pelo chat; vazio, `gemini-3.8-flash` |
| `DASH_CNPJ_LOOKUP` | não | `1`, `true` ou `sim` liga a consulta de nome fantasia por CNPJ na BrasilAPI; desligada por padrão, porque cada consulta conta a um terceiro com quem você tem relação comercial |

Segredo nunca entra no repositório: `.env` e `data/` estão no
`.gitignore`, e só o `.env.example`, sem valores, é versionado.
