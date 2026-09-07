# Brief — 011-serie-duplicada-e-tolerancia-do-vencimento

**Integridade das séries de compromisso.** Quatro defeitos medidos, todos em
`app/commitments/`, todos com a mesma consequência: um número de comprometido em
que não se pode confiar, na véspera de o item `004` projetar saldo dia a dia em
cima dele. Dois deles contam dinheiro que não vai sair; um parte uma compra em
duas; o quarto marca como morto o que está no futuro.

Escrito no presente. Cada requisito é `RF-nn` e é o que passa a valer.

## Contexto

O item `003` entregou o motor de compromissos e a tela de Comprometido. O
validador cego da fase 3 mediu dois defeitos; a investigação deste item achou o
terceiro — que é a causa de boa parte do primeiro — e o quarto, que sozinho vale
R$ 4.266,18/mês.

O número de cabeçalho da tela muda de **−R$ 12.802,64** para **−R$ 8.026,79**.
Isso não é ajuste fino: de um gasto mensal médio de R$ 17.295, é a diferença
entre ler 74% do mês já vendido antes de ele começar e ler 46%.

Nada aqui é tela nova, coluna nova ou dependência nova. É o motor passando a
dizer a verdade.

## Requisitos

### Precedência entre parcelamento e recorrência

- **RF-01** — Uma chave de série cobrada como **parcelamento** dentro da janela
  de vida não gera linha recorrente, tendo ou não parcela a vencer. A precedência
  deixa de olhar `installments_left` e passa a olhar só a janela.
- **RF-02** — Depois da correção, as quatro chaves hoje duplicadas —
  `cp amigao macae`, `jim com`, `mercadolivre merca` e `mercadolivre prod` — têm
  linha de parcelamento e **nenhuma** linha recorrente.
- **RF-03** — As quatro linhas recorrentes fantasmas somam **R$ 368,61/mês**, e
  saem do comprometido.
- **RF-04** — Um parcelamento cobrado **fora** da janela de vida continua sem
  suprimir a recorrência de mesma chave: uma compra parcelada encerrada há seis
  meses não apaga uma assinatura viva hoje com o mesmo beneficiário.

### A série de parcelamento é a compra, não o valor exato da parcela

- **RF-05** — Ocorrências com o mesmo beneficiário e o mesmo número total de
  parcelas formam **uma** série enquanto o valor da parcela ficar dentro de uma
  tolerância relativa declarada no código como constante nomeada.
- **RF-06** — A tolerância é **2%**. Ela absorve os 24 grupos partidos por
  arredondamento, cujo desvio vai de 0,01% a 0,14%, e mantém separado o único
  caso legítimo da base — `htm neg cursos tre`, total 12, com parcelas de
  R$ 27,07 e R$ 49,60, desvio de 45,4%, que são duas compras distintas na mesma
  loja.
- **RF-07** — A base de 05/09/2026 tem **66** pares `(beneficiário, total de
  parcelas)`, e a tolerância os resolve em **74** séries de parcelamento, contra
  as 96 de hoje. As oito separações que sobram são compras distintas na mesma
  loja, com valores de parcela que diferem entre 4,2% e 75,8%.
- **RF-08** — A série passa a ter `last_installment` igual à maior parcela vista
  da compra inteira, e `installments_left` calculado sobre ela. As séries
  fantasmas com `restam 5` de uma compra já quitada deixam de existir.
- **RF-09** — O valor da parcela da série é o valor da **última** ocorrência
  vista, não o da primeira: é ele que vai sair da conta nas parcelas que faltam.

### O lançamento substitui a previsão que ele realiza

- **RF-10** — O calendário casa lançamento com previsão por **distância entre
  datas**, não por mês do calendário. Um lançamento realiza a previsão da mesma
  série cuja data prevista está mais próxima, desde que a distância não passe da
  tolerância.
- **RF-11** — A tolerância é de **10 dias**. Ela absorve 90,3% da distância
  observada entre uma cobrança e o dia que a própria série prevê, e é curta o
  bastante para que uma cobrança do dia 5 não engula o vencimento previsto para o
  dia 25 — os 20 dias que separam os dois são o caso que este requisito existe
  para impedir.
- **RF-12** — Cada previsão é realizada por **no máximo um** lançamento. Dois
  lançamentos da mesma série dentro da tolerância aparecem os dois, e a previsão
  some uma vez só.
- **RF-13** — A distância é medida entre datas completas e por isso atravessa a
  virada do mês: uma série que prevê o dia 29 e é cobrada no dia 1º do mês
  seguinte tem distância de 2 ou 3 dias, não de 28. Sem isso, `ebn
  spotifycuritibabra` — mediana no dia 29, uma cobrança no dia 1º — seria lida
  como dois eventos.
- **RF-14** — Uma previsão não realizada por lançamento nenhum permanece no
  calendário. O defeito que este item corrige é a previsão que some, não a que
  fica.
- **RF-15** — `jim com` continua aparecendo uma vez só em setembro:
  `08/09/2026 · já lançado na conta · −R$ 136,43`, sem previsão no dia 6. Uma
  parcela já lançada com data futura entra no calendário mesmo quando a série não
  deve mais nada: o dinheiro sai da conta de qualquer jeito.

### Vivo é o que ainda vai sair da conta

- **RF-22** — A janela de vida é um **piso de data**: viva é a série cuja última
  cobrança não é anterior ao primeiro dia do mês anterior ao de referência. Ela
  deixa de ser um conjunto de dois rótulos de mês.
- **RF-23** — Cobrança com data **futura** conta como viva. Fatura de cartão
  chega com parcela lançada meses adiante, e são **15** as séries de parcelamento
  nessa situação, que a regra antiga marcava como paradas.
- **RF-24** — O total comprometido soma apenas séries **vivas**. Assinatura que
  parou de ser cobrada continua listada na tela, marcada, e fora do total: são
  **25** séries somando **R$ 2.739,97/mês** que hoje inflam o número de
  cabeçalho.
- **RF-25** — Com os quatro defeitos corrigidos, a base de 05/09/2026 devolve
  **−R$ 8.026,79** de comprometido, **R$ 233,76/mês** de caixa liberado pelos
  parcelamentos, **16** assinaturas vivas, **5** parcelamentos vivos e **115**
  linhas gravadas em `commitments` — 74 de parcelamento e 41 recorrentes.

### O que não pode quebrar

- **RF-16** — A janela de vida continua alcançando um mês para trás, e continua
  sendo ela que separa compromisso vivo de série morta.
- **RF-17** — A janela do calendário continua sendo de **45 dias**, e continua
  saindo de `app/commitments/calendar.py`.
- **RF-18** — A ação "não uso mais" continua reversível e continua devolvendo
  exatamente **R$ 1.099,63/mês** de economia projetada quando as três assinaturas
  do exemplo são marcadas.
- **RF-19** — Nenhum número medido nesta base aparece como literal no código de
  produção. Continua valendo o que o `003` já cobrava.
- **RF-20** — `recompute` continua idempotente e continua rodando numa transação
  só, e continua reaplicando as dispensas ao fim.

### Reconciliação de documento

- **RF-21** — `00-discovery.md` e `01-brief.md` do `003` afirmam o produto no
  presente, e passam a trazer os números corrigidos, com âncora de uma linha para
  este item.
- **RF-26** — `03-plan.md` do `003` **não** é reescrito. Os seus critérios são o
  registro do que cada fase foi medida contra, e os veredictos citam a saída
  daqueles comandos: reescrevê-los tornaria os veredictos inverificáveis. Ele
  ganha uma nota única no topo, dizendo que os números que os seus critérios
  cobram eram os corretos quando foram medidos e que este item os mudou.
- **RF-27** — `docs/plano.md` não muda, byte a byte: ele não afirma nada sobre
  séries de compromisso, que são construção deste projeto e não do relatório de
  origem.
