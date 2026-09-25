# PRD 034 — override-unnecessary-reclassify

## Valor

Marcar um lançamento como "não é gasto" (transferência entre contas próprias, estorno, outro) e desfazer a marcação hoje refazem a classificação de todos os lançamentos da base, embora a marcação não mude nada do que a classificação decide (grupo, natureza, essencialidade). O custo cresce com a base inteira a cada clique. Sem a reclassificação, a marcação grava só o motivo e responde no mesmo tempo, qualquer que seja o tamanho da base.

## Usuários

Quem usa a tela de gastos para tirar dos totais o que não é gasto; e quem mantém o painel, que passa a ler na função de marcação só o que ela faz.

## Requisitos

- **R1** — Marcar e desmarcar um lançamento como "não é gasto" grava só o motivo; a classificação dos lançamentos não é refeita.
- **R2** — Trocar a categoria de um lançamento, voltar à categoria automática e aplicar a categoria a lançamentos parecidos continuam refazendo a classificação.
- **R3** — O que a tela mostra e o que a API responde não mudam; as recusas (lançamento desconhecido, lançamento que não conta como gasto nem entrada) continuam iguais.
- **R4** — Nenhum teste deixa de verificar o que verifica, e nenhum é pulado ou afrouxado.

## Fora de escopo

- A reclassificação feita pelas regras de classificação (`app/taxonomy/rules.py`), que muda o que a classificação lê.
- Tornar a reclassificação incremental.

## Pontos em aberto

- nenhum
