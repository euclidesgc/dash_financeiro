# Brief — 038-conta-e-instituicao-como-eixo

**Item:** `038-conta-e-instituicao-como-eixo` · **Trilha:** rápida

**Depende de:** `037` fase 1, que cria a tabela de conexões `pluggy_items` e grava
em `accounts.item_id` a conexão de cada conta (migração 019). Este item lê as duas
e não altera o esquema delas.

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

**O painel não diz de que banco veio um gasto.** A lista de lançamentos de
`/gastos` mostra a conta pelo nome que a Pluggy manda, e para cartão esse nome é o
do cartão: "platinum" é o cartão do Nubank, e o "Passai Visa Gold" está na conexão
do Itaú. O campo de instituição da Pluggy não ajuda: para cartão ele repete o nome
do cartão, e o conector das cinco conexões se chama "MeuPluggy".

Somar também não dá. Os cinco eixos de `/gastos` — grupo, categoria, beneficiário,
natureza e essencialidade — não têm banco nem conta. Saber quanto o cartão do
Nubank pesa no mês exige saber de cor que "platinum" é o Nubank, e mesmo assim não
há linha que some o gasto dele. A base tem 12 contas em 5 conexões.

## Escopo

Cada conexão da Pluggy é uma instituição — C6, Mercado Pago, Nubank, CAIXA e
Itaú —, e cada uma das 12 contas é da instituição da sua conexão. O dono dá nome à
instituição e apelido à conta em `/configuracao`, e a sincronização nunca os toca.
Em `/gastos`, todo lançamento listado diz de que instituição e de que conta veio, e
os eixos instituição e conta somam o gasto do período por banco e por conta; abrir
uma linha deles lista os lançamentos daquela instituição ou daquela conta. Os sete
eixos repartem o mesmo total. Na seção de cartões de `/configuracao`, o banco de
cada cartão é o nome da instituição.

## Não-escopo

- **O esquema da conexão é do `037`.** `pluggy_items` e `accounts.item_id` nascem e
  se preenchem na fase 1 dele; este item só os lê. Redefini-los aqui daria duas
  casas para a mesma informação.
- **O dono não muda uma conta de instituição.** O vínculo é a conexão da Pluggy, e
  é isso que o item fixa: o dono muda nomes, não vínculos.
- **Não há tela nova para os nomes.** Eles se editam em `/configuracao`, onde o
  `015` juntou o que só o dono sabe; uma tela própria para dois campos por conta
  espalharia isso de novo.
- **A tela com todos os lançamentos — entradas e saídas, saldo de cada conta,
  filtro por banco e conta combinado com os outros — é o `041`.** Aqui a leitura é
  de gasto, e filtrar por instituição ou conta é abrir a linha do eixo.
- **Transferência entre contas próprias e estorno continuam fora.** Os eixos novos
  somam com o mesmo predicado de gasto dos outros cinco: um Pix do Itaú para o
  Nubank não é gasto de nenhuma das duas contas.
- **Os nomes do dono aparecem em `/gastos`, na lista de instituições e contas de
  `/configuracao` e, como banco de cada cartão, na seção de cartões (RF-19).** A
  escada de dívida, a fatura e os compromissos continuam com o nome que a Pluggy
  manda: o pedido é a origem do lançamento e o eixo de gasto, essas telas leem a
  conta por caminhos próprios, e trocar o rótulo delas é escopo que o dono não
  pediu.

## Requisitos

### Instituição

- **RF-01** — O sistema deve tratar cada conexão da Pluggy como uma instituição, e
  cada conta como da instituição da conexão gravada nela — as cinco conexões da
  base e qualquer uma que uma sincronização posterior traga. Na base do dono, o
  cartão "platinum" é da instituição da conexão `af3c4101`, a do Nubank, e o
  "Passai Visa Gold" é da instituição da conexão `f7d463e2`, a do Itaú. *(ubíquo)*
- **RF-02** — Enquanto o dono não deu nome a uma instituição, o sistema deve
  mostrá-la com o nome da conta de tipo `BANK` da conexão — havendo mais de uma, o
  da primeira por ordem de nome. A conexão `af3c4101`, com
  "Nu Pagamentos S.A. - Instituição de Pagamento" (`BANK`) e "platinum" (`CREDIT`),
  é a instituição "Nu Pagamentos S.A. - Instituição de Pagamento", com "platinum"
  sob ela. Na base do dono, os cinco nomes iniciais são "C6 BANK", "Mercado Pago",
  "Nu Pagamentos S.A. - Instituição de Pagamento", "CAIXA" e "itau".
  *(dirigido a estado)*
- **RF-03** — Se a conexão não tem conta de tipo `BANK`, então o sistema deve
  mostrar a instituição com o nome da primeira conta da conexão por ordem de nome.
  *(comportamento indesejado)*

### Nome e apelido

- **RF-04** — Quando o dono grava em `/configuracao` um nome para uma instituição,
  o sistema deve mostrar esse nome no lugar do nome inicial em `/gastos` e em
  `/configuracao`. O dono renomeia a instituição da conexão `af3c4101` para
  "Nubank". *(dirigido a evento)*
- **RF-05** — Quando o dono grava em `/configuracao` um apelido para uma conta, o
  sistema deve mostrar o apelido no lugar do nome vindo da Pluggy em `/gastos`. O
  dono dá à conta "platinum" o apelido "Cartão Nubank". *(dirigido a evento)*
- **RF-06** — Quando uma sincronização grava uma carga nova, inclusive a do mesmo
  bruto, o sistema deve manter todo nome de instituição e todo apelido de conta que
  o dono gravou. Depois de RF-04 e RF-05, uma nova carga do mesmo bruto mantém
  "Nubank" e "Cartão Nubank". *(dirigido a evento)*
- **RF-07** — Se o dono envia em branco o campo de nome de uma instituição ou de
  apelido de uma conta, então o sistema deve manter o valor guardado, sem gravar
  nada. *(comportamento indesejado)*
- **RF-08** — Quando o dono usa o botão de apagar do apelido de uma conta, o
  sistema deve apagar o apelido, e a conta volta a mostrar o nome vindo da Pluggy;
  quando usa o de apagar o nome de uma instituição, ela volta ao nome de RF-02 ou
  RF-03. *(dirigido a evento)*
- **RF-09** — Se o envio de `/configuracao` aponta para uma instituição ou uma
  conta que não existe na base, então o sistema deve recusá-lo com a tela de pé e
  mensagem em português, sem gravar e sem responder 500.
  *(comportamento indesejado)*
- **RF-10** — O sistema deve listar em `/configuracao` todas as instituições com as
  contas da conexão de cada uma, cada conta com o nome vindo da Pluggy e o apelido,
  quando houver; toda conta da base aparece ali para receber apelido, inclusive
  conta sem nenhum lançamento e conta sem conexão gravada. Na base do dono,
  "C6 BANK" e o cartão "Bandeirado", com zero lançamentos, aparecem ali.
  *(ubíquo)*
- **RF-11** — O sistema deve tratar nome de instituição e apelido de conta como
  camada de leitura: gravar, trocar ou apagar um deles não muda nenhum total,
  nenhuma contagem e nenhuma classificação. *(ubíquo)*

### Eixos e lançamentos

- **RF-12** — O sistema deve oferecer em `/gastos` o eixo instituição, com uma
  linha por instituição com gasto no período, rotulada pelo nome do dono ou, sem
  ele, pelo nome de RF-02 ou RF-03. *(ubíquo)*
- **RF-13** — O sistema deve oferecer em `/gastos` o eixo conta, com uma linha por
  conta com gasto no período, rotulada pelo apelido ou, sem ele, pelo nome vindo da
  Pluggy; duas contas de mesmo nome são duas linhas. Na base do dono, o cartão Itaú
  Black ("Itau Uniclass Mastercard Black") e o cartão Itaú Múltiplo
  ("Itau Uniclass Multiplo Mastercard Platinum+") aparecem em linhas separadas,
  cada um com o apelido do dono quando houver, e a corrente e a poupança da CAIXA,
  as duas chamadas "CAIXA" pela Pluggy, também, sempre que as duas têm gasto no
  período. *(ubíquo)*
- **RF-14** — Enquanto uma instituição ou uma conta não tem gasto no período, o
  sistema deve deixá-la fora do eixo correspondente. Na base do dono, "C6 BANK" e
  "Bandeirado" não aparecem no eixo conta, e a instituição da conexão `71349dd7`,
  que só tem as duas, não aparece no eixo instituição. *(dirigido a estado)*
- **RF-15** — O sistema deve repartir o mesmo total e a mesma contagem de
  lançamentos nos sete eixos de `/gastos` — grupo, categoria, beneficiário,
  natureza, essencialidade, instituição e conta —, em qualquer período. Em agosto
  de 2026, a soma das linhas do eixo instituição é igual ao total de gasto do
  período e igual à soma do eixo grupo. *(ubíquo)*
- **RF-16** — Se a conta de um lançamento não tem conexão gravada, ou não está na
  base, então o sistema deve somá-lo mesmo assim: no eixo instituição, na linha
  "sem valor", que é como os outros eixos mostram a chave vazia, e no eixo conta,
  na linha da conta dele. Nenhum lançamento sai de nenhum dos sete eixos.
  *(comportamento indesejado)*
- **RF-17** — Quando o dono abre uma linha do eixo instituição ou do eixo conta, o
  sistema deve listar só os lançamentos de gasto daquela instituição ou daquela
  conta no período, e a soma da lista é o valor da linha. *(dirigido a evento)*
- **RF-18** — O sistema deve mostrar, em todo lançamento listado em `/gastos`, em
  qualquer eixo, a instituição e a conta de onde ele veio, pelo nome do dono quando
  houver. Uma compra no cartão "platinum" aparece como da instituição
  "Nu Pagamentos S.A. - Instituição de Pagamento" e da conta "platinum"; depois de
  RF-04 e RF-05, como da instituição "Nubank" e da conta "Cartão Nubank".
  *(ubíquo)*

### Seção de cartões

- **RF-19** — O sistema deve mostrar, como banco de cada cartão na seção de cartões
  de `/configuracao`, o nome da instituição da conexão do cartão — o dado pelo dono
  ou, sem ele, o de RF-02 ou RF-03. O cartão "platinum" aparece sob
  "Nu Pagamentos S.A. - Instituição de Pagamento"; depois que o dono renomeia a
  instituição para "Nubank", aparece sob "Nubank". Se a conta do cartão não tem
  conexão gravada, então o sistema deve mostrar como banco o campo de instituição
  da Pluggy, `accounts.institution`: sem conexão não há instituição a nomear.
  Enquanto a conta do "platinum" não tem conexão gravada, ele aparece sob
  "platinum". *(ubíquo; o caso sem conexão, comportamento indesejado)*

## Métrica de sucesso

| Métrica | Onde se observa | Alvo |
|---|---|---|
| Gasto sem instituição | Linha "sem valor" do eixo instituição em `/gastos`, em qualquer período | Nenhum lançamento, a partir da primeira sincronização depois da entrega |
| Nome do dono desfeito por sincronização | Nomes e apelidos em `/configuracao`, antes e depois de cada sincronização | Zero nos 30 dias seguintes à entrega |

## Riscos

- **O nome do dono ao alcance da carga.** Coluna em `accounts` é reescrita pelo
  upsert de toda carga — o defeito que separou `cards` de `accounts` na migração
  013. Resposta: nome de instituição e apelido de conta moram em tabelas próprias,
  `institution_names` e `account_nicknames`, e RF-06 se verifica com uma carga nova
  do mesmo bruto.
- **O campo de instituição da Pluggy parece o banco e não é.** Para cartão ele
  repete o nome do cartão ("platinum", "Itau Uniclass Mastercard Black",
  "Passai Visa Gold"), na conta do Nubank ele termina em "(Conta Pré-paga)", e o
  conector das cinco conexões é "MeuPluggy". Resposta: o nome inicial sai do nome
  da conta `BANK` da conexão (RF-02), e nenhuma leitura deste item usa o nome do
  conector nem usa `accounts.institution` para nomear instituição; o único uso do
  campo é o banco do cartão sem conexão gravada (RF-19). A verificação é
  estrutural.
- **A seção de cartões de `/configuracao` desmentindo a lista nova na mesma tela.**
  Com o campo de instituição da Pluggy, o cartão do Nubank aparece com o banco
  "platinum" ao lado da lista que o põe sob o Nubank. Resposta: a seção mostra o
  nome da instituição (RF-19). Descartado manter o campo da Pluggy até o `041`,
  porque a contradição ficaria visível na tela do próprio item que existe para
  corrigi-la. Descartado levar os nomes também à escada de dívida, à fatura e aos
  compromissos, porque são mais quatro leituras da conta, cada uma por caminho
  próprio, e a fase cresceria por um rótulo que o dono não pediu.
- **Conta sem conexão gravada.** `accounts.item_id` só se preenche quando a carga da
  fase 1 do `037` roda, e uma junção que exija o par conta–conexão tira o
  lançamento do eixo em silêncio. Resposta: RF-15 e RF-16 cobram os sete eixos com o
  mesmo total, e a primeira métrica acompanha a linha "sem valor" até zerar.
- **Duas contas com o mesmo nome.** A corrente e a poupança da CAIXA chegam as duas
  como "CAIXA". Resposta: o eixo conta separa por conta, não por nome (RF-13), e o
  apelido é o que as distingue na leitura.
