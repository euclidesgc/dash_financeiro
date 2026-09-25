# PRD 031 — expense-count-label

## Valor

O painel escreve contagens como "1 gasto" e "3 gastos" em vários lugares: o rodapé da paginação, a coluna de quantidade do total por categoria, a oferta de aplicar a categoria a gastos parecidos e o uso de cada categoria na tela de categorias. Cada lugar decide o singular e o plural do seu jeito. Se a regra mudar num deles (o jeito de escrever o número, o caso do zero), os outros continuam com a antiga, e a mesma contagem aparece escrita de formas diferentes em telas vizinhas. Com uma regra só, a mudança vale para todos.

## Usuários

Quem mantém o painel, ao mudar como uma quantidade é escrita na tela.

## Requisitos

- **R1** — Toda contagem com singular e plural na interface ("gasto", "gasto parecido", "lançamento", "entrada", "categoria acima do limite") é escrita por uma regra única de singular e plural.
- **R2** — O que o usuário lê não muda: 1 fica no singular; 0 e 2 ou mais ficam no plural; "Nenhum gasto" continua aparecendo na tela de categorias quando a categoria não tem uso.
- **R3** — A API simulada dos testes escreve a mensagem de categoria em uso pela mesma regra.
- **R4** — Nenhum teste deixa de verificar o que verifica, e nenhum é pulado ou afrouxado.

## Fora de escopo

- As mensagens escritas pela API em Python (`app/routers/categories.py`).
- Mudar o texto de qualquer tela.

## Pontos em aberto

- nenhum
