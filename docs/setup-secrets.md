# Segredos e configuração — dash_financeiro — painel financeiro pessoal de um usuário, rodando local. Login, dashboard das movimentações bancárias (sincronizadas da Pluggy todo dia ou sob demanda) e IA que ajuda a alcançar o plano de curto, médio e longo prazo. Stack Python 3.12 + FastAPI + Jinja2 + HTMX + SQLite. O objetivo do produto é sair de um déficit de R$ 4.940,72/mês.

Os valores são seus; o harness sabe quais variáveis existem e onde cada uma
é obtida. Esta página é a lista de tarefas para preencher o `.env` — e a
aplicação recusa subir com variável obrigatória faltando, em vez de falhar
na primeira requisição que a usa.

```bash
cp .env.example .env
```

| Variável | Segredo | Onde obter |
|---|---|---|
| `DATABASE_URL` | sim | string de conexão do Postgres no formato `postgresql+asyncpg://…`; em teste, o CI sobe o serviço e injeta a sua |
| `SECRET_KEY` | sim | gere com `openssl rand -base64 48`; nunca reaproveite entre ambientes |
| `APP_ENV` | não | `local`, `staging` ou `production`; é o que decide se a documentação interativa fica exposta |
| `CORS_ORIGINS` | não | origens permitidas separadas por vírgula; `*` nunca em produção |

Segredo nunca entra no repositório nem em variável de build exposta ao
cliente. O `gitleaks` roda no CI e reprova o diff que contiver um.
