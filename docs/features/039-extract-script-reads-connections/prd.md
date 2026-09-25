# PRD 039 — extract-script-reads-connections

## Valor

Desde a tela "Conexões", a atualização do painel busca na Pluggy só as conexões cadastradas nela. O script manual de extração, que o dono usa para criar uma conexão nova, ver o estado de cada uma e baixar tudo de uma vez, ainda lê e grava a lista antiga num arquivo de texto. As duas listas divergem em silêncio: a conexão criada pelo script não aparece na tela nem entra na atualização, e o script consulta conexões que o dono já removeu. Com a fatia, o script usa a mesma lista da tela.

## Usuários

O único usuário do painel, que roda o script de extração no terminal quando cria ou confere uma conexão.

## Requisitos

- **R1** — Sem `--item`, os comandos `status` e `extrair` do script consultam exatamente as conexões da tela "Conexões", na mesma ordem em que ela as mostra.
- **R2** — Sem conexão cadastrada e sem `--item`, `status` e `extrair` param com "Nenhuma conexão cadastrada. Cadastre em Conexões ou passe --item.".
- **R3** — `criar-item` cadastra a conexão criada na lista da tela; se ela já estiver lá, segue sem duplicar. A mensagem final diz que a conexão foi cadastrada em Conexões.
- **R4** — O script deixa de ler e gravar o arquivo de texto antigo e a variável de ambiente de conexão avulsa; `--item` continua consultando uma conexão só, sem tocar na lista.
- **R5** — A ajuda do script (`--help`) diz como rodá-lo: da raiz do projeto, `uv run python -m ingestao.pluggy_extract <subcomando>`.

## Fora de escopo

- Trazer para a tela as conexões do arquivo antigo (já existe o comando de importação da 021).
- Mudar o que o script baixa ou onde grava os dados brutos.

## Pontos em aberto

- nenhum
