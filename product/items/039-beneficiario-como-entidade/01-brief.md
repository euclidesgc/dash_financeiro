# Brief — 039-beneficiario-como-entidade

**Item:** `039-beneficiario-como-entidade` · **Trilha:** rápida · **Fases:** 1 o
cadastro (RF-01 a RF-25); 2 a consulta de CNPJ sem clique (RF-26 a RF-30)

**Depende de:** `037` fase 1. A migração 019 grava em cada lançamento
`counterparty_name`, `counterparty_document` e `counterparty_kind` (CPF ou CNPJ),
escolhidos pelo sentido: na saída quem recebeu, na entrada quem pagou, no cartão
o estabelecimento. Este item lê essas colunas e não as redefine.

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem igual.

## Problema

Para o dono, único usuário do painel, o beneficiário é um texto: a descrição do
extrato normalizada. A base tem 805 deles. "IFOOD *RESTAURANTE X" vira
`ifood restaurante x` e "iFood.com" vira `ifood com`: a mesma empresa em duas
linhas do eixo beneficiário, sem jeito de juntá-las. Se a descrição de um
lançamento muda — 5 das 94 compras parceladas mudam entre parcelas —, a chave
antiga fica. A razão social chega por um clique por beneficiário, e a consulta
devolve um nome só. O CPF ou CNPJ da contraparte que o `037` grava não identifica
ninguém. Ler os gastos por quem recebeu o dinheiro, que é o que o eixo promete,
não funciona.

## Escopo

O beneficiário é um cadastro: nome do dono, razão social, nome fantasia, CPF ou
CNPJ e ramo de atividade. O documento da contraparte junta sozinho as descrições
diferentes da mesma empresa ou pessoa; sem documento, junta a descrição
normalizada. O que o documento não junta, o dono funde em `/configuracao` — e
desfaz a fusão que estiver errada —, e fundir nunca muda total; ali ele também
renomeia. O eixo beneficiário soma por cadastro. Os nomes que o `015` gravou
migram para o cadastro.

Na fase 2, a razão social, o nome fantasia e o ramo de atividade chegam sem
clique: depois da sincronização, cada CNPJ sem consulta é consultado uma vez na
BrasilAPI, uma consulta por segundo, e falha não rebaixa a sincronização. A
consulta continua opt-in; no ambiente do dono ela é ligada ao fim da fase 2,
porque ele pediu razão social e nome fantasia.

## Não-escopo

- **A tela própria de beneficiários é o item `042`.** Lá entram quantidade de
  lançamentos, classificação padrão e classificar em massa, e a seção de nomes
  sai de `/configuracao`. Aqui fundir e renomear moram na seção que já existe.
- **Fundir não muda a classificação.** A regra de texto exato alcança só o
  `payee` que ela nomeia; o padrão de classificação por beneficiário é do `040`,
  e o "corrigir" de `/gastos` o grava no `042`.
- **Os compromissos não trocam de chave.** A `series_key` é o `payee`; trocá-la
  mexe no `003` sem pedido.
- **Nenhuma expressão regular junta beneficiários.** Com ela o dono escreveria
  regex para dizer que dois nomes são a mesma empresa; juntar é fusão explícita.
- **CPF não é consultado.** Não existe fonte pública; fica o nome que o banco
  mandou.
- **A consulta não liga por padrão.** Ligada em toda instalação, ela manda CNPJ
  para fora sem pedido.
- **A IA não lê o cadastro.** A sugestão por beneficiário, com ramo de
  atividade, é o `043`.

## O que este brief substitui

- **RF-20 do `015`** (`payee_names`, o nome preso à descrição normalizada): vale
  o cadastro do RF-01, e `payee_names` sai pela migração do RF-16.
- **RF-21 do `015`** (a precedência do nome em cinco níveis): vale a precedência
  de seis níveis do RF-07.
- **RF-25 do `015`** ("sob demanda do dono, nunca na carga"): a consulta sob
  demanda continua no RF-20, e a fase 2 consulta cada CNPJ depois da
  sincronização (RF-26).

O brief do `015` é reescrito nesses três pontos pelo `doc-reconciler`, no PR da
fase que muda cada um (norma 8): RF-20 e RF-21 na fase 1, RF-25 na fase 2.

## O que este brief herda do `015`

| No `015` | Neste item |
|---|---|
| RF-22 e RF-23 (origem do nome, lista por dinheiro) | Herdados no RF-09, sobre o cadastro. |
| RF-24 (nome resolvido na leitura, apagar devolve o anterior) | Herdado nos RF-10 e RF-11. |
| RF-25a (consulta opt-in) | **Continua valendo**, para as duas formas de consulta (RF-21 e RF-27): desligada enquanto o dono não a liga por `DASH_CNPJ_LOOKUP`. |
| RF-25b (14 dígitos) | Herdado no RF-22. |
| RF-25c (uma vez por CNPJ) | Herdado nos RF-20 e RF-26: o resultado é guardado por CNPJ. |
| RF-26 (degradar com 200) | Herdado no RF-23. |
| RF-27 (o nome consultado não vira apelido) | Herdado: razão social e nome fantasia ficam abaixo do nome do dono na precedência, e nomear por cima não os apaga (RF-11). |
| RF-28 (classificação e compromissos por `payee`) | Herdado no RF-18; o eixo beneficiário agrupa por cadastro (RF-17) sem mudar total (RF-14). |

## Requisitos

### Fase 1 — o cadastro

- **RF-01** — O sistema deve manter um cadastro de beneficiários em que cada um
  tem nome do dono, razão social, nome fantasia, tipo de documento (CPF ou CNPJ),
  número do documento e ramo de atividade, todos opcionais, e o conjunto de
  chaves — documentos e descrições normalizadas — que apontam para ele.
  *(ubíquo)*
- **RF-02** — O sistema deve atribuir cada lançamento, de entrada ou de saída, a
  exatamente um beneficiário. *(ubíquo)*
- **RF-03** — O sistema deve atribuir o lançamento que traz documento ao
  beneficiário daquele documento, qualquer que seja a descrição. O documento é o
  `counterparty_document` e, na falta dele, o `merchant_cnpj`. Exemplos:
  "IFD*IFOOD.COM" e "IFOOD *RESTAURANTE", com o mesmo CNPJ `14380200000121`,
  pertencem ao mesmo beneficiário; dois Pix enviados ao mesmo CPF, com
  descrições diferentes, pertencem a um beneficiário só, do tipo CPF, com o nome
  que veio do `paymentData`. *(ubíquo)*
- **RF-04** — O sistema deve atribuir o lançamento sem documento ao beneficiário
  da sua descrição normalizada (`payee`). Exemplo: "PADARIA SAO JOSE 12/03" e
  "PADARIA SAO JOSE", sem documento, têm a chave `padaria sao jose` e pertencem
  a um beneficiário só. *(ubíquo)*
- **RF-05** — Quando a sincronização grava um lançamento cuja chave foi fundida
  em outro beneficiário, o sistema deve atribuí-lo ao beneficiário de destino.
  Exemplo: com `mercado livre pago` fundido em `mercado livre`, um lançamento
  novo com a chave `mercado livre pago` pertence ao beneficiário fundido.
  *(dirigido a evento)*
- **RF-06** — Quando a sincronização grava uma descrição diferente num
  lançamento que já existe, o sistema deve recalcular o `payee` a partir da
  descrição nova, e o lançamento sem documento passa ao beneficiário da chave
  nova. Exemplo: a parcela 2/10 volta da Pluggy com a descrição trocada de
  "MERCADOLIVRE*LOJA" para "MERCADO LIVRE LOJA" e sem documento: o `payee` é o
  da descrição nova, e a linha pertence ao beneficiário dessa chave, nunca à
  chave antiga. *(dirigido a evento)*
- **RF-07** — O sistema deve exibir como nome do beneficiário o primeiro que
  existir nesta ordem: nome do dono; `merchant.name` que a Pluggy mandou; nome
  fantasia; razão social; nome que veio do banco com o lançamento
  (`counterparty_name`); descrição normalizada. Exemplo: CNPJ `14380200000121`,
  sem nome do dono, `merchant.name` "iFood", nome fantasia vazio e razão social
  "IFOOD.COM AGENCIA DE RESTAURANTES ONLINE S.A." exibe "iFood"; depois de o
  dono nomeá-lo "Delivery", exibe "Delivery". *(ubíquo)*
- **RF-08** — O sistema deve preencher a razão social do beneficiário de CNPJ
  com a da consulta de CNPJ e, enquanto não houver consulta concluída, com a que
  a Pluggy mandou no estabelecimento (`merchant.businessName`). *(ubíquo)*
- **RF-09** — A lista de beneficiários de `/configuracao` deve listar cadastros,
  na ordem e com o corte do RF-23 do `015`, e cada linha deve trazer o nome
  exibido, de qual das seis fontes do RF-07 ele veio e, quando houver, a razão
  social ao lado. *(ubíquo)*
- **RF-10** — Quando o dono dá nome a um beneficiário em `/configuracao`, o
  sistema deve gravá-lo no cadastro, e toda tela que exibe esse beneficiário
  deve exibir o nome novo sem que número nenhum mude. Exemplo: renomear o
  beneficiário fundido para "Mercado Livre" muda o rótulo em toda tela e não
  muda número nenhum. *(dirigido a evento)*
- **RF-11** — Quando o dono apaga o nome que deu a um beneficiário, o sistema
  deve exibir o próximo nome da precedência do RF-07, com razão social e nome
  fantasia intactos no cadastro. *(dirigido a evento)*
- **RF-12** — Se o nome enviado passa do limite de tamanho que vale para o nome
  do dono, ou o beneficiário não existe, então o sistema deve recusar com 400 e
  mensagem em português, sem gravar. *(comportamento indesejado)*
- **RF-13** — Quando o dono funde um beneficiário em outro em `/configuracao`, o
  sistema deve passar ao destino todas as chaves e todos os lançamentos do
  fundido, que sai de toda lista e de todo eixo; o destino mantém o próprio nome
  do dono, razão social, nome fantasia e documento. Exemplo: fundir
  `mercado livre pago` em `mercado livre` deixa no eixo beneficiário uma linha
  só, com a soma dos dois. *(dirigido a evento)*
- **RF-14** — O sistema deve produzir o mesmo total, em qualquer eixo e filtro,
  antes e depois de uma fusão. Exemplo: o total do eixo beneficiário é igual
  antes e depois de fundir `mercado livre pago` em `mercado livre`. *(ubíquo)*
- **RF-15** — Se o dono pede uma fusão em que um dos dois beneficiários não
  existe ou já está fundido em outro, ou em que os dois são o mesmo, então o
  sistema deve recusar com 400 e mensagem em português, sem gravar.
  *(comportamento indesejado)*
- **RF-16** — Quando a migração da fase 1 roda, o sistema deve passar cada nome
  gravado em `payee_names` ao cadastro do beneficiário da mesma chave, na mesma
  posição da precedência — o de origem `dono` como nome do dono, o de origem
  `cnpj` como nome fantasia — e remover `payee_names`. Exemplo: com a linha
  (`mercado do bairro`, `dono`, "Mercadinho"), depois da migração o beneficiário
  da chave `mercado do bairro` exibe "Mercadinho", e `payee_names` não existe
  mais. *(dirigido a evento)*
- **RF-17** — O sistema deve agrupar o eixo beneficiário por cadastro, rotulado
  pelo nome do RF-07, com total igual ao de qualquer outro eixo no mesmo filtro.
  Exemplo: em `/gastos`, eixo beneficiário, agosto de 2026, "iFood" aparece numa
  linha só, somando as variações do mesmo CNPJ, e o total do eixo é igual ao dos
  outros eixos. *(ubíquo)*
- **RF-18** — O sistema deve usar o `payee` como chave na classificação, nos
  compromissos (a `series_key`), na escada, na projeção e no alcance de regra de
  `/gastos`; o cadastro não muda nenhum deles. *(ubíquo)*
- **RF-19** — O sistema deve consultar só CNPJ: nenhum CPF de contraparte sai do
  app para serviço externo. *(ubíquo)*
- **RF-20** — Quando o dono pede, em `/configuracao`, a consulta de um
  beneficiário de CNPJ, com a consulta ligada, o sistema deve consultar aquele
  CNPJ na BrasilAPI e guardar, por CNPJ, a razão social, o nome fantasia e o
  ramo de atividade — a atividade principal por extenso — que ela devolver, no
  lugar do registro anterior daquele CNPJ. *(dirigido a evento)*
- **RF-21** — Enquanto a consulta de CNPJ está desligada (`DASH_CNPJ_LOOKUP`
  ausente), o pedido de consulta em `/configuracao` deve responder sem chamar a
  BrasilAPI, e a tela deve declarar que a consulta está desligada.
  *(dirigido a estado)*
- **RF-22** — Se o beneficiário não tem CNPJ, ou o CNPJ não tem 14 dígitos,
  então o sistema deve recusar a consulta antes de montar a requisição e dizer o
  motivo na tela. *(comportamento indesejado)*
- **RF-23** — Se a consulta sob demanda falha — sem rede, tempo esgotado, erro
  do serviço, 404 ou resposta fora do formato —, então o sistema deve responder
  200 dizendo em português o que aconteceu, e o que o cadastro já tinha
  permanece. *(comportamento indesejado)*
- **RF-24** — Quando o dono desfaz uma fusão em `/configuracao`, o sistema deve
  devolver ao beneficiário de origem as chaves que vieram dele, e a origem volta
  a toda lista e todo eixo com o próprio cadastro, somando os lançamentos das
  próprias chaves. Para isso, toda fusão fica registrada: origem, destino e as
  chaves que passaram. Exemplo, em base de teste: em agosto de 2026,
  `mercado livre` soma −R$ 300,00 e `mercado livre pago` soma −R$ 120,00;
  fundido `mercado livre pago` em `mercado livre`, o eixo beneficiário mostra
  uma linha de −R$ 420,00; desfeita a fusão, volta a mostrar as duas linhas,
  −R$ 300,00 e −R$ 120,00, e o total do eixo é −R$ 420,00 nos três momentos.
  *(dirigido a evento)*
- **RF-25** — Se o dono pede para desfazer uma fusão que não existe ou que já
  foi desfeita, então o sistema deve recusar com 400 e mensagem em português,
  sem gravar e nunca com 500. *(comportamento indesejado)*

### Fase 2 — a razão social e o nome fantasia sem clique

- **RF-26** — Quando uma sincronização termina em estado diferente de `failed`,
  com a consulta ligada, o sistema deve consultar na BrasilAPI cada CNPJ da base
  sem consulta concluída (achado ou não encontrado), uma vez cada, no ritmo de
  uma consulta por segundo, e guardar por CNPJ o que o RF-20 guarda. Exemplo:
  com 100 CNPJs sem consulta, a sincronização consulta cada um uma vez, uma por
  segundo; a sincronização seguinte consulta zero. *(dirigido a evento)*
- **RF-27** — Enquanto a consulta de CNPJ está desligada, o sistema deve
  terminar toda sincronização sem chamada à BrasilAPI. *(dirigido a estado)*
- **RF-28** — Se a consulta automática recebe 429, ou falha por rede, tempo
  esgotado, erro do serviço ou resposta fora do formato, então o sistema deve
  interromper o lote naquela consulta, registrar a falha daquele CNPJ e terminar
  a sincronização no estado que ela teria sem a consulta. Exemplo: 429 na
  terceira consulta — o lote para, a falha fica registrada e a sincronização
  termina `ok`. *(comportamento indesejado)*
- **RF-29** — Quando uma sincronização começa o lote de consultas, o sistema
  deve consultar os CNPJs nunca consultados antes dos que falharam. Exemplo:
  depois do 429 na terceira consulta, a sincronização seguinte retoma pelos que
  faltam. *(dirigido a evento)*
- **RF-30** — Se a BrasilAPI responde 404 para um CNPJ, então o sistema deve
  registrá-lo como não encontrado, e a consulta automática não volta a ele; só o
  pedido do dono em `/configuracao` o consulta de novo. *(comportamento
  indesejado)*

## Métrica de sucesso

| Métrica | Onde se observa | Alvo |
|---|---|---|
| Beneficiários distintos contra chaves de descrição distintas, na mesma base | Contagem na base do dono (`data/dash.sqlite`) | O primeiro menor que o segundo; os dois medidos e declarados no PR da fase 1 |
| CNPJs da base sem consulta concluída | Registro de consulta por CNPJ na base do dono | Zero, depois da primeira sincronização com a consulta ligada cujo lote não é interrompido |

## Riscos

- **A BrasilAPI é serviço comunitário: 429, 404 e queda acontecem.** Resposta: o
  lote para, a sincronização termina no estado que teria sem a consulta, e a
  seguinte retoma pelos que faltam (RF-28, RF-29); o 404 fica registrado e só
  volta por pedido do dono (RF-30).
- **Recalcular o `payee` move a linha de série nos compromissos**, porque a
  série é por `payee` (RF-18). Resposta: é o que já acontece com a parcela que
  chega nova com a descrição trocada; manter a chave antiga é o defeito descrito
  no Problema.
- **Os números que o `015` mediu na lista de `/configuracao` — 720 beneficiários
  no gasto, os 30 maiores cobrindo 55,53% — contam chaves de descrição.** A lista
  conta cadastros (RF-09), e esses números deixam de descrevê-la. Resposta: o PR
  da fase 1 mede e declara os números da lista por cadastro.
- **O cadastro guarda CPF de terceiros, e a fase 2 chama serviço externo.**
  Resposta: CPF não sai do app (RF-19); CNPJ só sai com a consulta ligada (RF-21,
  RF-27) e validado como 14 dígitos (RF-22); o `security-auditor` entra nas duas
  fases.
- **`payee_names` está vazia na base do dono**, e a migração não tem linha real
  que a prove. Resposta: o RF-16 se verifica em base de teste com a linha do
  exemplo.
