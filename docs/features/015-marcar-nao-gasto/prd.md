# PRD 015 — marcar não-gasto

## Valor

O dono do painel tira da conta o que a automação não pegou como transferência entre contas próprias ou estorno (ou qualquer outro motivo), sem que isso mintam os totais — e pode voltar atrás se marcar errado.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", olhando um lançamento que aparece como gasto mas não devia contar (transferência para outra conta própria, estorno, ou outro motivo).

## Requisitos

- **R1** — Em cada linha da lista de gastos, o usuário vê a ação "Não é gasto".
- **R2** — Ao acionar "Não é gasto", o usuário escolhe um motivo entre "Transferência entre minhas contas", "Estorno" e "Outro".
- **R3** — Ao confirmar o motivo, o lançamento some imediatamente da lista de gastos e sai dos totais (sinal por categoria, teto do mês, bloco "Por categoria"), sem exigir recarregar a página.
- **R4** — Ao confirmar, o usuário vê um aviso confirmando a marcação com a opção "Desfazer"; usando "Desfazer" logo em seguida, o lançamento volta a aparecer como gasto e volta a contar nos totais.
- **R5** — Na barra da página "Gastos", o usuário vê um filtro "Mostrar: gastos | não são gastos".
- **R6** — No modo "não são gastos", o usuário vê os lançamentos marcados, cada um com o motivo escolhido.
- **R7** — Em cada linha do modo "não são gastos", o usuário vê a ação "Voltar a ser gasto", que remove a marcação: o lançamento volta a aparecer na lista de gastos e a contar nos totais.
- **R8** — Uma marcação de "não é gasto" sobrevive à próxima atualização dos registros: reingerir os lançamentos da Pluggy não desfaz a marcação manual.
- **R9** — Um lançamento que a automação já classifica como transferência entre contas próprias ou estorno não aparece na lista de gastos nem no modo "não são gastos"; ele não é afetado nem editável por esta fatia.

## Fora de escopo

- Ver e marcar entradas como não-gasto (fatia 016).
- Regra automática que aprenda a marcar lançamentos parecidos sozinha.
- Editar ou desmarcar em lote (mais de um lançamento por vez).
- Editar o motivo depois de marcado (é preciso desfazer e marcar de novo).

## Pontos em aberto

- nenhum
