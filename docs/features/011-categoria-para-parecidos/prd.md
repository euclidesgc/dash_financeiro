# PRD 011 — categoria para parecidos

## Valor

O dono do painel corrige de uma vez a categoria de todos os gastos parecidos com o que acabou de ajustar, sem repetir o clique um a um.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", logo depois de trocar a categoria de um gasto (fatia 009), percebendo que outros gastos do mesmo recebedor ou da mesma descrição também estão na categoria errada.

## Requisitos

- **R1** — Depois que a troca de categoria de um gasto salva com sucesso, o usuário vê uma oferta discreta na linha, com o texto "Aplicar a N gastos parecidos", onde N é a quantidade de gastos parecidos calculada pelo servidor.
- **R2** — "Parecido" significa: mesmo recebedor, quando o gasto tiver recebedor identificado; ou, na ausência de recebedor, mesma descrição normalizada (sem diferenciar maiúsculas de minúsculas nem acentos).
- **R3** — Se não houver nenhum gasto parecido (N = 0), a oferta não aparece.
- **R4** — A oferta traz duas ações: "Aplicar" e "Agora não".
- **R5** — Escolher "Agora não" dispensa a oferta sem alterar nada; a categoria já trocada na linha original permanece.
- **R6** — Escolher "Aplicar" mostra um indicador de "Aplicando…" enquanto a categoria é propagada aos N gastos parecidos.
- **R7** — Ao concluir com sucesso, o usuário vê a confirmação "Categoria aplicada a N gastos", e a lista de gastos e o bloco "Por categoria" refletem a nova categoria em todos os gastos afetados, sem exigir recarregar a página.
- **R8** — Todos os gastos parecidos que receberam a categoria por essa aplicação ficam marcados como manuais (mesma indicação visual da fatia 009) e sobrevivem à próxima atualização dos registros, igual ao gasto original.
- **R9** — Se a aplicação falhar, o usuário vê o erro na oferta com a opção "Tentar de novo"; nenhum dos gastos parecidos muda de categoria até a nova tentativa ter sucesso.
- **R10** — A oferta só aparece depois de uma troca de categoria bem-sucedida (fatia 009); não aparece ao desfazer para "automática" nem em outras ações da linha.

## Fora de escopo

- Classificar automaticamente lançamentos futuros parecidos (regras automáticas ficam para outra fatia).
- Limite mensal por categoria (fatia 012).
- Editar a categoria em lote escolhendo manualmente quais gastos incluir ou excluir do grupo de parecidos.
- Desfazer em lote a aplicação (reverter os N gastos de uma vez).

## Pontos em aberto

- nenhum
