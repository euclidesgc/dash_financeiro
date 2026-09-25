# PRD 030 — shared-categories-query

## Valor

A lista de gastos e a tela de categorias pedem a mesma lista de categorias à API, cada uma com a sua cópia do pedido e do formato da resposta, e as duas guardam o resultado no mesmo lugar do cache. Se uma cópia mudar (o endereço, o formato ou o nome da chave), a outra segue lendo o cache com a suposição antiga, e a tela que usa a cópia desatualizada mostra categorias erradas ou some com elas sem que nenhum teste acuse. Com um pedido só, uma mudança vale para as duas telas.

## Usuários

Quem mantém o painel, ao mudar a lista de categorias, o formato dela ou quando ela é atualizada depois de uma troca.

## Requisitos

- **R1** — A lista de categorias é pedida à API por um único pedido compartilhado, usado pela lista de gastos e pela tela de categorias.
- **R2** — O formato de uma categoria, como a API devolve, é descrito uma vez só.
- **R3** — Toda atualização da lista de categorias depois de criar, renomear, apagar, definir limite ou trocar a categoria de um gasto aponta para a mesma chave do pedido compartilhado.
- **R4** — As duas telas se comportam como hoje; nenhum teste deixa de verificar o que verifica, e nenhum é pulado ou afrouxado.

## Fora de escopo

- Mudar o que a API devolve em `GET /api/categories`.
- Mudar a aparência ou o comportamento das telas.

## Pontos em aberto

- nenhum
