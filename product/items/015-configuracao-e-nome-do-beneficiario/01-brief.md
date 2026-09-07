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
  `centavos`, `pontos-base` ou `meses`. Nunca em ponto flutuante.
- **RF-05** — Quem lia `plan_parameters` passa a ler `plan_facts`, e o saldo de
  quitação informado em `/dividas` aparece em `/simulador` e vice-versa — hoje
  não aparece.

## O catálogo declara o que cada valor muda

- **RF-06** — Existe um **catálogo** dos valores que o painel aceita, declarado
  como dado e não como literal espalhado: nome, rótulo, ajuda, unidade, tipo, a
  tela onde se edita e **qual número aquele valor muda**.
- **RF-07** — Valor fora do catálogo é recusado na gravação, com mensagem que
  nomeia o valor inválido — a mesma régua das regras de classificação do `002`.
- **RF-08** — O catálogo cobre, no mínimo: taxa mensal de cada dívida sem taxa,
  saldo de quitação do CDC, custo mensal de transporte sem o carro, renda mensal
  esperada, meses de reserva do objetivo e meses da janela da mediana.
- **RF-09** — Meta informada **substitui** a constante que a governa hoje:
  `RESERVE_MONTHS` em `app/plan/objective.py` e `MONTHS` em
  `app/projection/monthly.py` passam a ser o **padrão** quando não há meta
  informada, não o valor final.
- **RF-10** — `WINDOW_DAYS` em `app/commitments/calendar.py` **não** entra no
  catálogo: o item `004` a consome como contrato entre telas, e mudá-la mudaria o
  significado de "os próximos 45 dias" em três lugares.
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
  cada um representa**, e mostra os **30** primeiros. Na base de 05/09/2026 são
  **721** beneficiários no gasto; os 30 maiores cobrem **55,8%** do dinheiro, e
  os 100 maiores cobrem **73,0%**. Dos 721, **137** já têm nome vindo da Pluggy
  — 19,0% dos beneficiários, mas **35,5%** do dinheiro.
- **RF-24** — Batizar um beneficiário não reescreve lançamento: o apelido é
  resolvido na leitura, e apagá-lo devolve o nome anterior.

## O CNPJ, e o que fazer sem rede

- **RF-25** — Onde há CNPJ, o painel consulta o nome fantasia numa fonte pública,
  **sob demanda do dono**, nunca na carga.
- **RF-26** — Sem rede, com erro ou com resposta inesperada, a consulta **degrada
  com `200`** e diz o que aconteceu em português, e o nome que já existia
  permanece — a mesma régua do consultor do `009`.
- **RF-27** — O nome consultado entra como **sugestão**, com a origem declarada,
  e o dono aceita ou corrige. Não vira apelido sozinho.

## O que não pode quebrar

- **RF-28** — A classificação, os compromissos, a escada e a projeção continuam
  agrupando por `payee`. O apelido é **camada de leitura**; nenhum número muda
  por causa dele.
- **RF-29** — Nenhum número medido nesta base aparece como literal no código de
  produção.
- **RF-30** — A tela obedece à linguagem visual: cor e espaço só de `tokens.css`,
  foco visível, sem rolagem horizontal do corpo de 375 a 1440, e
  `prefers-reduced-motion` respeitado.
