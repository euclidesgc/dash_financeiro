# PRD 022 — setup-secrets-pluggy-credentials

## Valor

A página que ensina a preencher o `.env` descreve variáveis de outro projeto (Postgres, `DATABASE_URL`, `CORS_ORIGINS`) e não cita as credenciais da Pluggy nem a chave que liga a sincronização com ela. Quem segue a página não consegue ligar a atualização pela Pluggy. Com a fatia, a página lista exatamente o que o painel lê e onde obter cada valor.

## Usuários

O único usuário do painel, ao configurar o ambiente local.

## Requisitos

- **R1** — A página cita `PLUGGY_CLIENT_ID` e `PLUGGY_CLIENT_SECRET`, onde obtê-las, e `DASH_SYNC_SOURCE`, que liga a sincronização pela Pluggy.
- **R2** — A página lista as variáveis que o painel lê (`LOGIN`, `PASSWORD`, `SESSION_SECRET`, `DASH_DB_PATH`, `GEMINI_API_KEY`, `DASH_CNPJ_LOOKUP`) e nenhuma que ele não lê.
- **R3** — O `.env.example` traz toda variável citada na página como necessária para ligar a Pluggy.

## Fora de escopo

- Mudar como o painel lê a configuração.

## Pontos em aberto

- nenhum
