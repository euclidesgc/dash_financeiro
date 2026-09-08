# Brief — 030-numeracao-de-migracao-sem-buraco

**Trilha:** rápida · **Este documento funde discovery, PRD e spec.**

## Problema

`app/migrations/runner.py:36` aplica as migrações em **ordem lexical do nome do
arquivo**, pulando as que já estão em `schema_migrations`. A sequência de hoje é
`001`–`015` e `018`: **`016` e `017` não existem** — foram números reservados por
itens que fecharam fora de ordem.

Isso faz a mesma migração rodar em **duas ordens diferentes em duas máquinas**.
Numa base que já aplicou `018`, uma migração `016` escrita amanhã é desconhecida,
entra, e roda contra um esquema que tem `018` dentro — que não é o esquema que ela
pressupõe. Numa base nova, a mesma `016` roda antes da `018`, na ordem certa.

Nada quebrou porque nenhum buraco foi preenchido. É defeito latente, e o que o
torna perigoso é ser silencioso: as duas execuções dizem `applied`.

Três validadores independentes relataram o salto (itens `024`, `025` e `027`).
Pela norma 20, segunda ocorrência é causa raiz.

## Requisitos

- **RF-01.** O aplicador **recusa** uma migração cuja versão ordene **abaixo** da
  maior já registrada em `schema_migrations`, com mensagem que nomeia as duas
  versões e diz o que fazer.
- **RF-02.** A recusa não deixa o banco pela metade: nada é aplicado na mesma
  execução em que a recusa acontece.
- **RF-03.** Uma árvore sem buraco continua aplicando exatamente como aplica hoje,
  em base nova e em base parcialmente migrada.
- **RF-04.** A numeração perde os buracos: `016` e `017` deixam de ser vãos.

## Não-escopo

- Renumerar migração já aplicada na base do dono. Renomear um arquivo já
  registrado em `schema_migrations` o faria ser reaplicado.

## Riscos

- **Travar a subida do painel por um falso positivo.** RF-03 é o que mede: base
  nova e base parcial continuam subindo.
