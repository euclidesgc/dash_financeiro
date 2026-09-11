# Discovery — 037-sincronizacao-real-com-a-pluggy

**Item do roadmap:** `037-sincronizacao-real-com-a-pluggy` — o botão
Sincronizar busca na Pluggy, e a base deixa de estar parada em 05/09/2026.

**Data:** 2026-09-10 · **Origem:** plano "Base financeira organizada", aprovado
pelo dono em 10/09/2026 (itens `037` a `044`). · **Trilha declarada:** completa

## O terreno

**"Sincronizar" não fala com a Pluggy.** `POST /sincronizar`
(`app/routers/summary.py:48`) chama `synchronise()` (`app/sync/__init__.py:34`),
que relê `data/processed/transacoes.json` — gerado à mão por
`ingestao/pluggy_extract.py` (rede) e `ingestao/pluggy_consolidate.py` (sinal do
cartão, transferência, estorno, parcela). As 14 execuções depois da primeira
inseriram **zero** lançamentos: o painel mostra o extrato de 05/09 com cara de
fresco, que é o que o `006` existia para impedir. Não há rotina diária.

**Medido na base de 05/09/2026 e no bruto de `data/raw/`:**

- 1.942 lançamentos, 12 contas, 5 conexões MeuPluggy. **139 PENDING**, todas de
  cartão, 43 datadas depois de hoje (parcelas futuras). A maior data da base é
  2027-05-06 — por isso a janela não pode partir da "última data conhecida".
- **14 compras em USD gravadas em dólar**: `pluggy_consolidate.py:174-176` usa
  `amount` e não `amountInAccountCurrency`. Somadas, faltam **R$ 2.346,09** de
  gasto entre dez/2025 e ago/2026.
- Descartados na carga e presentes no bruto: documento do pagador (624) e do
  recebedor (516), `paymentMethod` (720), MCC (978), `operationType` (907),
  `status`, `billId`, `purchaseDate`. `providerId` e `balance` por transação
  vêm nulos em 100% das linhas (MeuPluggy não é conexão regulada).
- `accounts.institution` repete o nome do cartão ("platinum" é o cartão do
  Nubank); o banco é o **item** da Pluggy, e todo `accounts_*.json` traz
  `itemId`.
- 23 créditos pagos pelo CPF do dono e 23 débitos recebidos por ele: **todos já
  marcados** como transferência. A regra do CPF do dono não move número hoje.
- 21 lançamentos sem categoria da Pluggy têm categoria inventada por regex
  (`inferir_categoria`: 15 "Não classificado", 5 "Educação", 1 "Telecom"),
  somando −R$ 233,98.
- Fatos da Pluggy: id de transação **instável** (a passagem PENDING → POSTED
  pode recriar o id); histórico de 12 meses; `PATCH /items/{id}` no máximo uma
  vez por hora por conexão, 409 dentro do intervalo; atualização automática a
  cada 24/12/8 h conforme o plano; `/v2/transactions` aceita `accountId`,
  `dateFrom`, `dateTo`, páginas de 500.
- O fixture `no_network` (`tests/conftest.py:76`) só bloqueia `httpx.get` e
  `httpx.post`: `httpx.request` e `httpx.patch` sairiam para a rede num teste.

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim | Nada aberto antes dele; é o primeiro da cadeia `037`–`044`. |
| Negociável | sim | Fixo: a sync busca na Pluggy e não perde o que foi classificado. Conversável: janela, trava, forma do botão. |
| Valioso | sim | O dono volta a ver o extrato de hoje; o gasto histórico sobe R$ 2.346,09 para o número real. |
| Estimável | sim | Três fases. |
| Pequeno | sim | Três fases: a carga entende o bruto; o botão busca na Pluggy; o botão e o relógio. |
| Testável | sim | Transporte falso injetável no lugar da Pluggy; cada regra abaixo tem exemplo com valores. |

**Veredicto do INVEST:** segue como está. O item já é o resultado da quebra da
iniciativa em oito.

## História

Como dono, quero apertar **Sincronizar** — ou só deixar o painel de pé — e ter
na base os lançamentos que a Pluggy tem hoje, sem duplicata e sem perder nada
do que já foi classificado, para decidir com o extrato de hoje e não com o de
05/09.

## Regras e exemplos

### R1 — Sincronizar busca na Pluggy; o arquivo de `ingestao/` deixa de ser caminho de produção

- **E1.1** — Base com última busca bem-sucedida em 05/09/2026; a Pluggy tem 30
  lançamentos novos, de 06/09 a 10/09, espalhados nas 12 contas. Depois da
  sincronização a base tem 1.972 lançamentos e `sync_runs` registra 30
  inseridos.
- **E1.2** — Sem `PLUGGY_CLIENT_ID` no ambiente: a tela responde 400 com a
  mensagem em português de credencial ausente, e nada é gravado.

### R2 — A janela parte da última busca bem-sucedida da conta, sem data final

- **E2.1** — Hoje 10/09/2026, última busca da conta em 05/09/2026:
  `dateFrom = 2026-07-12` (o menor entre hoje − 60 dias e última busca − 7
  dias), sem `dateTo` — as 43 parcelas datadas depois de hoje continuam vindo.
- **E2.2** — Conta sem busca anterior: busca completa, sem `dateFrom`.

### R3 — O valor é em reais e o sinal diz a direção do dinheiro

- **E3.1** — Compra no cartão "STRIPE Z.AI", `amount` 64.8, `currencyCode` USD,
  `amountInAccountCurrency` 350.57: grava **−35057** centavos.
- **E3.2** — Compra no cartão `amount` 120.00 BRL → −12000. Pagamento de
  fatura na conta de cartão, `amount` −2425.59 → +242559.
- **E3.3** — Na base do dono, as 14 compras em USD somam **R$ 2.346,09** a mais
  de gasto depois da carga — medido e declarado no PR.

### R4 — A contraparte segue o sentido do lançamento

- **E4.1** — Pix enviado da conta Itaú com
  `paymentData.receiver.documentNumber` CNPJ `14380200000121`:
  `counterparty_kind` = CNPJ, `counterparty_document` = `14380200000121`, nome
  = `receiver.name`.
- **E4.2** — Pix recebido com `payer.documentNumber` CPF: `counterparty_kind` =
  CPF, nome = `payer.name`.
- **E4.3** — Compra no cartão com `merchant.cnpj`: a contraparte é o
  estabelecimento — nome, razão social e CNPJ do `merchant`.

### R5 — As marcas moram no app e rodam sobre a tabela inteira, iguais às do consolidador

- **E5.1** — A mesma amostra processada por `app/sync/marks.py` e por
  `ingestao/pluggy_consolidate.py` dá as mesmas tuplas (`pluggy_id`,
  `is_transfer`, `transfer_reason`, `is_refund`, `refunded_by`,
  `is_cash_withdrawal`), elemento a elemento.
- **E5.2** — Débito de −R$ 500,00 na conta Itaú em 03/09 já gravado; a carga
  seguinte traz crédito de +R$ 500,00 na conta Nubank em 05/09: os dois ficam
  `is_transfer = 1`, motivo transferência entre contas próprias.
- **E5.3** — Crédito cujo pagador tem o CPF do dono (lido de `/identity`) é
  transferência própria mesmo sem o par na base. Hoje isso não move número (os
  23 casos já estão marcados).
- **E5.4** — Uma marca que muda de uma sincronização para a outra (um par novo
  que troca o parceiro de um débito antigo) é contada em `sync_runs` e a tela a
  mostra.

### R6 — A categoria inventada por regex não é portada

- **E6.1** — Lançamento cuja categoria da Pluggy veio vazia: `category` fica
  vazia e o grupo sai da classificação (reserva "Outros" se nenhuma regra
  casar). Na base do dono são 21 linhas e −R$ 233,98 que podem trocar de grupo;
  o gasto total não muda.

### R7 — O lançamento recriado pela Pluggy é religado, não duplicado

- **E7.1** — Parcela PENDING `p-velho` (−R$ 50,00, 3/10, `purchase_date`
  2026-07-15) no cartão Itaú Black; a Pluggy a devolve como `p-novo` POSTED com
  o mesmo valor, parcela e data da compra: a base tem **uma** linha, o
  `transactions.id` é o mesmo, o `pluggy_id` passa a `p-novo`, e
  `transaction_removals` fica vazia.
- **E7.2** — Duas compras de R$ 30,00 no mesmo dia, mesma descrição, somem e
  voltam com dois ids novos: o par é ambíguo, nenhuma religa; as duas antigas
  saem com lápide e as novas entram.

### R8 — Só sai da base o que sumiu sem par, dentro da janela, de conta com busca completa — e sai com lápide

- **E8.1** — Conta com 40 lançamentos na janela e resposta 200 vazia para ela:
  **nenhuma** linha some, e a tela diz que a remoção dessa conta foi suspensa.
- **E8.2** — Lançamento datado de hoje − 200 dias, ausente da resposta:
  continua na base. A Pluggy guarda 12 meses; a base local guarda tudo.
- **E8.3** — Compra PENDING de R$ 89,90 cancelada pela Pluggy (some sem par),
  numa conta com 60 lançamentos na janela: sai da base e fica em
  `transaction_removals` com o bruto. A trava suspende só quando faltam mais que
  max(5, 20%) das linhas da janela.

### R9 — Conexão que pede novo login não perde nada e diz o que fazer

- **E9.1** — O item do Itaú em `LOGIN_ERROR`: as quatro contas dele não sofrem
  remoção, as outras quatro conexões sincronizam, e a tela diz que o Itaú pede
  novo login em meu.pluggy.ai.

### R10 — O cliente só faz as chamadas da lista fechada

- **E10.1** — O registro do transporte falso de uma sincronização completa só
  contém `POST /auth`, `GET /items/{id}`, `GET /accounts`,
  `GET /v2/transactions`, `GET /bills`, `GET /identity` e
  `PATCH /items/{id}`. Qualquer outro método ou caminho levanta erro antes de
  sair.
- **E10.2** — Nenhum teste sai para a rede: `httpx.request` e `httpx.patch`
  também são bloqueados pelo fixture.

### R11 — Pedir atualização ao banco: no máximo uma vez por hora por conexão

- **E11.1** — Uma conexão com pedido feito há 30 minutos e outra há 2 horas:
  só a segunda recebe `PATCH`. Um 409 da Pluggy não rebaixa a execução.

### R12 — O botão não reenvia no F5 e mostra o estado por banco

- **E12.1** — `POST /sincronizar` sem HTMX responde 303 para `/`; com HTMX
  responde 200 com o fragmento que acompanha o andamento por
  `GET /sincronizar/estado`.
- **E12.2** — A tela mostra, por instituição, "atualizado pela Pluggy em
  10/09/2026 06:12", lido do `lastUpdatedAt` do item.

### R13 — A rotina diária é opt-in, uma execução por vez, e segue a Pluggy

- **E13.1** — Sem `DASH_SYNC_AUTO`, subir o app não cria thread `dash-sync`.
- **E13.2** — Com `DASH_SYNC_AUTO` e o `lastUpdatedAt` de uma conexão avançado
  desde a última busca, a rotina busca aquela conexão; o botão apertado durante
  a execução responde que já há uma sincronização em andamento.
- **E13.3** — A rede roda fora da transação SQL; um erro na escrita desfaz a
  carga inteira e `sync_runs` grava `failed` — o "tudo ou nada" do `012`
  continua.

## Perguntas em aberto

Nenhuma.

## Trilha

**Trilha: completa**

| Gatilho | Verdadeiro | Evidência |
|---|---|---|
| Zero perguntas em aberto | sim | Nenhuma; as decisões estão abaixo e no plano aprovado. |
| Uma stack só | sim | Só a frente `api` (`.`, Python). |
| Sem mudança de contrato | sim | Não existe OpenAPI no repositório; as rotas são HTML servidas pelo próprio app. `POST /sincronizar` muda de 200 para 303/fragmento e nasce `GET /sincronizar/estado`, sem consumidor externo. |
| Sem dependência nova | sim | `httpx` já está declarado; thread e trava vêm da biblioteca padrão. |

Os quatro gatilhos permitiriam a trilha rápida. **A trilha completa é decisão do
dono, em 10/09/2026:** este é o único item da cadeia `037`–`044` que apaga
lançamentos da base, e o primeiro a falar com a Pluggy com credencial. A spec em
EARS, requisito por requisito, dá ao validador cego uma régua mais fina
exatamente onde um erro custa dado do dono — ao preço de um documento e uma
aprovação a mais.

O item toca **fronteira externa com credencial** (Pluggy) e **documento de
terceiros** (CPF/CNPJ de contraparte): o `security-auditor` entra nas fases 1 e
2, como manda a ordem da fase.

## Decisões autônomas

| Dúvida | Decisão | Alternativa descartada e por quê |
|---|---|---|
| O que sumiu da Pluggy sai ou fica marcado? | **Sai por DELETE, com lápide** em `transaction_removals`, depois da religação. | Soft-delete obriga os ~20 leitores de `transactions` a filtrar; um esquecido corrompe número em silêncio. |
| Como o que o dono anota sobrevive à troca de id? | **Religação**: o `transactions.id` é mantido e só o `pluggy_id` muda; tudo o que se prende ao id sobrevive. | Migrar anotação por impressão digital a cada sync duplica o mecanismo e falha no par ambíguo. |
| De onde parte a janela? | Da **última busca bem-sucedida** da conta, sem data final. | A última data da base é 2027-05-06 por causa das parcelas futuras. |
| Porta a categoria por regex? | **Não.** A classificação decide. | Os nomes que a regex inventa são nomes de grupo, e `tests/test_taxonomy_literals.py` reprovaria. |
| Rotina diária com APScheduler? | **Não**: thread no `lifespan`, com `threading.Event`, opt-in por `DASH_SYNC_AUTO`. | Dependência nova para um relógio de uma linha; norma 15. |
| A rede entra na transação da carga? | **Não.** Busca primeiro, escreve curto depois. | Transação aberta durante a rede trava o SQLite para as telas. |
| `ingestao/` continua? | Como **oráculo de teste** das marcas e ferramenta manual, não como caminho do botão. | Apagar agora tira o oráculo que prova o porte. |

## Validações de campo previstas

- Uma sincronização real contra a Pluggy do dono traz os lançamentos de 05/09
  em diante, sem duplicata.
- O `PATCH` num item MeuPluggy chega ou não ao banco (o agregador tem cadência
  própria). O comportamento é o mesmo nos dois casos: a tela mostra o
  `lastUpdatedAt` que a Pluggy devolver.
