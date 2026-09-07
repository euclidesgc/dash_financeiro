# Discovery — 003-comprometido

**Item do roadmap:** `003-comprometido` — O que já está comprometido e quando sai
da conta: assinatura recorrente com valor médio, meses seguidos e ação "não uso
mais"; parcelamento com data de término e quanto de caixa ele libera ao acabar; e
o calendário de vencimentos.

**Data:** 2026-09-06

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim | Depende só do `001` e do `002`, ambos concluídos: o banco tem os 1.942 lançamentos classificados nos três eixos. |
| Negociável | sim | Fixo: as três superfícies (assinatura, parcelamento, calendário) e a ação "não uso mais". Conversável: como a próxima data é prevista, qual a janela que mata uma série, como o caixa liberado é apresentado. |
| Valioso | sim | É o item que responde "quanto do meu mês já está vendido antes de começar", e é dele que sai o insumo datado da projeção de 45 dias do `004`. |
| Estimável | sim | Três fases: motor de compromissos · tela de Comprometido · calendário. |
| Pequeno | sim | Nenhuma fase toca mais de duas famílias de prova, e nenhuma depende de terceiro. |
| Testável | sim | Todo número se compara com o que a base de 05/09/2026 tem, medido por consulta. |

**Veredicto do INVEST:** segue como está.

## História

Como dono deste painel, quero ver o que já está comprometido antes de o mês
começar — o que se repete todo mês, o que ainda tem parcelas a vencer e em que
dia cada coisa sai da conta — para saber quanto do salário já está vendido e o
que posso cancelar com um clique.

## Regras e exemplos

### R1 — Recorrente é o que se repete, e a tela diz há quanto tempo

- **E1.1** — A base traz **41 séries recorrentes**, das quais **16 estão vivas**
  — cobradas no mês corrente ou no anterior, ou com cobrança já datada adiante —,
  somando **R$ 7.793,03/mês** de valor médio. A maior é `DEBITO PRESTACAO HAB`,
  com média de **R$ 2.467,20** em 9 meses observados, 4 deles consecutivos,
  última cobrança em 08/2026.
- **E1.2** — Cada linha mostra valor médio, quantos meses seguidos apareceu e a
  data da última cobrança. Sem os meses seguidos, uma cobrança que parou há meio
  ano parece um compromisso vivo.

### R2 — Quem decide o que é cancelável é o dono, não o código

- **E2.1** — As três assinaturas que o relatório de origem soma como
  canceláveis — `ANTHROPIC* CLAUDE` R$ 581,68, `Pagamento de boleto MYCON`
  R$ 408,95 e TotalPass R$ 109,00 — somam **R$ 1.099,63/mês**. Esse recorte é
  **julgamento**, não categoria: escola, condomínio e financiamento também são
  recorrentes e não se cortam com um clique.
- **E2.2** — Marcar "não uso mais" numa linha tira o valor do comprometido e o
  soma na economia projetada, na hora, sem reiniciar o processo. Marcar as três
  do exemplo devolve exatamente **R$ 1.099,63/mês**.
- **E2.3** — A marca é reversível: desmarcar devolve a linha ao comprometido.

### R3 — Parcelamento morto não é compromisso

- **E3.1** — A base tem **66 compras parceladas** distintas, que a tolerância de
  valor resolve em **74 séries**. Contando ingenuamente `total − maior parcela
  vista`, **8** teriam parcelas a vencer. Com a janela de vida, sobram **5**,
  somando **R$ 233,76/mês** de caixa preso.
- **E3.2** — `IPVA parcela 1 de 3`, visto pela última vez em 26/01/2026, tem
  `restantes = 2` pela conta ingênua e **não** aparece como compromisso: as duas
  parcelas ou já foram pagas sob outra descrição, ou a série morreu. Um
  compromisso que não existe mais inflando o total é pior que não ter a tela.
- **E3.3** — `MERCADOLIVRE*MERCADOLIVRE` de R$ 127,27, parcela 2 de 24, vista em
  11/08/2026, aparece com **22 parcelas restantes** e data de término prevista
  para **06/2028**.

### R4 — Parcelamento tem fim, e o fim é dinheiro de volta

- **E4.1** — Cada parcelamento vivo mostra a data prevista de término e quanto
  de caixa mensal ele devolve ao acabar. Os cinco vivos somados devolvem
  **R$ 233,76/mês**, escalonados em três marcos: R$ 68,72 em 12/2026, R$ 37,77
  em 12/2027 e R$ 127,27 em 06/2028.
- **E4.2** — A tela ordena por quanto falta pagar, não por valor de parcela: o
  que decide é o total ainda comprometido.

### R5 — O calendário diz o dia, e declara que é previsão

- **E5.1** — O dia de cobrança é previsto pela **mediana** dos dias observados,
  porque a base mostra que ele varia: `debito prestacao hab` caiu nos dias
  6, 16, 17, 18, 19, 28 e 31 ao longo de nove meses.
- **E5.2** — A tela declara, em texto, que a data é prevista a partir do
  histórico e não é data contratual. Número que parece exato e não é destrói a
  confiança no resto.
- **E5.3** — O calendário cobre os próximos 45 dias, a mesma janela da projeção
  do item `004`, e soma quanto sai em cada dia.

### R6 — O comprometido não inventa dinheiro

- **E6.1** — Transferência entre contas próprias, pagamento de fatura e estorno
  não viram compromisso — as mesmas exclusões que o `001` marcou e o `002` usa.
- **E6.2** — Um lançamento que é ao mesmo tempo recorrente e parcelado entra uma
  vez só no total, como parcelamento, porque parcelamento tem fim e recorrência
  não.

> Os números desta seção são os do item `011`, que corrigiu quatro defeitos do
> motor de compromissos: a série que acabava e ressuscitava como assinatura, a
> compra partida em duas por um centavo de arredondamento, a previsão apagada
> pelo mês inteiro e o total que somava assinatura parada. O comprometido da base
> de 05/09/2026 é **−R$ 8.026,79**.

## Perguntas em aberto

Nenhuma.

Três dúvidas apareceram, todas técnicas, todas registradas em
`decisoes-autonomas.md`: a janela que mata uma série, a mediana como previsão de
dia, e a precedência entre recorrente e parcelado. A única pergunta que seria do
dono — *o que você considera cancelável?* — é justamente o que a ação "não uso
mais" transforma em mecanismo do produto, como o `002` fez com a classificação.

## Trilha

**Trilha: rápida.**

| Gatilho | Verdadeiro | Evidência |
|---|---|---|
| Zero perguntas em aberto | sim | Nenhuma sobrou. |
| Uma stack só | sim | Python 3.12 servindo HTML por Jinja2 e fragmentos HTMX. |
| Sem mudança de contrato | sim | Não há OpenAPI versionado nem consumidor externo. |
| Sem dependência nova | sim | Tudo que o item precisa já está no `pyproject.toml`. |

Os quatro gatilhos são verdadeiros, e a decisão do dono para este item, tomada
antes da corrida, também é a trilha rápida.
