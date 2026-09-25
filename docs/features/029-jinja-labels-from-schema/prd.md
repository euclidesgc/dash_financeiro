# PRD 029 — jinja-labels-from-schema

## Valor

Quando o dono renomeia uma categoria ou cria uma nova na tela de categorias, o nome que ele escolheu vale em todo o painel. Hoje as telas antigas de gastos por eixo e de regras continuam mostrando o nome de fábrica (ou só a chave crua, para a categoria criada), porque leem os nomes uma vez só, quando o servidor sobe. O painel mostra dois nomes para a mesma categoria.

## Usuários

O único usuário do painel, dono das contas, depois de renomear ou criar uma categoria e abrir a tela de gastos por eixo ou a tela de regras.

## Requisitos

- **R1** — Na tela de gastos por eixo (tabela, painel dos cruzamentos e lista aberta de uma linha), uma categoria renomeada aparece com o nome novo, sem reiniciar o servidor.
- **R2** — Na tela de regras (lista de regras e categorias sem regra), uma categoria renomeada aparece com o nome novo, sem reiniciar o servidor.
- **R3** — Uma categoria criada pelo dono aparece nas duas telas com o nome que ele deu, e não só com a chave.
- **R4** — Categoria que não está cadastrada continua aparecendo pela chave, uma vez só, como hoje.

## Fora de escopo

- Migrar as telas antigas para a nova interface.
- Mudar a tela de categorias ou a forma de renomear.

## Pontos em aberto

- nenhum
