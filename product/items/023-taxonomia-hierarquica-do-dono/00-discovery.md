# Discovery — 023-taxonomia-hierarquica-do-dono

**Item do roadmap:** `023-taxonomia-hierarquica-do-dono` — a classificação primária é
uma árvore de duas alturas que pertence ao dono: grupo, e dentro dele categoria.

**Data:** 2026-09-07 · **Trilha declarada:** rápida

## O terreno, lido no código

Hoje **não há hierarquia nenhuma**. `categories`
(`app/migrations/sql/003_taxonomy.sql:20-23`) tem `id` e `name`, sem chave estrangeira
para grupo, e é preenchida por `app/taxonomy/classify.py:_record_categories` com os
nomes crus que a fonte manda — os 77 rótulos traduzidos em `app/taxonomy/seed.json`,
na seção `category_labels`, consumida em `app/routers/spending.py:33` e
`app/routers/rules.py:25` só para exibir.

`category_groups` são dez etiquetas paralelas, aplicadas por regra. As 80 regras de
`seed.json` atribuem grupo, natureza e essencialidade de uma vez; 76 casam por categoria
crua e 4 por expressão sobre o beneficiário. Grupo e categoria são dois campos lado a
lado nos cinco eixos de `app/queries/axes.json`, não pai e filho.

É essa forma que faz o vocabulário parecer preso à vida de outra pessoa: ele foi copiado
de uma base, não desenhado.

## Regra, exemplo e pergunta

- **Regra.** Cada categoria pertence a um grupo, e o par é do dono.
- **Regra.** Nenhum total de gasto muda: a mesma transação continua sendo a mesma
  transação, classificada por outro caminho.
- **Regra.** Existe grupo que guarda transferência entre contas próprias e estorno, e
  ele existe porque sem ele o painel mente em R$ 20.272,00 (norma 25).
- **Exemplo.** "Financiamento imobiliário" deixa de ser um rótulo solto e passa a ser
  categoria dentro de **Moradia**; "Combustível" passa a ser categoria dentro de
  **Transporte**.
- **Pergunta em aberto:** nenhuma de produto.

## Os quatro gatilhos de trilha completa

| Gatilho | Resposta |
|---|---|
| Mexe em contrato público ou OpenAPI? | Não. |
| Toca autenticação, autorização ou dado pessoal? | Não. |
| Tem mais de uma frente de stack? | Não. |
| Requisito ambíguo que exija spec formal? | Não, mas o item tem invariante numérica dura, e é ela que os critérios medem. |

**Trilha rápida.**

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| Onde a árvore mora? | **`categories` ganha o grupo a que pertence e o rótulo em português.** A chave continua sendo o nome cru, que é o que a transação carrega. | Tabela nova obrigaria a reescrever a junção de todos os eixos e a migrar o que as transações já apontam, para guardar a mesma informação. |
| `category_groups` é substituída? | **Não. É reescrita**, com os grupos do dono. A tabela e a chave estrangeira de `transactions` ficam onde estão. | Tabela nova quebraria `app/queries/axes.py:43`, os cinco eixos e toda a tela de regras, sem mudar nada do que o item pede. |
| A regra deixa de atribuir grupo, já que a categoria agora tem um? | **Não.** A regra continua atribuindo grupo, natureza e essencialidade de uma vez, e nenhum deles aceita nulo. | Derivar o grupo da categoria dentro do classificador tiraria do dono a capacidade de dizer "este beneficiário é Transporte mesmo que a fonte chame de Compras" — que é o que as 4 regras por expressão fazem hoje. |
| E se a árvore e as regras discordarem? | **Teste.** Toda regra que casa por categoria atribui o grupo a que aquela categoria pertence na árvore. Discordância é defeito de semente, e falha no portão. | Deixar discordar cria duas verdades sobre o mesmo lançamento, e a que vence passa a ser a ordem de execução. |
| O grupo de escape continua existindo? | **Sim, `Outros`.** Classificação sem escape não tem onde pôr o que nenhuma regra pegou. | Removê-lo faria o classificador falhar em vez de classificar, e é o item `019` que encolhe os 244 lançamentos que hoje caem lá. |
| Os cinco eixos mudam de nome ou de número? | **Não.** `grupo` passa a mostrar os grupos do dono e `categoria` continua sendo a categoria; o que muda é o vocabulário, não a forma da tela. | Mexer nos eixos junto misturaria a árvore com a tela de `019`. |
| `category_labels` continua existindo? | **Não como seção separada.** O rótulo passa a ser campo da categoria na árvore — uma casa só para o nome em português. | Duas casas para o mesmo rótulo é a repetição que o `015` já pagou uma vez. |
