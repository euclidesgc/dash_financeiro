# Brief — 033-semear-taxonomia-deixa-o-banco-coerente

**Trilha:** rápida · **Este documento funde discovery, PRD e spec.**

## Problema

Semear a taxonomia deixa o banco pela metade, e só um segundo comando o completa.

Dois achados do validador do item `023`, medidos:

- **`seed_taxonomy` só conserta parte.** Ela reescreve o grupo dos lançamentos que
  apontavam para grupo que sumiu. O lançamento cujo grupo sobreviveu mas cuja
  **regra** mudou de grupo fica desatualizado até a classificação seguinte — **14
  de 87** no cenário que o validador montou.
- **A migração `012_taxonomy_tree.sql` derruba e recria `categories` na subida.**
  Na base do dono isso apaga as categorias já registradas. É dado derivado, que a
  classificação repõe — mas só se ela rodar.

Hoje nada quebra porque a linha de comando encadeia semeadura e classificação. O
defeito aparece para quem roda a semeadura isolada, que é exatamente o que alguém
faz ao depurar. **Um comando que deixa o banco incoerente e sai com sucesso é a
mesma classe de defeito que o item `012` fechou na sincronização:** sucesso
mentiroso.

## Escopo

Semear a taxonomia deixa o banco coerente sozinho — ou recusa terminar dizendo o
que falta.

## Requisitos

- **RF-01.** Depois da semeadura, nenhum lançamento fica com grupo divergente da
  regra que o classifica.
- **RF-02.** A semeadura isolada não pode sair com sucesso deixando o banco
  incoerente. Ou ela completa, ou ela recusa e diz o que falta rodar.
- **RF-03.** O encadeamento atual da linha de comando continua funcionando, e não
  passa a fazer o trabalho duas vezes.
- **RF-04.** Nenhum total de dinheiro muda com esta entrega.

## Riscos

- **Acoplar semeadura e classificação a ponto de não se poder mais semear sem
  reclassificar tudo.** RF-03 mede o custo: o caminho normal não pode ficar mais
  lento nem repetir trabalho.
