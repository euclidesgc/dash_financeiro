# Brief — 023-taxonomia-hierarquica-do-dono

**Item:** `023-taxonomia-hierarquica-do-dono` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

O vocabulário com que este painel classifica gasto não é do dono. Ele foi copiado da
fonte: `categories` guarda os 77 nomes crus que a Pluggy manda
(`app/taxonomy/classify.py:_record_categories`), e `category_groups` são dez etiquetas
paralelas aplicadas por regra. **Não há hierarquia**: `categories` tem `id` e `name`, e
nenhuma chave estrangeira para grupo (`app/migrations/sql/003_taxonomy.sql:20-23`).

Grupo e categoria são dois campos lado a lado nos cinco eixos, não pai e filho. O
resultado é que a tela responde "quanto gastei em Comer fora e lazer" com um recorte que
ninguém desenhou, e "quanto gastei com a casa" não tem resposta — porque energia, água,
condomínio e financiamento estão espalhados por grupos diferentes.

Uma árvore de duas alturas que o dono reconhece é o que faz a pergunta seguinte —
"onde eu corto?" — ter resposta. Sem ela, o item `019`, que deixa o dono corrigir
classificação a partir do lançamento, seria construído sobre o vocabulário plano de hoje
e teria de ser construído duas vezes.

## Escopo

A classificação primária passa a ser uma árvore de duas alturas do dono: grupo, e dentro
dele categoria. Cada categoria sabe a que grupo pertence e tem nome em português numa
casa só. As regras existentes são remapeadas para os grupos novos. **Nenhum total de
gasto muda.**

Os grupos são: Moradia, Transporte, Alimentação, Saúde, Educação, Assinaturas, Pessoal,
Financeiro, Dependentes, Renda, **Não é gasto** — que guarda transferência entre contas
próprias e estorno, e existe porque sem ele o painel mente em R$ 20.272,00 (norma 25) —
e o grupo de escape **Outros**, para o que nenhuma regra pegou.

## Não-escopo

- **A tela de correção a partir do lançamento é o item `019`.** Aqui o vocabulário muda;
  quem o edita a partir do gasto é o item seguinte.
- **Os cinco eixos não mudam de forma.** `grupo` e `categoria` continuam existindo e
  continuam se chamando assim.
- **O mecanismo que exclui transferência e estorno do gasto não muda.** Ele é por marca
  na transação (`app/taxonomy/classify.py:13`) e continua sendo; o grupo **Não é gasto**
  é vocabulário, não mecanismo.
- **Nenhuma regra nova é escrita para reduzir o escape.** Encolher `Outros` é o `019`.

## Requisitos

- **RF-01.** Cada categoria pertence a exatamente um grupo, e a relação é chave
  estrangeira, não convenção de nome.
- **RF-02.** Cada categoria tem um nome em português numa casa só. A seção
  `category_labels` da semente deixa de existir como lista paralela.
- **RF-03.** Os grupos são os do dono, na ordem em que ele os lê, com um grupo de escape
  marcado como tal e um grupo **Não é gasto**.
- **RF-04.** Toda regra existente aponta para um grupo que existe depois do remapeamento.
  Nenhuma regra fica órfã.
- **RF-05.** Toda regra que casa por categoria atribui o mesmo grupo a que aquela
  categoria pertence na árvore. Discordância entre árvore e regra falha o portão.
- **RF-06.** **Nenhum total muda.** Sobre a mesma base, antes e depois: o gasto total, o
  número de lançamentos considerados gasto, o cruzamento variável × supérfluo e o
  cruzamento fixa × essencial são idênticos, dígito a dígito.
- **RF-07.** Natureza e essencialidade de cada lançamento continuam as mesmas: a árvore
  muda o grupo e a categoria, e não toca nos outros dois eixos.
- **RF-08.** Uma categoria que a fonte mande e que a árvore não conheça continua sendo
  registrada e cai no grupo de escape, como hoje — a carga nunca quebra por vocabulário.

## Riscos

- **Mudar um total sem perceber.** É o risco central. RF-06 é medido por comparação da
  mesma base antes e depois, não por leitura.
- **O remapeamento perder uma regra.** RF-04 e RF-05 são o que se verifica, e os dois
  são estruturais: se alguma regra apontar para grupo inexistente, o portão acusa.
