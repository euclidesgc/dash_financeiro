# Spec — Sincronização real com a Pluggy

**Item:** `037-sincronizacao-real-com-a-pluggy` · **PRD:** `01-prd.md` (aprovado em
10/09/2026, `ecd6974`) · **Trilha:** completa

## 1. Escopo desta spec

Detalha o escopo inteiro do PRD aprovado, em três fases entregues nesta ordem, uma
por PR: **fase 1**, a carga entende o bruto (2.1 a 2.6); **fase 2**, o botão busca
na Pluggy (2.7 a 2.14); **fase 3**, o botão e o relógio (2.15 a 2.18). Cada exemplo
da discovery, de E1.1 a E13.3, aparece com os mesmos valores sob o requisito que
ilustra.

### 1.1 Termos

- **Hoje** — a data de referência do painel: `DASH_TODAY` quando definida, senão a
  data local.
- **Conexão** — um item da Pluggy, registrado em `pluggy_items`. As cinco conexões
  MeuPluggy do dono são C6, Mercado Pago, Nubank, CAIXA e Itaú.
- **Nome do banco** — o nome da conta corrente (`subtype` `CHECKING_ACCOUNT`) da
  conexão, como a Pluggy o manda; sem conta corrente, os nomes das contas dela,
  separados por vírgula. O nome do conector não serve, porque é "MeuPluggy" nas
  cinco. Na base do dono: "C6 BANK", "Mercado Pago", "Nu Pagamentos S.A. -
  Instituição de Pagamento", "CAIXA" e "itau".
- **Conexão em dia** — `GET /items/{id}` devolve `status` `UPDATED` e
  `executionStatus` `SUCCESS`. Qualquer outro valor — `PARTIAL_SUCCESS`,
  `UPDATING`, `LOGIN_ERROR`, `WAITING_USER_INPUT`, `USER_AUTHORIZATION_REVOKED` ou
  outro — deixa a conexão **fora do dia**.
- **Resposta inteira** de uma conta — todas as páginas de `GET /v2/transactions`
  daquela conta responderam 200 na execução.
- **Busca completa** — busca de uma conta sem `dateFrom`.
- **Janela** de uma conta — de `dateFrom` em diante, sem fim; na busca completa,
  tudo o que a Pluggy devolve.
- **Ausente** — lançamento da conta que estava na base antes da execução, datado
  dentro da janela e não antes de 12 meses antes de hoje, cujo `pluggy_id` não veio
  na resposta inteira.
- **Novo** — lançamento da resposta cujo `pluggy_id` não está na base.
- **Última busca bem-sucedida** de uma conta — o instante da última execução em que
  a conta teve resposta inteira, com a conexão em dia e sem remoção suspensa.
- **Marcas** — `is_transfer`, `transfer_reason`, `is_refund`, `refunded_by` e
  `is_cash_withdrawal`.
- **Consolidador** — `ingestao/pluggy_consolidate.py`, oráculo dos testes das
  marcas.

## 2. Requisitos funcionais

### Fase 1 — a carga entende o bruto

A carga recebe o bruto da Pluggy — conexões, contas, lançamentos e identidade, na
forma em que a API os devolve — e tira dele tudo o que grava.

#### 2.1 Valor e sinal

- **RF-01** — O sistema deve gravar o valor de cada lançamento em centavos inteiros
  de real, lido de `amountInAccountCurrency` quando esse campo vem preenchido e de
  `amount` quando não vem. *(ubíquo)*
  - *E3.1* — Compra no cartão "STRIPE Z.AI", `amount` 64.8, `currencyCode` USD,
    `amountInAccountCurrency` 350.57: grava **−35057** centavos.
- **RF-02** — O sistema deve gravar negativo o dinheiro que sai e positivo o que
  entra, em qualquer tipo de conta, invertendo uma vez, na carga, o sinal que a
  Pluggy dá aos lançamentos de conta `CREDIT`. *(ubíquo)*
  - *E3.2* — Compra no cartão, `amount` 120.00 BRL: −12000. Pagamento de fatura na
    conta de cartão, `amount` −2425.59: +242559.
- **RF-03** — Quando o bruto de 05/09/2026 do dono é carregado, o sistema deve
  deixar o gasto de dez/2025 a ago/2026 exatamente R$ 2.346,09 (234.609 centavos
  de saída) acima do gasto da mesma base carregada do arquivo consolidado, com a
  diferença inteira vinda das 14 compras em USD. *(dirigido a evento)*
  - *E3.3* — Na base do dono, as 14 compras em USD somam **R$ 2.346,09** a mais de
    gasto depois da carga; a medida vai declarada no PR da fase 1.
- **RF-04** — Se um lançamento do bruto vem sem `id`, sem `accountId`, sem `date`,
  ou com valor ausente, não numérico ou com fração de centavo, então o sistema deve
  recusar a carga inteira, gravar a execução como `failed` com quantos lançamentos
  foram recusados, e não gravar nenhum lançamento. *(comportamento indesejado)*

#### 2.2 O que a carga guarda

- **RF-05** — O sistema deve gravar em cada lançamento o estado (`status`,
  `PENDING` ou `POSTED`), a moeda (`currencyCode`), o meio de pagamento
  (`paymentData.paymentMethod`), o tipo de operação (`operationType`), o código de
  ramo do estabelecimento (`creditCardMetadata.payeeMCC`), a fatura
  (`creditCardMetadata.billId`) e a data da compra (os dez primeiros caracteres de
  `creditCardMetadata.purchaseDate`), deixando vazio o campo que a Pluggy não
  manda. *(ubíquo)*
- **RF-06** — O sistema deve guardar, para cada lançamento, o último registro
  original que a Pluggy devolveu para ele, preso ao número interno do lançamento.
  *(ubíquo)*
- **RF-07** — O sistema deve gravar cada conexão em `pluggy_items` — id, `status`,
  `executionStatus`, `lastUpdatedAt` e o registro original — e atualizar esses
  campos a cada leitura da conexão. *(ubíquo)*
- **RF-08** — O sistema deve gravar em cada conta o id da conexão a que ela
  pertence, lido do `itemId` da conta. *(ubíquo)*
  - Exemplo: a conta de cartão "platinum" fica com o id da conexão do Nubank.

#### 2.3 Contraparte

- **RF-09** — O sistema deve gravar como contraparte de um lançamento de saída, em
  conta que não é de cartão, o recebedor (`paymentData.receiver`): o nome em
  `counterparty_name`, o tipo do documento em `counterparty_kind` e o documento em
  `counterparty_document`. *(ubíquo)*
  - *E4.1* — Pix enviado da conta Itaú com `paymentData.receiver.documentNumber`
    CNPJ `14380200000121`: `counterparty_kind` = CNPJ, `counterparty_document` =
    `14380200000121`, nome = `receiver.name`.
- **RF-10** — O sistema deve gravar como contraparte de um lançamento de entrada,
  em conta que não é de cartão, o pagador (`paymentData.payer`), nos mesmos três
  campos. *(ubíquo)*
  - *E4.2* — Pix recebido com `payer.documentNumber` CPF: `counterparty_kind` =
    CPF, nome = `payer.name`.
- **RF-11** — O sistema deve gravar como contraparte de todo lançamento de conta de
  cartão o estabelecimento (`merchant`): nome de `merchant.name`, documento de
  `merchant.cnpj` com tipo CNPJ, e razão social de `merchant.businessName` em
  `merchant_legal_name`. *(ubíquo)*
  - *E4.3* — Compra no cartão com `merchant.cnpj`: a contraparte é o
    estabelecimento — nome, razão social e CNPJ do `merchant`.
- **RF-12** — O sistema deve gravar o documento da contraparte só com os dígitos.
  *(ubíquo)*
  - Exemplo: `documentNumber` `{"type": "CNPJ", "value": "14.380.200/0001-21"}`
    grava `14380200000121`.
- **RF-13** — Se o documento vem sem tipo CPF ou CNPJ, ou se a contraparte não vem,
  então o sistema deve deixar tipo e documento vazios e gravar o nome quando houver.
  *(comportamento indesejado)*
- **RF-14** — O sistema deve gravar nome, razão social e CNPJ do estabelecimento e o
  nome do recebedor em `merchant_name`, `merchant_legal_name`, `merchant_cnpj` e
  `receiver_name`, com vazio no lugar de texto em branco, porque as telas de
  beneficiário do item `015` leem essas colunas. *(ubíquo)*

#### 2.4 Marcas

- **RF-15** — Quando uma carga grava lançamentos, o sistema deve recalcular as
  marcas de todos os lançamentos da base, não só dos que a carga trouxe, depois de
  gravada a carga inteira. *(dirigido a evento)*
  - *E5.2* — Débito de −R$ 500,00 na conta Itaú em 03/09 já gravado; a carga
    seguinte traz crédito de +R$ 500,00 na conta Nubank (a conta corrente, não o
    cartão) em 05/09: os dois ficam `is_transfer = 1`, motivo `transferência entre
    contas próprias`.
- **RF-16** — Enquanto o CPF do dono não é conhecido, o sistema deve dar, para a
  mesma amostra, as mesmas tuplas (`pluggy_id`, `is_transfer`, `transfer_reason`,
  `is_refund`, `refunded_by`, `is_cash_withdrawal`) que o consolidador, elemento a
  elemento. *(dirigido a estado)*
  - *E5.1* — A mesma amostra processada por `app/sync/marks.py` e por
    `ingestao/pluggy_consolidate.py` dá as mesmas tuplas, elemento a elemento.
- **RF-17** — O sistema deve gravar, para a mesma amostra, data, descrição, tipo,
  categoria da Pluggy e parcela (`installment_current`, `installment_total`)
  iguais às do consolidador, e o valor igual exceto nas compras em moeda
  estrangeira (RF-01). *(ubíquo)*
  - Exemplo: `installmentNumber` 3 e `totalInstallments` 10 gravam a parcela 3 de
    10; sem esses campos, "3/10" na descrição dá o mesmo.
- **RF-18** — O sistema deve marcar `is_transfer = 1`, com motivo `transferência
  entre contas próprias (CPF do dono)`, o lançamento que nenhuma outra marca marcou
  e cuja contraparte tem o CPF do dono — o pagador num crédito, o recebedor num
  débito —, exceto o saque. O CPF do dono é o documento que a Pluggy devolve em
  `/identity`. *(ubíquo)*
  - *E5.3* — Crédito cujo pagador tem o CPF do dono é transferência própria mesmo
    sem o par na base. Na base do dono isso não move número: os 23 créditos pagos
    pelo CPF dele e os 23 débitos recebidos por ele já estão marcados.

#### 2.5 Categoria

- **RF-19** — O sistema deve gravar como categoria do lançamento a categoria da
  Pluggy, vazia quando a Pluggy não manda nenhuma e nunca inferida da descrição; o
  grupo desse lançamento é o que a classificação der, e "Outros" quando nenhuma
  regra casa. *(ubíquo)*
  - *E6.1* — Lançamento cuja categoria da Pluggy veio vazia: `category` fica vazia
    e o grupo sai da classificação. Na base do dono são 21 linhas e −R$ 233,98 que
    podem trocar de grupo; o gasto total não muda.

#### 2.6 Amostra de teste

- **RF-20** — A amostra de bruto usada nos testes não deve conter CPF, nome de
  pessoa física, número de conta ou de cartão, nem id da Pluggy da base do dono;
  CNPJ e nome de empresa podem ficar. *(ubíquo)*

### Fase 2 — o botão busca na Pluggy

#### 2.7 A busca

- **RF-21** — Quando a sincronização roda, o sistema deve buscar na Pluggy as contas
  e os lançamentos de cada conexão registrada em `pluggy_items` e gravar os novos,
  sem ler o arquivo consolidado (`data/processed/transacoes.json`). *(dirigido a
  evento)*
  - *E1.1* — Base com última busca bem-sucedida em 05/09/2026; a Pluggy tem 30
    lançamentos novos, de 06/09 a 10/09, espalhados nas 12 contas. Depois da
    sincronização a base tem 1.972 lançamentos e `sync_runs` registra 30
    inseridos.
- **RF-22** — Quando o dono roda `python -m app.sync`, o sistema deve executar a
  mesma sincronização do botão, na hora, imprimir o resultado numa linha e sair com
  0 em `ok` e 1 em falha ou recusa. *(dirigido a evento)*
- **RF-23** — Se `PLUGGY_CLIENT_ID` ou `PLUGGY_CLIENT_SECRET` falta no ambiente,
  então o sistema deve recusar a sincronização antes de qualquer chamada, com
  mensagem em português que nomeia a variável ausente, sem gravar nada — nem linha
  em `sync_runs` —, e o botão, numa requisição sem HTMX, deve responder 400 com a
  tela de Resumo e a mensagem. *(comportamento indesejado)*
  - *E1.2* — Sem `PLUGGY_CLIENT_ID` no ambiente: a tela responde 400 com a mensagem
    em português de credencial ausente, e nada é gravado.
- **RF-73** — Quando o sistema monta a lista de conexões — no começo de cada
  sincronização e de cada verificação da rotina —, o sistema deve registrar em
  `pluggy_items` todo id de `data/item_ids.txt` que ainda não está lá, e tomar como
  lista a união desse arquivo com as conexões já registradas. O arquivo é o que a
  ferramenta manual de extração grava ao criar uma conexão: um id por linha, com
  linhas em branco ignoradas. Sem o arquivo, valem só as conexões já registradas.
  *(dirigido a evento)*
  - Exemplo: `data/item_ids.txt` tem os cinco ids de hoje e ganha um sexto,
    `00000000-0000-4000-8000-000000000006`. A sincronização seguinte registra essa
    conexão em `pluggy_items`, chama
    `GET /items/00000000-0000-4000-8000-000000000006` e
    `GET /accounts?itemId=00000000-0000-4000-8000-000000000006`, grava as contas
    dela com esse `item_id`, e o banco dela aparece no Resumo como o dos outros.

#### 2.8 O cliente da Pluggy

- **RF-24** — O sistema deve falar com a Pluggy só por estas chamadas: `POST /auth`,
  `GET /items/{id}`, `GET /accounts`, `GET /v2/transactions`, `GET /bills`,
  `GET /identity` e `PATCH /items/{id}`. *(ubíquo)*
  - *E10.1* — O registro do transporte falso de uma sincronização completa só
    contém essas sete chamadas.
- **RF-25** — Se algum código pede ao cliente da Pluggy uma chamada fora dessa
  lista — outro método ou outro caminho —, então o cliente deve levantar erro antes
  de a requisição sair. *(comportamento indesejado)*
  - *E10.1* — Qualquer outro método ou caminho levanta erro antes de sair.
- **RF-26** — O sistema não deve pôr `PLUGGY_CLIENT_ID`, `PLUGGY_CLIENT_SECRET` nem
  a chave que `POST /auth` devolve em página, fragmento, log, mensagem de
  `sync_runs` ou texto de exceção. *(ubíquo)*
- **RF-27** — O sistema não deve pôr o CPF do dono nem documento de contraparte em
  log nem em mensagem de `sync_runs`. *(ubíquo)*
- **RF-28** — Se `POST /auth` responde algo diferente de 200, ou não responde,
  então o sistema deve gravar a execução como `failed`, com mensagem em português
  que diz que a Pluggy recusou as credenciais ou não respondeu, sem fazer outra
  chamada nem gravar lançamento. *(comportamento indesejado)*
- **RF-29** — Se a Pluggy responde 429, então o sistema não deve fazer nenhuma
  chamada à Pluggy antes de passado o intervalo que o cabeçalho `Retry-After`
  indica. *(comportamento indesejado)*
- **RF-30** — Se um teste tenta uma requisição de rede real por `httpx` — por
  qualquer função do módulo (`get`, `post`, `request`, `patch` e as demais) ou por
  uma instância de cliente sem transporte falso —, então a suíte deve falhar o
  teste com a mensagem "o teste tentou sair para a rede", antes de a requisição
  sair. *(comportamento indesejado)*
  - *E10.2* — Nenhum teste sai para a rede: `httpx.request` e `httpx.patch` também
    são bloqueados pelo fixture.

#### 2.9 A janela

- **RF-31** — Quando a sincronização busca uma conta que tem última busca
  bem-sucedida, o sistema deve pedir `GET /v2/transactions` com `accountId`,
  `dateFrom` igual ao menor entre hoje − 60 dias e a última busca bem-sucedida − 7
  dias, e sem `dateTo`. *(dirigido a evento)*
  - *E2.1* — Hoje 10/09/2026, última busca da conta em 05/09/2026:
    `dateFrom = 2026-07-12`, sem `dateTo` — as 43 parcelas datadas depois de hoje
    continuam vindo.
- **RF-32** — Quando a sincronização busca uma conta sem última busca
  bem-sucedida, o sistema deve pedir `GET /v2/transactions` com `accountId`, sem
  `dateFrom` e sem `dateTo`. *(dirigido a evento)*
  - *E2.2* — Conta sem busca anterior: busca completa, sem `dateFrom`.
  - Na base do dono as 12 contas começam sem última busca: a primeira
    sincronização real é completa e não remove nada (RF-46).
- **RF-33** — O sistema deve pedir os lançamentos em páginas de 500 e seguir o
  cursor `next` da resposta até ele vir vazio. *(ubíquo)*
- **RF-34** — Quando a carga grava uma conta que teve resposta inteira, com a
  conexão em dia e sem remoção suspensa, o sistema deve gravar o instante da
  execução como a última busca bem-sucedida da conta, na mesma transação da carga.
  *(dirigido a evento)*

#### 2.10 Conexões, identidade e faturas

- **RF-35** — Se `GET /items/{id}` ou `GET /accounts` de uma conexão não responde
  200, então o sistema deve seguir com as outras conexões e não gravar nenhum
  lançamento daquela conexão na execução. *(comportamento indesejado)*
- **RF-36** — Se alguma página de `GET /v2/transactions` de uma conta não responde
  200, então o sistema não deve inserir, religar nem remover nenhum lançamento
  daquela conta na execução. *(comportamento indesejado)*
- **RF-37** — Se nenhuma conta tem resposta inteira na execução — inclusive quando
  não há conexão registrada —, então o sistema deve gravar a execução como
  `failed`, com mensagem em português que diz que nenhum banco pôde ser buscado.
  *(comportamento indesejado)*
- **RF-38** — Quando a sincronização busca uma conexão, o sistema deve ler
  `GET /identity` dela e guardar o documento devolvido, só com dígitos, como CPF do
  dono. *(dirigido a evento)*
- **RF-39** — Quando a sincronização busca uma conta de cartão (`CREDIT`), o
  sistema deve ler `GET /bills` dela e gravar cada fatura em `card_bills`: id,
  conta, vencimento (`dueDate`, como data), valor total em centavos com o sinal
  invertido — a fatura a pagar fica negativa, como o saldo do cartão —, moeda
  (`totalAmountCurrencyCode`) e o registro original. *(dirigido a evento)*
- **RF-40** — Se `GET /identity` ou `GET /bills` falha, então o sistema deve seguir
  a sincronização sem rebaixá-la, mantendo o CPF do dono e as faturas já guardados.
  *(comportamento indesejado)*

#### 2.11 Religação

- **RF-41** — Quando uma conta tem resposta inteira, o sistema deve religar cada
  ausente ao novo da mesma conta que forma com ele um par 1:1 pela chave — na
  parcela, a mesma data da compra, a mesma parcela, o mesmo total de parcelas e o
  mesmo valor; nos demais, o mesmo valor, data a até 5 dias e a mesma descrição
  normalizada por `normalize_description` —: a linha mantém o `transactions.id`,
  recebe o `pluggy_id` e os campos do novo, e não gera lápide. *(dirigido a evento)*
  - *E7.1* — Parcela PENDING `p-velho` (−R$ 50,00, 3/10, `purchase_date`
    2026-07-15) no cartão Itaú Black; a Pluggy a devolve como `p-novo` POSTED com o
    mesmo valor, parcela e data da compra: a base tem **uma** linha, o
    `transactions.id` é o mesmo, o `pluggy_id` passa a `p-novo`, e
    `transaction_removals` fica vazia.
- **RF-42** — Se um ausente tem mais de um novo candidato, ou um novo tem mais de um
  ausente candidato, então o sistema não deve religar nenhum deles: os ausentes
  seguem a regra de remoção e os novos entram como lançamentos novos.
  *(comportamento indesejado)*
  - *E7.2* — Duas compras de R$ 30,00 no mesmo dia, mesma descrição, somem e voltam
    com dois ids novos: o par é ambíguo, nenhuma religa; as duas antigas saem com
    lápide e as novas entram.

#### 2.12 Remoção e lápide

- **RF-43** — Quando uma conta buscada com `dateFrom` tem resposta inteira, a
  conexão dela está em dia e a trava não suspende, o sistema deve remover da base os
  ausentes que ficaram sem par e gravar, para cada um, uma lápide em
  `transaction_removals` com a linha removida inteira, o registro original, o id da
  execução e o instante. *(dirigido a evento)*
  - *E8.3* — Compra PENDING de R$ 89,90 cancelada pela Pluggy (some sem par), numa
    conta com 60 lançamentos na janela: sai da base e fica em
    `transaction_removals` com o bruto.
- **RF-44** — Se os ausentes sem par de uma conta são mais que max(5, 20% dos
  lançamentos da conta na janela), então o sistema não deve remover nenhum
  lançamento daquela conta na execução, e deve contá-la como remoção suspensa.
  *(comportamento indesejado)*
  - *E8.1* — Conta com 40 lançamentos na janela e resposta 200 vazia para ela:
    **nenhuma** linha some, e a tela diz que a remoção dessa conta foi suspensa
    (RF-51).
  - *E8.3* — A trava suspende só quando faltam mais que max(5, 20%) das linhas da
    janela: com 60 lançamentos, mais que 12.
- **RF-45** — Enquanto a conexão está fora do dia, o sistema não deve remover
  lançamento de nenhuma conta dela; os novos entram e a religação acontece.
  *(dirigido a estado)*
  - *E9.1* — O item do Itaú em `LOGIN_ERROR`: as quatro contas dele não sofrem
    remoção, as outras quatro conexões sincronizam, e a tela diz que o Itaú pede
    novo login em meu.pluggy.ai (RF-52).
- **RF-46** — O sistema não deve remover lançamento fora da janela: na busca
  completa, nenhum; na busca com `dateFrom`, nenhum datado antes dele ou antes de 12
  meses antes de hoje. *(ubíquo)*
  - *E8.2* — Lançamento datado de hoje − 200 dias, ausente da resposta: continua na
    base. A Pluggy guarda 12 meses; a base local guarda tudo.

#### 2.13 Escrita e registro da execução

- **RF-47** — O sistema deve fazer todas as chamadas à Pluggy antes de abrir a
  transação que grava a carga, e nenhuma chamada de rede dentro dela. *(ubíquo)*
  - *E13.3* — A rede roda fora da transação SQL.
- **RF-48** — Se a escrita da carga falha, então o sistema deve desfazê-la inteira —
  nenhum lançamento inserido, religado, removido ou remarcado, nenhuma lápide,
  nenhuma última busca atualizada — e gravar a execução como `failed`.
  *(comportamento indesejado)*
  - *E13.3* — Um erro na escrita desfaz a carga inteira e `sync_runs` grava
    `failed`; o "tudo ou nada" do `012` continua.
- **RF-49** — Quando a carga termina `ok`, o sistema deve rodar a pós-carga —
  classificação, compromissos e escada de dívida — e rebaixar a execução a `failed`
  se ela falha, como o item `012` definiu. *(dirigido a evento)*
- **RF-50** — Quando a execução termina, o sistema deve gravar em `sync_runs`, além
  de inseridos e contas: quantos lançamentos saíram com lápide
  (`removed_count`), quantos foram religados (`relinked_count`), quantos
  lançamentos que já estavam na base tiveram as marcas mudadas
  (`marks_changed_count`), quantas contas tiveram a remoção suspensa
  (`removal_suspended_count`), e quem abriu a execução em `source` (`botao`,
  `rotina` ou `comando`). *(dirigido a evento)*
  - *E5.4* — Uma marca que muda de uma sincronização para a outra (um par novo que
    troca o parceiro de um débito antigo) é contada em `sync_runs`.

#### 2.14 O que o Resumo diz da execução

- **RF-51** — Enquanto a última execução concluída suspendeu a remoção de uma conta,
  o sistema deve mostrar no Resumo o nome do banco e o da conta, e dizer que a
  remoção dela foi suspensa. *(dirigido a estado)*
  - *E8.1* — A tela diz que a remoção dessa conta foi suspensa.
- **RF-52** — Enquanto o `status` ou o `executionStatus` de uma conexão é
  `LOGIN_ERROR`, `WAITING_USER_INPUT` ou `USER_AUTHORIZATION_REVOKED`, o sistema
  deve mostrar no Resumo o nome do banco e dizer que ele pede novo login em
  meu.pluggy.ai. *(dirigido a estado)*
  - *E9.1* — A tela diz que o Itaú pede novo login em meu.pluggy.ai.
- **RF-53** — Enquanto uma conexão está fora do dia por outro estado, o sistema deve
  mostrar no Resumo o nome do banco, dizer que a remoção das contas dele foi
  suspensa porque a atualização da Pluggy não está completa, e mostrar o estado que
  a Pluggy informou. *(dirigido a estado)*
- **RF-54** — Se a busca de uma conexão falhou na última execução concluída, então o
  sistema deve mostrar no Resumo o nome do banco e dizer que a busca dele falhou
  nessa execução. *(comportamento indesejado)*
- **RF-55** — Enquanto a última execução concluída tem lançamentos removidos,
  religados ou com marcas mudadas, o sistema deve mostrar no Resumo quantos saíram
  com lápide, quantos foram religados e quantas marcas mudaram.
  *(dirigido a estado)*
  - *E5.4* — A marca que muda é contada, e a tela a mostra.

### Fase 3 — o botão e o relógio

#### 2.15 Uma execução por vez

- **RF-56** — Quando uma execução começa, o sistema deve gravar a linha dela em
  `sync_runs` com `status` `running`, e trocá-lo por `ok` ou `failed` quando ela
  termina. *(dirigido a evento)*
- **RF-57** — Enquanto uma execução está em andamento no painel, o sistema não deve
  iniciar outra, nem pelo botão nem pela rotina. *(dirigido a estado)*
- **RF-58** — Quando o dono aciona Sincronizar durante uma execução em andamento, o
  sistema deve responder sem iniciar outra e sem gravar linha nova em `sync_runs`,
  dizendo que já há uma sincronização em andamento. *(dirigido a evento)*
  - *E13.2* — O botão apertado durante a execução responde que já há uma
    sincronização em andamento.
- **RF-59** — Enquanto uma execução está em andamento, o sistema não deve lê-la no
  Resumo como falha nem como a última bem-sucedida: o Resumo mostra a última
  execução concluída e diz que há uma sincronização em andamento.
  *(dirigido a estado)*
- **RF-60** — Se o painel sobe e encontra execução com `status` `running`, então o
  sistema deve gravá-la como `failed` com a mensagem "interrompida antes de
  terminar". *(comportamento indesejado)*

#### 2.16 Pedido de atualização ao banco

- **RF-61** — Quando o dono aciona Sincronizar, pelo botão ou pelo comando, o
  sistema deve pedir atualização (`PATCH /items/{id}`) só às conexões que nunca
  receberam pedido ou cujo último pedido foi feito há uma hora ou mais, gravar o
  instante do pedido por conexão, e seguir para a busca na mesma execução, sem
  esperar a conexão sair de `UPDATING`. *(dirigido a evento)*
  - *E11.1* — Uma conexão com pedido feito há 30 minutos e outra há 2 horas: só a
    segunda recebe `PATCH`.
- **RF-62** — Se a Pluggy responde 409 ou outro erro ao pedido de atualização,
  então o sistema deve tratar como "ainda não": seguir a busca daquela conexão com o
  que a Pluggy tem, sem rebaixar a execução. *(comportamento indesejado)*
  - *E11.1* — Um 409 da Pluggy não rebaixa a execução.

#### 2.17 O botão e o estado

- **RF-63** — Quando o dono aciona Sincronizar sem HTMX, o sistema deve iniciar a
  execução fora da requisição e responder 303 para `/`. *(dirigido a evento)*
  - *E12.1* — `POST /sincronizar` sem HTMX responde 303 para `/`; recarregar a
    página depois disso não reenvia a sincronização.
- **RF-64** — Quando o dono aciona Sincronizar com HTMX (cabeçalho `HX-Request`), o
  sistema deve iniciar a execução fora da requisição e responder 200 com o
  fragmento que acompanha o andamento por `GET /sincronizar/estado`.
  *(dirigido a evento)*
  - *E12.1* — Com HTMX responde 200 com o fragmento que acompanha o andamento por
    `GET /sincronizar/estado`.
- **RF-65** — Quando `GET /sincronizar/estado` é chamado, o sistema deve responder
  200 com o fragmento do estado: enquanto há execução em andamento, o fragmento se
  pede de novo; quando ela termina, mostra o resultado — inseridos, removidos,
  religados, marcas mudadas e os avisos por banco de 2.14 — e para de se pedir.
  *(dirigido a evento)*
- **RF-66** — Se `GET /sincronizar/estado` chega sem sessão, então o sistema deve
  responder 302 para `/login`, sem devolver estado nenhum. *(comportamento
  indesejado)*
- **RF-67** — Se o dono aciona Sincronizar com HTMX e falta credencial da Pluggy,
  então o sistema deve responder 200 com o fragmento que traz a mensagem de
  credencial ausente, sem iniciar execução nem gravar nada, porque o HTMX não troca
  o conteúdo numa resposta 4xx. *(comportamento indesejado)*
- **RF-68** — O sistema deve mostrar no Resumo, por banco, "atualizado pela Pluggy
  em DD/MM/AAAA HH:MM", lido do `lastUpdatedAt` da conexão e convertido para o fuso
  local. *(ubíquo)*
  - *E12.2* — A tela mostra, por instituição, "atualizado pela Pluggy em
    10/09/2026 06:12", lido do `lastUpdatedAt` do item.

#### 2.18 A rotina

- **RF-69** — Enquanto `DASH_SYNC_AUTO` não está ligado (`1`, `true` ou `sim`, como
  `DASH_CNPJ_LOOKUP`), o sistema não deve criar a thread `dash-sync` ao subir o
  painel. *(dirigido a estado)*
  - *E13.1* — Sem `DASH_SYNC_AUTO`, subir o app não cria thread `dash-sync`.
- **RF-70** — Enquanto `DASH_SYNC_AUTO` está ligado, o sistema deve manter uma única
  thread `dash-sync`, que verifica as conexões ao subir o painel e depois a cada
  hora. *(dirigido a estado)*
- **RF-71** — Quando a rotina verifica as conexões, o sistema deve ler
  `GET /items/{id}` de cada uma e abrir uma execução que busca só as conexões cujo
  `lastUpdatedAt` é posterior ao que tinham na última busca de lançamentos delas —
  a conexão nunca buscada conta como avançada —, sem pedir atualização ao banco; se
  nenhuma avançou, não abre execução nem grava linha em `sync_runs`.
  *(dirigido a evento)*
  - *E13.2* — Com `DASH_SYNC_AUTO` e o `lastUpdatedAt` de uma conexão avançado desde
    a última busca, a rotina busca aquela conexão.
- **RF-72** — Quando o painel encerra, o sistema deve parar a rotina sem abrir
  execução nova. *(dirigido a evento)*

## 3. Requisitos não funcionais

- **RNF-01** — Nenhuma dependência nova: o cliente usa `httpx`, já declarado; a
  thread, a trava e o relógio vêm da biblioteca padrão.
- **RNF-02** — O cliente da Pluggy recebe o transporte HTTP por injeção, e os testes
  o exercitam com um transporte falso que registra método e caminho de cada
  chamada.

## 4. Contrato

Não há OpenAPI no repositório; as rotas servem HTML do próprio painel e não têm
consumidor externo.

**Rotas do painel**

- `POST /sincronizar` — até a fase 3, responde como hoje: 200 com a tela de Resumo e
  o resultado, e 400 sem credencial. Na fase 3: 303 para `/` sem HTMX; 200 com o
  fragmento com HTMX; sem credencial, 400 com a tela de Resumo sem HTMX e 200 com o
  fragmento da recusa com HTMX; com execução em andamento, a mesma forma, sem
  execução nova.
- `GET /sincronizar/estado` — novo na fase 3. 200 com o fragmento; 302 para
  `/login` sem sessão.

**Chamadas à Pluggy** (`https://api.pluggy.ai`)

- `POST /auth` — corpo com `clientId` e `clientSecret`; devolve `apiKey`, que vai no
  cabeçalho `X-API-KEY` das demais.
- `GET /items/{id}` · `GET /accounts?itemId=` · `GET /identity?itemId=` ·
  `GET /bills?accountId=`.
- `GET /v2/transactions?accountId=&dateFrom=` — páginas de 500, cursor `next`.
- `PATCH /items/{id}` — só na fase 3.

**Esquema** (migrações numeradas pela ordem de merge)

- Fase 1: `transactions` ganha `status`, `currency_code`, `payment_method`,
  `operation_type`, `mcc`, `bill_id`, `purchase_date`, `counterparty_kind`,
  `counterparty_document` e `counterparty_name`; `accounts` ganha `item_id`; nascem
  `pluggy_items` (com `identity_document`, o CPF do dono lido de `/identity`) e
  `transaction_payloads`, presa a `transactions(id)` com `ON DELETE CASCADE`.
- Fase 2: nascem `transaction_removals` e `card_bills`; `accounts` ganha
  `last_fetched_at` (a última busca bem-sucedida); `pluggy_items` ganha
  `fetched_last_updated_at` (o `lastUpdatedAt` na última busca de lançamentos);
  `sync_runs` ganha `removed_count`, `relinked_count`, `marks_changed_count` e
  `removal_suspended_count`.
- Fase 3: `pluggy_items` ganha `refresh_requested_at`; `sync_runs.status` passa a
  aceitar `running`.

## 5. Fora desta spec

- **O não-escopo do PRD vale inteiro:** eixo banco e conta (`038`), cadastro de
  beneficiário e CNPJ (`039`), camadas e operação (`040`), tela de lançamentos
  (`041`), IA (`043`), o pendente no gasto, reconexão de consentimento,
  sincronizar com o painel desligado e apagar os scripts manuais.
- **Criar conexão.** Criar é `POST /items`, fora da lista fechada, e continua com a
  ferramenta manual de extração; o painel só lê os ids que ela grava em
  `data/item_ids.txt` (RF-73).
- **Nome editável do banco.** É do `038`. Esta spec nomeia o banco pela conta
  corrente da conexão (1.1), e o `038` troca esse nome pelo que o dono der.
- **Exclusão entre o comando e o painel.** A trava é do processo do painel, com a
  biblioteca padrão, como decidiu a discovery; `python -m app.sync` roda em outro
  processo e não a vê.
- **Intervalo do fragmento.** O intervalo com que o fragmento de RF-65 se pede de
  novo é do plano.
- **Repetir a chamada que recebeu 429.** Esta spec fixa não chamar antes do
  `Retry-After` e que conta sem resposta inteira não perde nada; repetir ou não
  depois do intervalo é do plano.
- **Validade do consentimento** (`consentExpiresAt`) não é lida: o aviso vem do
  estado da conexão.

### 5.1 Notas de reconciliação

Norma 8: cada uma entra no PR da fase indicada.

- `docs/plano.md`, tabela *Stack*, linha "Agendamento | APScheduler no processo": o
  PR da fase 3 a reescreve para a thread `dash-sync` no processo do painel, ligada
  por `DASH_SYNC_AUTO`, sem dependência nova.
- `docs/plano.md`, *Modelo de dados*: a lista de tabelas ganha `pluggy_items` e
  `transaction_payloads` no PR da fase 1, e `transaction_removals` e `card_bills` no
  da fase 2.
- `docs/plano.md`, *Convenções*: o PR da fase 1 acrescenta que o valor em reais vem
  de `amountInAccountCurrency` quando a Pluggy o manda; o da fase 2, que o
  lançamento recriado pela Pluggy com id novo é religado e mantém o número interno.
