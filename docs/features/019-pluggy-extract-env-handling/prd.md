# PRD 019 — pluggy-extract-env-handling

## Valor

A atualização dos registros pela Pluggy e os comandos manuais de extração dependem dos mesmos scripts de `ingestao/`. Hoje esses scripts se comportam como programa de terminal: leem as credenciais sempre do `.env` da pasta atual, ignorando o arquivo que o painel foi configurado para usar, e encerram o processo quando algo falta. O painel convive com isso apanhando o encerramento no meio do caminho. O dono ganha duas coisas: o comando manual passa a usar as mesmas credenciais que o painel usa, e uma falha na consolidação chega ao painel como motivo legível, sem depender de um contorno.

## Usuários

O único usuário do painel, dono das contas, que usa o botão de atualização e, às vezes, os comandos manuais da Pluggy no terminal.

## Requisitos

- **R1** — O comando manual da Pluggy lê as credenciais do mesmo lugar que o painel: o arquivo apontado por `DASH_ENV_FILE` (ou `.env`), com variável de ambiente já definida valendo sobre o arquivo.
- **R2** — Sem credencial, o comando manual diz qual variável falta, sem mostrar nenhum segredo, e termina com erro.
- **R3** — Quando não há dados brutos para consolidar, a atualização pela tela fica registrada como falha com o motivo "a consolidação dos dados brutos falhou", como hoje, sem que nada no painel precise apanhar o encerramento de um script.
- **R4** — A consolidação chamada pelo painel não escreve nada na saída do servidor; o comando manual continua mostrando o resumo que mostra hoje.

## Fora de escopo

- Tirar a lista de conexões de `data/item_ids.txt` (item próprio do roadmap).
- Mudar o que a extração ou a consolidação fazem com os dados.

## Pontos em aberto

- nenhum
