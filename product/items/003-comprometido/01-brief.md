# Brief — O que já está comprometido

**Item:** `003-comprometido` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado e validador cego valem igual. Se uma
> divergência for aprovada durante a execução, o item é promovido para a trilha
> completa e o `doc-reconciler` desdobra este arquivo em `01-prd.md` e
> `02-spec.md`.


> Os números deste brief são os do item `011`, que corrigiu quatro defeitos do
> motor de compromissos: a série que acabava e ressuscitava como assinatura, a
> compra partida em duas por um centavo de arredondamento, a previsão apagada
> pelo mês inteiro e o total que somava assinatura parada. O comprometido da base
> de 05/09/2026 é **−R$ 8.026,79**.

## Problema

O dono deste painel tem um déficit de R$ 4.940,72/mês e um comprometimento fixo
de R$ 6.563,57/mês — 58% da renda. Os itens `001` e `002` respondem o que ele
gastou; nenhum responde **quanto do mês seguinte já está vendido antes de o mês
começar**. Sem esse número, cortar assinatura vira palpite e o dia 10 chega com
uma cobrança que ninguém esperava.

A base sabe a resposta e não a diz. Ela tem 41 séries que se repetem há três ou
mais meses e 74 séries parceladas, vindas de 66 compras — e a conta ingênua diz que
32 ainda têm parcela a vencer, quando só 6 têm. `IPVA parcela 1 de 3`, visto
pela última vez em 26/01/2026, "deve" duas parcelas que não vão sair de conta
nenhuma. Um comprometido inflado por 26 séries mortas é pior que não ter a tela:
ele faz o dono cortar onde não precisava e desistir de um plano que estava certo.

  Medido: o `parcelamentos.json` conta 100, e quatro delas não têm nenhum
  lançamento de gasto — três são parcelamento de fatura, marcado `is_transfer`,
  e uma é compra estornada. O filtro de gasto do item `002`, que a invariante 25
  manda aplicar, as exclui, e por isso o motor detecta **96**.

E o dia também não é conhecido. `debito prestacao hab` caiu nos dias 6, 16, 17,
18, 19, 28 e 31 ao longo de nove meses: quem espera pelo dia 6 fica no vermelho
no dia 18.

## Escopo

Depois deste item existe uma tela de **Comprometido** que responde três coisas.

As **assinaturas** que se repetem, cada uma com valor médio, quantos meses
seguidos apareceu e a data da última cobrança — os meses seguidos são o que
separa um compromisso vivo de uma cobrança que parou há meio ano. Cada linha traz
a ação **"não uso mais"**, que tira o valor do comprometido e o soma na economia
projetada na hora, e que se desfaz do mesmo jeito. O que é cancelável é
julgamento do dono, não categoria no código: as três assinaturas que o relatório
de origem trata assim somam R$ 1.099,63/mês, enquanto as categorias de serviço
somam R$ 2.245,69/mês.

Os **parcelamentos vivos**, com parcelas restantes, mês de término e quanto de
caixa mensal cada um devolve ao acabar — R$ 233,76/mês no total, dos quais
R$ 68,72 já em 12/2026.

O **calendário dos próximos 45 dias**, com o dia previsto de cada vencimento e a
soma do que sai em cada dia, declarando em texto que a data é previsão a partir
do histórico.

Por baixo dos três está o motor de compromissos, que deriva tudo das transações
**no banco** e grava em `commitments` — a mesma tabela que a projeção do item
`004` vai somar.

## Não-escopo

- **A projeção de saldo dia a dia e a tela de Resumo não entram.** É o item
  `004`, que consome os `commitments` datados que este item cria. A ordem é essa
  porque projetar sem compromisso datado projeta só o passado.
- **A escada de dívidas e os simuladores não entram.** É o item `005`. Um
  parcelamento aqui é caixa preso com data de fim; dívida com taxa é outro
  assunto e outra ordenação.
- **Sincronização com a Pluggy não entra.** É o item `006`. A base é a que o
  `001` carregou de arquivo em disco; nada nesta tela dispara rede.
- **Objetivo com data e linha do tempo não entram.** É o item `007`. Aqui não há
  alvo a bater, só compromisso a enxergar.
- **Simulador e `plan_facts` não entram.** É o item `008`. A pergunta "quantos
  dias esta assinatura me custa" depende da linha do tempo que ainda não existe.
- **IA não entra.** É o item `009`. Detecção de recorrência e cálculo de término
  são função determinística testada (invariante 23); o modelo explica, não conta.
- **Negociação de taxa e previsão de reajuste não entram.** O valor previsto é a
  média observada. Prever reajuste exigiria índice externo e data de aniversário
  de contrato, que a base não tem — inventá-los daria um número exato e errado.
- **Cancelar a assinatura no fornecedor não entra.** A marca "não uso mais" é
  decisão registrada no painel; cancelar de fato exige credencial de terceiro,
  que este produto não guarda.
- **Criar ou editar compromisso à mão não entra.** Toda série vem do banco. Uma
  linha digitada seria uma segunda fonte de verdade sobre o mesmo dinheiro, e o
  total da tela deixaria de ser explicável pelas transações.

## Requisitos

### Tabela e disciplina do motor

- **RF-01** — O sistema deve criar por migração numerada nova a tabela
  `commitments`, sem editar migração já aplicada, com espaço para o tipo da série
  (recorrente ou parcelada), a chave da série, a descrição observada, a conta, o
  valor em centavos, os meses observados, os meses consecutivos, a data da última
  ocorrência, o dia previsto de cobrança, a última parcela vista, o total de
  parcelas, as parcelas restantes, o mês previsto de término e a marca do dono.
  *(ubíquo)*
- **RF-02** — O sistema deve derivar toda série de compromisso das linhas de
  `transactions`: nenhum módulo de `app/` lê `data/processed/recorrentes.json`
  nem `data/processed/parcelamentos.json`. *(ubíquo)*
- **RF-03** — O sistema deve receber a data de referência como parâmetro da
  detecção e do calendário, com a data corrente como padrão, de modo que a mesma
  base produza o mesmo resultado em qualquer dia em que a verificação rode.
  *(ubíquo)*
- **RF-04** — O sistema deve considerar apenas lançamentos de saída
  (`amount_cents` negativo) com `is_transfer = 0`, `is_refund = 0` e
  `refunded_by IS NULL`, deixando de fora as 152 linhas de transferência entre
  contas próprias e as 9 de estorno que o `001` marcou. *(ubíquo)*
- **RF-05** — O sistema deve identificar a série pela descrição normalizada com o
  marcador de parcela `n/N` removido, de modo que `OTICA BARDASSON E 10/10` caia
  na chave `otica bardasson e`, junto com as demais parcelas da mesma compra.
  *(ubíquo)*
- **RF-06** — Quando a detecção roda uma segunda vez sobre a mesma base e a mesma
  data de referência, o sistema deve manter a contagem de linhas de `commitments`
  inalterada. *(dirigido a evento)*
- **RF-07** — Quando a detecção roda de novo, o sistema deve preservar a marca
  "não uso mais" de cada série que já a tinha. *(dirigido a evento)*
- **RF-08** — Se a detecção falha no meio, então o sistema deve desfazer a
  operação inteira e manter `commitments` como estava, sem deixar parte das
  séries atualizada. *(comportamento indesejado)*

### Recorrência

- **RF-09** — O sistema deve classificar como recorrente a série observada em
  três ou mais meses distintos, produzindo sobre a base de 05/09/2026 as 55
  séries que `data/processed/recorrentes.json` registra, somando R$ 7.793,03/mês
  de valor médio. *(ubíquo)*
  A detecção que produz esse número aplica três cortes, e os três são parte do
  requisito: ao menos três meses distintos, ao menos três meses **consecutivos**,
  e desvio relativo máximo de 0,35 em torno da média.
- **RF-10** — O sistema deve gravar em cada série recorrente o valor médio, os
  meses observados, os meses consecutivos e a data da última cobrança:
  `DEBITO PRESTACAO HAB` tem valor médio R$ 2.467,20, 9 meses observados, 4
  consecutivos e última cobrança em 08/2026, e é a maior das 55. *(ubíquo)*
- **RF-11** — O sistema deve somar R$ 2.245,69/mês nas séries recorrentes de
  categorias de serviço sem tratar nenhuma delas como cancelável: a diferença
  para os R$ 1.099,63/mês de RF-24 é julgamento do dono, e não sai de categoria
  nenhuma. *(ubíquo)*

### Parcelamento

- **RF-12** — O sistema deve detectar série parcelada a partir de
  `installment_current` e `installment_total` e do padrão `n/N` na descrição,
  produzindo sobre a base de 05/09/2026 as 74 séries parceladas que
  `data/processed/parcelamentos.json` registra. *(ubíquo)*
- **RF-13** — O sistema deve tratar como compromisso vivo apenas a série
  parcelada cuja última parcela vista caiu no mês da data de referência ou no mês
  anterior ou datada adiante, de modo que das 74 restem 5, somando R$ 233,76/mês.
  *(ubíquo)*
- **RF-14** — O sistema deve calcular as parcelas restantes como o total de
  parcelas menos a última parcela vista, e o mês de término como o mês da última
  parcela vista somado às parcelas restantes: `MERCADOLIVRE*MERCADOLIVRE` de
  R$ 127,27, parcela 2 de 24, vista em 11/08/2026, tem 22 restantes e término
  previsto em 06/2028. *(ubíquo)*
- **RF-15** — O sistema deve registrar, para cada parcelamento vivo, o mês em que
  o caixa mensal volta a ficar livre e quanto volta: `Assai 232 Macae`, parcela 1
  de 24 de R$ 127,27 vista em 11/08/2026, termina em 06/2028 e devolve
  R$ 127,27/mês. *(ubíquo)*
- **RF-16** — Se a última parcela vista de uma série caiu antes do mês anterior à
  data de referência, então o sistema deve deixá-la fora do comprometido mesmo
  com parcelas restantes pela conta ingênua: `IPVA parcela 1 de 3`, visto em
  26/01/2026, tem duas restantes e não aparece em lugar nenhum da tela.
  *(comportamento indesejado)*
- **RF-17** — Se uma série é ao mesmo tempo recorrente e parcelada, então o
  sistema deve contá-la uma vez só, como parcelamento, e nenhuma chave de série
  aparece nas duas listas. *(comportamento indesejado)*
  A precedência vale contra o parcelamento **vivo** — o que a janela de vida
  deixou em pé —, não contra as 74 séries parceladas detectadas. Medido: a precedência
  vale para toda chave cobrada como parcelamento dentro da janela, tenha ou não parcela
  a vencer. Aplicá-la contra as séries mortas derrubaria `RF-09` sem que um único real deixasse
  de sair da conta; o que a regra existe para impedir é contar duas vezes o
  dinheiro que **vai** sair.

### Previsão de dia e calendário

- **RF-18** — O sistema deve prever o dia de cobrança de cada série pela mediana
  dos dias do mês em que ela foi observada, e o dia previsto é sempre um dia
  observado: `debito prestacao hab` foi observado nos dias 6, 16, 17, 18, 19, 28
  e 31 ao longo de nove meses. *(ubíquo)*
- **RF-19** — Se o número de ocorrências observadas é par, então o sistema deve
  tomar como mediana o menor dos dois dias centrais, para que o dia previsto
  continue sendo um dia que a série realmente teve. *(comportamento indesejado)*
- **RF-20** — Se o dia previsto não existe no mês de destino, então o sistema deve
  lançar a previsão no último dia daquele mês: dia previsto 31 vence em 30 de
  novembro. *(comportamento indesejado)*
- **RF-21** — O sistema deve devolver o calendário dos 45 dias seguintes à data de
  referência — de 05/09/2026 a 20/10/2026 na base medida —, com uma entrada por
  vencimento previsto e a soma do que sai em cada dia. *(ubíquo)*
- **RF-22** — O sistema deve incluir no calendário apenas séries vivas: recorrente
  com última cobrança no mês da data de referência ou no anterior, e parcelamento
  que passou pela janela de RF-13; a tela diz quantas das 41 recorrentes ficaram
  de fora e por quê. *(ubíquo)*
- **RF-23** — Se uma ocorrência da série já está lançada em `transactions` com
  data dentro dos 45 dias, então o sistema deve usar o lançamento existente e não
  somar também a previsão, para o mesmo dinheiro não aparecer duas vezes no
  mesmo dia. *(comportamento indesejado)*

### A marca "não uso mais"

- **RF-24** — Quando o dono marca "não uso mais" numa assinatura, o sistema deve
  tirar o valor médio dela do total comprometido e somá-lo na economia projetada,
  na resposta da mesma requisição e sem reiniciar o processo: marcar
  `ANTHROPIC* CLAUDE SUBSAN FRANCISCOUSA` R$ 581,68, `Pagamento de boleto MYCON`
  R$ 408,95 e `TOTALPASSSAO PAULOBRA` R$ 109,00 leva a economia projetada a
  R$ 1.099,63/mês. *(dirigido a evento)*
- **RF-25** — Quando o dono desmarca uma assinatura, o sistema deve devolvê-la ao
  total comprometido e tirar o valor dela da economia projetada, na resposta da
  mesma requisição. *(dirigido a evento)*
- **RF-26** — O sistema deve derivar "cancelável" apenas da marca gravada na linha
  de `commitments`: nenhum módulo de `app/` traz nome de categoria, nome de grupo
  ou descrição de assinatura como literal para decidir o que se corta.
  *(ubíquo)*
- **RF-27** — Se a marca "não uso mais" é pedida numa linha de parcelamento, então
  o sistema deve recusá-la com mensagem dizendo que parcelamento contratado não
  para com um clique, e o total comprometido permanece igual ao centavo.
  *(comportamento indesejado)*
- **RF-28** — Enquanto ao menos uma assinatura está marcada como "não uso mais", a
  tela deve exibir bloco próprio com essas linhas e com a economia projetada que
  elas somam. *(dirigido a estado)*
- **RF-29** — O sistema deve declarar em texto, no bloco da marca, que "não uso
  mais" registra a decisão no painel e não cancela nada no fornecedor.
  *(ubíquo)*

### Tela de Comprometido

- **RF-30** — Quando `GET /comprometido` chega com sessão válida, o sistema deve
  responder 200 com os três blocos — assinaturas, parcelamentos e calendário —,
  o total comprometido do mês e a economia projetada. *(dirigido a evento)*
- **RF-31** — O sistema deve listar as assinaturas ordenadas do maior valor médio
  para o menor, cada linha com valor médio, meses seguidos, última cobrança e a
  ação "não uso mais", com `DEBITO PRESTACAO HAB` (R$ 2.467,20) na primeira
  posição das 55. *(ubíquo)*
- **RF-32** — O sistema deve listar os parcelamentos vivos ordenados por quanto
  falta pagar, do maior para o menor, cada linha com valor da parcela, parcelas
  restantes, mês de término e caixa mensal devolvido — a ordenação é pelo total
  ainda comprometido, não pelo valor da parcela. *(ubíquo)*
- **RF-33** — O sistema deve exibir o cronograma de caixa liberado, com quanto
  volta em cada mês conforme as séries terminam: R$ 68,72 em 12/2026 e
  R$ 233,76/mês quando os cinco parcelamentos vivos acabarem. *(ubíquo)*
- **RF-34** — O sistema deve declarar em texto, no bloco do calendário, que a data
  de cada vencimento é previsão a partir do histórico e não data contratual.
  *(ubíquo)*
- **RF-35** — Enquanto a última cobrança de uma assinatura é anterior ao mês
  anterior à data de referência, a tela deve marcá-la como sem cobrança recente,
  para que uma série que parou não passe por compromisso vivo. *(dirigido a
  estado)*
- **RF-36** — Se um dos blocos da tela fica sem linha, então a tela deve mostrar
  estado vazio que diz o que aconteceu e qual é o próximo ato, nunca uma tabela
  ou um calendário sem linhas. *(comportamento indesejado)*
- **RF-37** — O sistema deve derivar do banco, em tempo de consulta, todo total e
  toda contagem que a tela mostra: nenhum arquivo de `app/` traz 55, 100, 6,
  R$ 7.793,03, R$ 233,76, R$ 2.245,69, R$ 1.099,63, R$ 2.467,20 ou R$ 127,27
  como literal. Esses números vivem nos testes, que medem o banco carregado a
  partir da fonte de 05/09/2026. *(ubíquo)*

### Interface

- **RF-38** — O sistema deve renderizar a tela de Comprometido com os tokens
  declarados em `product/00-linguagem-visual.md` e definidos em
  `app/static/css/tokens.css`, nos dois temas, com `tabular-nums` em toda cifra e
  o sinal `−` colado ao valor negativo; nenhum template deste item traz cor em
  hexadecimal, `rgb()` ou `hsl()`. *(ubíquo)*
- **RF-39** — O sistema deve renderizar a tela em 375, 768 e 1440 px sem rolagem
  horizontal do corpo, com a captura de cada largura em `06-capturas/`.
  *(ubíquo)*
- **RF-40** — Enquanto um elemento interativo da tela tem o foco do teclado, o
  sistema deve desenhar um contorno visível de ao menos 2 px em volta dele.
  *(dirigido a estado)*
- **RF-41** — Enquanto o navegador declara `prefers-reduced-motion: reduce`, o
  sistema deve entregar a tela sem animação e sem transição, com o estado final
  preservado. *(dirigido a estado)*

## Métrica de sucesso

| Métrica | Onde se observa | Alvo |
|---|---|---|
| O comprometido do mês passa a ter um número derivado do banco | consulta a `data/dash.sqlite`, data de referência 05/09/2026 | 16 assinaturas vivas somando R$ 7.793,03/mês e 5 parcelamentos somando R$ 233,76/mês |
| Parcelamento morto não infla o total | consulta a `data/dash.sqlite`, data de referência 05/09/2026 | das 74 séries parceladas detectadas, 5 entram no comprometido; `IPVA parcela 1 de 3` não entra |
| A economia projetada da alavanca de curto prazo ganha fonte | tela de Comprometido, com as três assinaturas marcadas | R$ 1.099,63/mês, o mesmo número que `docs/plano.md` usa no horizonte de 0–3 meses |

## Restrições herdadas

Da norma do projeto (`CLAUDE.md`), de `docs/plano.md` e dos itens `001` e `002`:

- **Valor em centavos inteiros, negativo = dinheiro saindo** (invariante 22). O
  motor soma `amount_cents`; formatação em reais é da apresentação.
- **Transferência entre contas próprias e estorno não entram** (invariante 25).
  As flags já existem desde o `001` — 152 linhas `is_transfer = 1` e 9
  `is_refund = 1` — e este item as consome sem recalcular heurística (RF-04).
- **O que só o humano sabe é parâmetro editável na tela, nunca constante no
  código** (invariante 26). Aqui isso é o recorte de cancelável: ele é marca em
  `commitments` (RF-26), não categoria.
- **Cálculo financeiro é código determinístico, nunca IA** (invariante 23).
  Detecção, mediana, término e caixa liberado são função testada.
- **Login antes de qualquer rota que devolva dado** (invariante 24). A guarda do
  `001` já cobre a rota deste item: página sem sessão responde 302 para `/login`
  (RF-26 do `001`), rota `/api/*` responde 401 sem valor de conta no corpo
  (RF-27 do `001`). Nada disso se reescreve aqui, e rota JSON que este item
  venha a expor usa o prefixo `/api/`.
- **Antes de escrever a tela, carregar a skill `frontend-design`** (invariante
  27), e `product/00-linguagem-visual.md` é o canônico de interface. A folha de
  estilo viaja dentro do documento renderizado: o projeto não monta diretório
  estático, e `app/static/css/tokens.css` segue sendo a fonte única dos valores.
- **Números congelados em 05/09/2026** (invariante 28). Eles vivem em requisito e
  em teste, medindo o banco carregado da fonte daquela data; um número dentro do
  código de produção faria a consulta do mês seguinte falhar por estar certa
  (RF-37).
- **Sem dependência não declarada** (15), **zero comentário exceto o porquê que o
  código não mostra** (11), **sem TODO** (12), **código em inglês, documentos e
  interface em pt-BR** (16).

Das decisões autônomas deste item (`decisoes-autonomas.md`), que este brief
assume e não reabre: **D1** — janela de vida de um mês para parcelamento
(RF-13, RF-16); **D2** — mediana dos dias observados como previsão, declarada
como previsão na tela (RF-18, RF-34); **D3** — série recorrente e parcelada conta
como parcelamento (RF-17); **D4** — cancelável é marca do dono, não categoria
(RF-11, RF-26); **D5** — o motor detecta do banco, não dos JSONs de
`data/processed/`, que ficam como referência de conferência (RF-02, RF-09,
RF-12).

## Interseção entre recorrência e parcelamento — medida

A interseção é **vazia**: nenhum dos 5 parcelamentos vivos aparece entre as 41
séries recorrentes, medido comparando a descrição normalizada de cada
parcelamento vivo com a chave de cada recorrente. Logo `RF-09` (R$ 7.793,03/mês
em 16 séries vivas) e `RF-13` (R$ 233,76/mês em 5 parcelamentos) somam sem dupla
contagem nesta base, e a regra de precedência de `D3` continua valendo por
construção, para a base que crescer.

## Riscos

- **Os recorrentes e os parcelamentos foram medidos em passadas separadas.**
  Se alguma chave de série aparecer nas duas listas, RF-17 manda contá-la como
  parcelamento e o total de recorrentes cai abaixo de R$ 7.793,03. Resposta: a
  verificação mede a interseção antes de comparar os dois totais; se ela não for
  vazia, o número de RF-09 é reconciliado por divergência, não ajustado em
  silêncio.
- **A janela de vida de um mês mata série real que pula um mês** — cobrança anual
  ou fatura atrasada. É o custo aceito em D1, e ele é assimétrico de propósito:
  26 séries mortas inflando o comprometido enganam mais que uma série ausente.
  Resposta: a lista de assinaturas não usa a janela, e RF-22 faz o calendário
  declarar quantas ficaram de fora.
- **A base já traz lançamento com data futura** — `OTICA BARDASSON E 10/10` tem
  ocorrência em 02/2027, porque fatura de cartão chega parcelada adiante.
  Resposta: RF-23 usa o lançamento existente no lugar da previsão dentro dos 45
  dias, de modo que o dia nunca soma o mesmo dinheiro duas vezes.
- **A mediana erra o dia.** `debito prestacao hab` variou entre o dia 6 e o dia
  31. Resposta: RF-34 declara na tela que a data é previsão do histórico, e a
  decisão contra o dia da última ocorrência está registrada em D2 — a última
  ocorrência herdaria o mês atípico inteiro.
- **Os números medidos envelhecem no primeiro sync do item `006`.** Resposta:
  RF-37 mantém todo total fora do código de produção; a verificação mede o banco
  carregado da fonte de 05/09/2026, e é a fonte que fixa o número.
- **A tela nova não tem revisor de norma de código para Python.** É o atalho
  declarado em `docs/plano.md`. Resposta: `frontend-design` e
  `product/00-linguagem-visual.md` cobrem o lado da interface, e RF-38 a RF-41
  são verificáveis por teste e por captura, não por opinião.
