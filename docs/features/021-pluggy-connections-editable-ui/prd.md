# PRD 021 — pluggy-connections-editable-ui

## Valor

A atualização dos registros bancários busca, na Pluggy, cada conexão que o dono autorizou (uma por banco). Hoje a lista dessas conexões mora num arquivo de texto da máquina, fora do painel: quando o dono refaz uma conexão no meu.pluggy.ai, a conexão ganha outro identificador e ele precisa editar o arquivo à mão, sem ver o que está cadastrado. Com a fatia, a lista vira uma tela do painel onde ele vê, cadastra e remove conexões, e a atualização passa a ler só o que está nessa tela.

## Usuários

O único usuário do painel, dono das contas, que refaz conexões na Pluggy quando um banco pede novo login.

## Requisitos

- **R1** — Uma tela "Conexões", no menu principal, lista as conexões cadastradas com o identificador de cada uma e a data do cadastro, da mais antiga para a mais nova.
- **R2** — O dono cadastra uma conexão colando o identificador que o meu.pluggy.ai mostra. Identificador vazio ou fora do formato da Pluggy é recusado com a mensagem "Informe um identificador de conexão da Pluggy (formato 8-4-4-4-12)."; identificador já cadastrado é recusado com "Essa conexão já está cadastrada.".
- **R3** — O dono remove uma conexão depois de confirmar a remoção.
- **R4** — Sem nenhuma conexão cadastrada, a tela diz "Nenhuma conexão cadastrada." e a atualização pela Pluggy falha com o motivo "nenhuma conexão cadastrada; cadastre em Conexões.".
- **R5** — A atualização pela Pluggy busca exatamente as conexões da tela; o arquivo de texto antigo deixa de ser lido por ela.
- **R6** — As conexões do arquivo antigo podem ser trazidas para a tela uma vez, por um comando, sem duplicar as que já estão cadastradas.

## Fora de escopo

- Nome amigável por conexão (o banco aparece nos saldos).
- Consultar na Pluggy se a conexão existe no momento do cadastro.
- Fazer o script manual de extração (`ingestao/pluggy_extract.py`) ler a tela.

## Pontos em aberto

- nenhum
