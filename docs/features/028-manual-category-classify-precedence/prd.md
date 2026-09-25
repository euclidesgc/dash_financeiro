# PRD 028 — manual-category-classify-precedence

## Valor

Quando o dono troca à mão a categoria de um gasto, essa escolha vale em todo o painel. Hoje ela vale na lista de gastos, mas as telas antigas (gastos por grupo, regras, resumo) ainda podem pôr o mesmo gasto em outro grupo, com outra natureza e outra essencialidade, porque uma regra pela descrição passa na frente da escolha dele. O painel mostra dois números diferentes para a mesma pergunta.

## Usuários

O único usuário do painel, dono das contas, depois de ajustar a categoria de um gasto (um por um ou "aplicar aos parecidos") e abrir qualquer tela que agrupa por grupo, natureza ou essencialidade.

## Requisitos

- **R1** — Um gasto com categoria ajustada à mão fica no grupo, na natureza e na essencialidade da categoria escolhida, mesmo que uma regra pela descrição do recebedor aponte para outro lugar.
- **R2** — Um gasto ajustado à mão para "Sem categoria", ou para uma categoria sem regra de agrupamento, cai no grupo de "não classificado", e não no grupo de uma regra pela descrição.
- **R3** — Ao voltar o gasto para a categoria automática, as regras pela descrição voltam a valer para ele, como antes do ajuste.
- **R4** — Gastos que nunca foram ajustados continuam classificados como hoje: a regra pela descrição continua passando na frente da regra por categoria.
- **R5** — Na tela antiga de correção por recebedor, a prévia ("o beneficiário alcança N lançamentos") conta só os gastos que a correção pode mover: os ajustados à mão ficam de fora, e o resultado depois de salvar bate com a prévia.
- **R6** — A escolha manual continua valendo depois de uma atualização dos registros bancários.

## Fora de escopo

- Migrar as telas antigas para a nova interface.
- Mudar como as regras pela descrição ou por categoria são criadas e editadas.
- Dar grupo próprio a categorias criadas pelo dono (continuam no grupo de "não classificado" até existir regra para elas).

## Pontos em aberto

- nenhum
