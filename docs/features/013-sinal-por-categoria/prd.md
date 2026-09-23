# PRD 013 — sinal por categoria

## Valor

O dono do painel vê, sem fazer conta de cabeça, se está dentro do que planejou gastar em cada categoria no mês, a tempo de reagir antes de estourar.

## Usuários

O único usuário do painel, dono das contas, na página "Gastos", olhando o bloco "Por categoria" (fatia 008), com limites já definidos em algumas categorias (fatia 012).

## Requisitos

- **R1** — Na página "Gastos", quando o filtro de período é exatamente um mês fechado, cada linha do bloco "Por categoria" que tem limite definido mostra um sinal: "Dentro" (verde) quando o gasto do mês é menor ou igual ao limite, "Atenção" (âmbar) quando está entre 80% e 100% do limite, "Acima" (vermelho) quando ultrapassa o limite.
- **R2** — A linha com sinal mostra também o valor no formato "R$ gasto de R$ limite" e a porcentagem atingida.
- **R3** — Categoria sem limite definido não mostra sinal nem os valores de R2, só o que já mostrava na fatia 008.
- **R4** — Quando o filtro de período não é um mês fechado (intervalo de datas ou todo o período), nenhuma linha mostra sinal; o bloco mostra um aviso curto "Sinal só por mês" e as categorias continuam mostrando o total normalmente.
- **R5** — No topo do bloco "Por categoria", com o filtro em um mês fechado, o usuário vê um resumo "N categorias acima do limite", contando só as categorias com limite definido que estão no estado "Acima". Quando N é zero, o resumo não aparece.
- **R6** — Mudar o filtro de período atualiza sinal, valores e resumo junto com o resto do bloco, sem ação separada do usuário.
- **R7** — O sinal, os valores de R2 e a contagem de R5 são calculados no servidor, nunca no cliente nem por um modelo de IA.

## Fora de escopo

- Teto do mês inteiro, diferente do sinal por categoria (fatia 014).
- Notificação ou alerta fora da tela "Gastos".
- Sinal para período diferente de mês fechado (intervalo, todo o período): fica sem sinal, conforme R4.
- Editar o limite a partir da página "Gastos" (o limite se edita na página "Categorias", fatia 012).
- Histórico ou comparação do sinal entre meses.

## Pontos em aberto

- nenhum

Premissas registradas: (1) "mês fechado" é o mesmo filtro de mês único já usado no bloco de período (fatia 005), sem proporcionalização por dias corridos ou parciais — o limite é sempre mensal e comparado ao mês inteiro selecionado; (2) fora de um mês fechado o bloco não tenta prorratear o limite, por ser menos honesto que simplesmente não mostrar sinal.
