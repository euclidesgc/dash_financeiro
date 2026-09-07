# Brief — 015-configuracao-e-nome-do-beneficiario

Escrito no presente. Cada requisito é `RF-nn` e é o que passa a valer.

## Um armazém só para o que só o humano sabe

- **RF-01** — Existe **uma** tabela para o que só o humano sabe. `plan_facts`
  sobrevive — ela já tem rótulo, unidade, origem e validade — e
  `plan_parameters` deixa de existir.
- **RF-02** — A migração **converte** as linhas de `plan_parameters` para
  `plan_facts`, preservando nome e valor, com `source` dizendo que vieram dali.
  Nenhum valor que o dono informou se perde.
- **RF-03** — `plan_facts` ganha a coluna `kind`, que separa **fato** (o que ele
  sabe do mundo: saldo de quitação, taxa, custo) de **meta** (o que ele decide:
  meses de reserva, janela da mediana).
- **RF-04** — O valor é guardado em **inteiro**, na unidade que a linha declara:
  `centavos`, `pontos-base` ou `meses`. Nunca em ponto flutuante. A coluna que o
  guarda **não** se chama `value_cents`: um nome que afirma centavos sobre uma
  linha que guarda meses faz `/simulador` exibir "R$ 0,06" onde a resposta é
  "6 meses".
- **RF-04a** — Existe **um** leitor de valor digitado, com uma gramática por
  unidade e **uma** exceção. Dinheiro se escreve na forma brasileira e `5000.00`
  é recusado; taxa aceita ponto decimal e se limita a 0–100% ao mês; `inf`,
  `nan` e `1e308` são recusados em qualquer unidade, nunca HTTP 500.
- **RF-05** — Quem lia `plan_parameters` passa a ler `plan_facts`, e o saldo de
  quitação informado em `/dividas` aparece em `/simulador` e vice-versa — hoje
  não aparece.

## O catálogo declara o que cada valor muda

- **RF-06** — Existe um **catálogo** dos valores que o painel aceita, declarado
  como dado e não como literal espalhado: nome, rótulo, ajuda, unidade, tipo, a
  tela onde se edita e **qual número aquele valor muda**.
- **RF-07** — Valor fora do catálogo é recusado na gravação, com mensagem que
  nomeia o valor inválido — a mesma régua das regras de classificação do `002`.
- **RF-08** — O catálogo cobre, no mínimo, os quatro valores que hoje têm
  consumidor no código: **saldo de quitação do CDC** (a conta de vender o carro),
  **custo mensal de transporte sem o carro** (o texto que declara o fluxo
  liberado), **meses de reserva do objetivo** e **meses da janela da mediana**.
  A **taxa mensal de cada dívida sem taxa** continua onde está, em `/dividas`, um
  campo por dívida gravado em `debts.monthly_rate_bp`: não é uma linha
  `nome → valor` e o catálogo a declara como editável ali, sem duplicá-la.
- **RF-08a** — O catálogo tem **um nome canônico** por valor. Hoje o mesmo fato
  tem dois: `/dividas` grava `quitacao` e o consultor procura `quitacao-cdc`, e
  por isso ele pergunta para sempre o que o dono já respondeu. A migração
  converte os nomes antigos para o canônico.
- **RF-09** — Meta informada **substitui** a constante que a governa hoje:
  `RESERVE_MONTHS` em `app/plan/objective.py` e `MONTHS` em
  `app/projection/monthly.py` passam a ser o **padrão** quando não há meta
  informada, não o valor final.
- **RF-10** — `WINDOW_DAYS` em `app/commitments/calendar.py` **não** entra no
  catálogo, e a razão não é ter mais consumidores — medido, tem menos que
  `MONTHS`, que entra. A razão é que 45 dias é **vocabulário do produto**,
  impresso na tela como "os próximos 45 dias", enquanto meses da mediana é uma
  **escolha estatística do dono** sobre quantos meses representam o mês típico
  dele.
- **RF-10a** — Meta que a base não comporta é **recusada**, não truncada em
  silêncio: pedir mediana de 12 meses numa base com 6 fechados diria 12 e
  calcularia 6. E a tela declara que os meses da mediana movem também o piso de
  sobrevivência, e com ele a reserva alvo — os dois valores não são
  independentes.
- **RF-11** — Tolerância de modelo — os dez dias do calendário, os 2% que
  separam duas compras, o piso de saldo da taxa observada — **não** entra no
  catálogo. A invariante 26 fala do que só o humano sabe, não do que é ajustável.

## A tela de configuração

- **RF-12** — `GET /configuracao` serve a tela, atrás da sessão, e o Resumo leva
  até ela.
- **RF-13** — A tela lista o catálogo em dois blocos — **fatos** e **metas** —,
  cada linha com o valor atual, a validade quando houver, **o que ele muda** e o
  caminho para a tela onde se edita no contexto.
- **RF-14** — Valor ausente aparece como **ausente**, dizendo o que o painel usa
  no lugar enquanto ele não vier — nunca como zero.
- **RF-15** — Valor **vencido** aparece marcado, como já acontece em
  `/simulador`.
- **RF-16** — A tela **grava** o valor, e o número que ele muda se move na
  resposta da mesma requisição, sem reingestão e sem reiniciar o processo.
- **RF-17** — Os campos que já existem em `/dividas` e `/simulador` continuam
  onde estão e escrevem no mesmo armazém: a configuração é índice e complemento,
  não substituição.

## O nome real do beneficiário

- **RF-18** — O consolidador carrega adiante o que a Pluggy já manda e hoje é
  descartado: `merchant.name`, que é o **nome fantasia**;
  `merchant.businessName`, que é a **razão social**; `merchant.cnpj`; e
  `paymentData.receiver.name`, que também é razão social. Campo que a Pluggy
  manda como string vazia é ausência, não valor.
- **RF-19** — A carga grava esses campos, e na base de 05/09/2026 ficam com nome
  vindo da Pluggy **53** lançamentos por nome fantasia, **338** por razão social
  e **169** por nome de recebedor — **404** lançamentos distintos, 20,8% do
  total, alcançando **148** descrições normalizadas.
- **RF-20** — Existe a tabela `payee_names`, que prende um nome legível a um
  **beneficiário**, não a uma descrição: um apelido alcança todos os lançamentos
  daquele beneficiário, hoje e no futuro.
- **RF-21** — O nome exibido segue uma **precedência declarada**, ordenada pela
  qualidade do nome e não pela fonte: apelido do dono; nome fantasia que a
  Pluggy já mandou; nome fantasia consultado por CNPJ; razão social; descrição
  normalizada, como hoje.
- **RF-22** — A tela mostra de **onde** o nome veio, e a origem é dado da linha,
  não adivinhação de quem lê.
- **RF-23** — A lista de beneficiários a batizar é ordenada **por quanto dinheiro
  cada um representa**, sobre **todo o histórico** e usando o predicado de gasto
  único do projeto, e mostra os **30** primeiros. Na base de 05/09/2026 são
  **720** beneficiários no gasto; os 30 maiores cobrem **55,53%** do dinheiro e
  os 100 maiores cobrem **72,83%**. Dos 720, **137** já têm nome vindo da Pluggy
  — 19,0% dos beneficiários, mas **36,1%** do dinheiro. O maior de todos,
  `debito prestacao hab` com R$ 22.204,77, é justamente um que a Pluggy **não**
  nomeia.
- **RF-24** — Batizar um beneficiário não reescreve lançamento: o apelido é
  resolvido na leitura, e apagá-lo devolve o nome anterior.

## O CNPJ, e o que fazer sem rede

- **RF-25** — Onde há CNPJ, o painel consulta o nome fantasia numa fonte pública
  **nomeada** — `https://brasilapi.com.br/api/cnpj/v1/{cnpj}`, sem chave —,
  **sob demanda do dono**, nunca na carga.
- **RF-25a** — A consulta é **opt-in**, como a do consultor do `009`: desligada
  enquanto o dono não a habilitar por variável de ambiente, e a tela declara que
  está desligada em vez de esconder o botão. O produto é local por definição, e
  cada consulta conta a um terceiro que este usuário tem relação comercial com
  aquele CNPJ — numa lista ordenada por quanto cada um representa.
- **RF-25b** — O CNPJ é validado como **14 dígitos** antes de virar URL. Ele vem
  de terceiro, não do dono, e um valor com barra ou esquema mudaria o alvo da
  requisição.
- **RF-25c** — Cada CNPJ vai à rede **uma vez**: o nome consultado fica guardado
  com a origem `cnpj`, e é ele que responde na próxima leitura.
- **RF-26** — Sem rede, com erro ou com resposta inesperada, a consulta **degrada
  com `200`** e diz o que aconteceu em português, e o nome que já existia
  permanece — a mesma régua do consultor do `009`, com tempo limite próprio: a
  tela de configuração não espera um modelo.
- **RF-27** — O nome consultado entra como **sugestão**, com a origem declarada,
  e o dono aceita ou corrige. Não vira apelido sozinho, e batizar por cima
  **não apaga** o nome consultado: apagar o apelido devolve o que havia antes.

## O que não pode quebrar

- **RF-28** — A classificação, os compromissos, a escada e a projeção continuam
  agrupando por `payee`. O apelido é **camada de leitura**; nenhum número muda
  por causa dele.
- **RF-29** — Nenhum número medido nesta base aparece como literal no código de
  produção, e os números novos entram em `tests/test_frozen_numbers.py`, que é o
  mecanismo permanente — um `grep` de uma vez só prova a árvore de hoje.
- **RF-30** — A tela obedece à linguagem visual: cor e espaço só de `tokens.css`,
  foco visível, sem rolagem horizontal do corpo de 375 a 1440, e
  `prefers-reduced-motion` respeitado.
