# Brief — Gastos em três eixos

**Item:** `002-gastos-tres-eixos` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado e validador cego valem igual. Se uma
> divergência for aprovada durante a execução, o item é promovido para a trilha
> completa e o `doc-reconciler` desdobra este arquivo em `01-prd.md` e
> `02-spec.md`.

## Problema

O dono deste painel tem um déficit de R$ 4.940,72/mês e precisa cortar gasto
sem cortar o que sustenta a casa. O banco do item `001` sabe responder uma
pergunta só: "você gastou R$ 103.772,33 em seis meses". Esse número não decide
nada — ele não separa a escola dos R$ 12.992,18 do delivery, nem a prestação da
casa da assinatura esquecida.

O eixo de categoria sozinho também não decide. As 77 categorias que os dados
trazem são vocabulário da Pluggy, montado para classificar transação, não para
responder "isto é fixo ou variável" e "isto sustenta a casa ou é conforto". Sem
esses dois eixos, cortar vira adivinhação: ou se corta o que dói pouco e não
muda a conta, ou se corta o que fazia falta e o corte não dura um mês.

E qualquer taxonomia escrita dentro do código erra na primeira semana de uso. O
que é supérfluo na casa de alguém não é decisão de quem escreve o código, e
corrigir a classificação não pode custar um deploy.

## Escopo

Depois deste item o dono lê os próprios gastos por **grupo**, **categoria**,
**beneficiário**, **natureza** (fixa · variável · eventual) e **essencialidade**
(essencial · importante · supérfluo), em qualquer período, e desce de qualquer
linha até a transação que a compõe. Trocar o eixo reparticiona o mesmo total;
nunca muda o total.

Dois cruzamentos ficam prontos na tela: **variável × supérfluo**, que é a lista
de corte, e **fixa × essencial**, que é o piso de sobrevivência do mês — o
número que dimensiona a reserva do item `007`. A evolução de treze meses mostra
se o corte pegou.

A classificação mora em tabela — `category_groups`, `categories`,
`category_rules` — e se edita na tela de **Regras**, sem deploy e sem
reingestão. O que nenhuma regra alcança não desaparece: aparece contado, em
lançamentos e em dinheiro, nas duas telas.

## Não-escopo

- **Resumo, saldo do dia e projeção de 45 dias não entram.** É o item `004`, que
  depende do `003` para somar compromissos datados. Este item lê o passado; a
  projeção é outra pergunta e outra tela.
- **Assinatura recorrente, parcelamento e calendário de vencimento não entram.**
  É o item `003-comprometido`. Detectar recorrência é análise de série, não
  agregação de período, e misturar as duas nesta tela produziria uma tela que
  responde duas perguntas pela metade.
- **Dívidas, escada de taxa e simuladores não entram.** É o item `005`. Juros
  pagos aparecem aqui como gasto do grupo `Dívidas e juros`, nada além disso.
- **Sincronização com a Pluggy não entra.** É o item `006`. A base é a que o
  `001` carregou de arquivo em disco; nada nesta tela dispara rede.
- **IA não entra, e classificação por IA menos ainda.** É o item `009`. O
  resíduo que as regras não pegam fica visível e esperando — resíduo silencioso
  é resíduo que ninguém corrige, e resíduo classificado por palpite de modelo é
  pior, porque parece resolvido.
- **Reclassificar um lançamento isolado, à mão, não entra.** A classificação é
  por regra, e uma exceção por lançamento seria uma segunda fonte de verdade
  sobre o mesmo dado: o total da tela deixaria de ser explicável pela tabela de
  regras.
- **Orçamento ou meta por categoria não entra.** O objetivo com data é o item
  `007`; aqui não há alvo a bater, só distribuição a ler.

## Requisitos

### Taxonomia em tabela

- **RF-01** — O sistema deve criar por migração numerada as tabelas
  `category_groups`, `categories` e `category_rules`, mais a coluna
  `transactions.payee` com índice, sem editar migração já aplicada. *(ubíquo)*
- **RF-02** — O sistema deve manter em `category_groups` exatamente dez linhas:
  Moradia, Educação, Transporte, Alimentação, Comer fora e lazer, Saúde,
  Serviços e assinaturas, Dívidas e juros, Transferências, Outros. *(ubíquo)*
- **RF-03** — O sistema deve aceitar como natureza apenas `fixa`, `variável` ou
  `eventual`, e como essencialidade apenas `essencial`, `importante` ou
  `supérfluo`. *(ubíquo)*
- **RF-04** — O sistema deve gravar em `category_rules` regras de dois tipos —
  casamento pela categoria da Pluggy e casamento por expressão sobre a descrição
  normalizada —, e cada regra declara grupo, natureza e essencialidade.
  *(ubíquo)*
- **RF-05** — Quando o seed da taxonomia roda, o sistema deve cobrir por regra as
  76 categorias nomeadas da base (74 vindas da Pluggy, mais as inferidas na
  consolidação), e nenhuma delas recebe essencialidade `supérfluo`: o seed é
  conservador por decisão registrada (D2), e a tela é o lugar de corrigir.
  A 77ª, `Não classificado`, **não** ganha regra: ela é o nome que a
  consolidação deu ao que ninguém classificou, e cobri-la por regra esvaziaria
  o balde de resíduo no primeiro dia, escondendo justamente o que precisa de
  olho. *(dirigido a evento)*
- **RF-06** — Quando o seed roda uma segunda vez sobre o mesmo banco, o sistema
  deve manter a contagem de linhas de `category_groups`, `categories` e
  `category_rules` inalterada. *(dirigido a evento)*
- **RF-07** — Se a gravação de uma regra declara grupo, natureza ou
  essencialidade fora das listas de RF-02 e RF-03, então o sistema deve recusar
  a gravação com mensagem que nomeia o valor inválido, e a tabela permanece como
  estava. *(comportamento indesejado)*
- **RF-08** — O sistema deve ler o vocabulário da tabela em toda consulta:
  nenhum arquivo de `app/` traz nome de grupo, de natureza, de essencialidade ou
  de categoria da Pluggy como literal dentro de uma condição. *(ubíquo)*

### Motor de classificação

- **RF-09** — O sistema deve atribuir a todo lançamento exatamente um grupo, uma
  natureza e uma essencialidade: depois da carga da taxonomia, a contagem de
  lançamentos sem os três eixos é zero, incluídos os 21 de categoria inferida na
  consolidação e os 15 em `Não classificado`. *(ubíquo)*
- **RF-10** — O sistema deve derivar o beneficiário da descrição normalizada e
  gravá-lo em `transactions.payee`, de modo que o período de 01/03/2026 a
  31/08/2026 tenha 317 beneficiários distintos **entre as linhas de gasto** — o
  mesmo universo dos 732 lançamentos e das 52 categorias, isto é, valor
  negativo com `is_transfer = 0`, `is_refund = 0` e `refunded_by IS NULL` —,
  com `debito prestacao hab` no topo somando −R$ 12.358,81 em 5 lançamentos.
  *(ubíquo)*
- **RF-11** — O sistema deve aplicar as regras em ordem determinística —
  primeiro as de expressão sobre a descrição, depois as de categoria, e dentro
  de cada tipo pela ordem crescente de `id`, classificando pela primeira que
  casa —, de modo que reexecutar a classificação sobre a mesma base produza
  classificação idêntica em todos os 1.942 lançamentos. *(ubíquo)*
- **RF-12** — Se nenhuma regra alcança um lançamento, então o sistema deve
  classificá-lo no grupo `Outros`, natureza `eventual`, essencialidade
  `importante`, e contá-lo como resíduo, com o número de lançamentos e a soma em
  centavos disponíveis para a tela. *(comportamento indesejado)*
- **RF-13** — Quando uma regra é gravada ou alterada, o sistema deve
  reclassificar os lançamentos que ela alcança e refletir a mudança na consulta
  seguinte, sem reingestão e sem reiniciar o processo: mudar a essencialidade de
  `Eating out` de `importante` para `supérfluo` move os 128 lançamentos daquela
  categoria — 60 deles no período de 01/03/2026 a 31/08/2026, somando
  −R$ 4.360,13 — para o cruzamento variável × supérfluo. *(dirigido a evento)*
- **RF-14** — Se a gravação de uma regra ou a reclassificação que ela dispara
  falha no meio, então o sistema deve desfazer a operação inteira e manter a
  classificação anterior de todos os lançamentos, sem deixar parte da base
  reclassificada. *(comportamento indesejado)*

### Agregação pelos cinco eixos

- **RF-15** — O sistema deve agregar o gasto por qualquer um dos cinco eixos —
  grupo, categoria, beneficiário, natureza, essencialidade — sobre um período
  delimitado por data inicial e data final livres, devolvendo por linha o valor
  somado e a contagem de lançamentos. *(ubíquo)*
- **RF-16** — O sistema deve excluir de todo agregado de gasto as linhas com
  `is_transfer = 1` (152 na base), `is_refund = 1` (9) e `refunded_by`
  preenchido, de modo que o período de 01/03/2026 a 31/08/2026 some
  −R$ 103.772,33 em 732 lançamentos. *(ubíquo)*
- **RF-17** — O sistema deve devolver, no eixo categoria e nesse período, 52
  linhas ordenadas do maior gasto para o menor, começando por `School`
  −R$ 12.992,18 (20 lançamentos), `Real estate financing` −R$ 12.358,81 (5),
  `Services` −R$ 8.774,12 (48), `Loans and financing` −R$ 7.870,50 (7),
  `Transfers` −R$ 6.220,71 (21), `Transfer - Bank Slip` −R$ 5.239,59 (1),
  `Groceries` −R$ 5.017,64 (84), `Transfer - PIX` −R$ 4.685,15 (58),
  `Eating out` −R$ 4.360,13 (60) e `Shopping` −R$ 4.178,70 (84). *(ubíquo)*
- **RF-18** — O sistema deve devolver, no eixo beneficiário e nesse período,
  `debito prestacao hab` −R$ 12.358,81 (5), `pagamento de boleto sociedade de
  assistencia e cultura sagra` −R$ 10.880,05 (7) e `pagamento de boleto safra cfi s a`
  −R$ 7.497,38 (6) nas três primeiras posições. *(ubíquo)*
- **RF-19** — O sistema deve contar PIX e boleto a terceiros como gasto: nesse
  período, `Transfer - PIX` soma −R$ 4.685,15 em 58 lançamentos e
  `Transfer - Bank Slip` soma −R$ 5.239,59 em 1. *(ubíquo)*
- **RF-20** — O sistema deve devolver a mesma soma nos cinco eixos para o mesmo
  período: −R$ 103.772,33, idêntico ao centavo, agregando por grupo, categoria,
  beneficiário, natureza ou essencialidade. *(ubíquo)*
- **RF-21** — O sistema deve manter receita fora de todo agregado de gasto: no
  período de 01/03/2026 a 31/08/2026 a receita de R$ 99.231,49 não aparece em
  linha nenhuma dos cinco eixos, e nenhuma linha de gasto tem valor positivo.
  *(ubíquo)*
- **RF-22** — O sistema deve derivar do banco, em tempo de consulta, todo total e
  toda contagem que a tela mostra: nenhum arquivo de `app/` traz
  −R$ 103.772,33, 732, 52, 317 ou −R$ 19.217,11 como literal. Esses números vivem
  nos testes, que medem o banco carregado a partir da fonte de 05/09/2026.
  *(ubíquo)*
- **RF-23** — Se a consulta chega com data final anterior à inicial, ou com data
  que não é data, então o sistema deve recusá-la com mensagem que nomeia o campo
  inválido e não devolver agregado nenhum. *(comportamento indesejado)*
- **RF-24** — Se a consulta chega com eixo fora dos cinco, então o sistema deve
  recusá-la com mensagem que nomeia o eixo recebido e lista os aceitos.
  *(comportamento indesejado)*

### Cruzamentos, evolução e drill-down

- **RF-25** — O sistema deve devolver o cruzamento variável × supérfluo como
  lista ordenada do maior gasto para o menor, com o total do período — a lista
  de corte. *(ubíquo)*
- **RF-26** — O sistema deve devolver o cruzamento fixa × essencial com o total
  do período e a média mensal — o piso de sobrevivência. *(ubíquo)*
- **RF-27** — O sistema deve devolver a evolução como série de 13 meses
  terminando no mês final do período selecionado, com um ponto por mês; para a
  série que termina em 08/2026, o ponto de 08/2026 vale −R$ 19.217,11. *(ubíquo)*
- **RF-28** — Se um mês da série não tem lançamento de gasto, então o sistema
  deve devolver o ponto com valor zero e mantê-lo na série, nunca omitir o mês:
  buraco invisível numa série temporal mente sobre a tendência. *(comportamento
  indesejado)*
- **RF-29** — Quando uma linha de agregado de qualquer eixo é aberta, o sistema
  deve listar as transações que a compõem, cada uma com data, descrição, conta e
  valor: a linha `School` do período de 01/03/2026 a 31/08/2026 abre 20
  transações. *(dirigido a evento)*
- **RF-30** — O sistema deve devolver na lista aberta uma soma igual, ao centavo,
  ao valor da linha de origem: as 20 transações de `School` somam
  −R$ 12.992,18. *(ubíquo)*

### Tela de Gastos

- **RF-31** — Quando `GET /gastos` chega com sessão válida, o sistema deve
  responder 200 com o seletor dos cinco eixos, o seletor de período e a
  agregação do período padrão — os seis meses fechados mais recentes, que em
  05/09/2026 são 01/03/2026 a 31/08/2026, com total −R$ 103.772,33 em 732
  lançamentos. *(dirigido a evento)*
- **RF-32** — Quando o eixo é trocado na tela, o sistema deve substituir apenas o
  fragmento da tabela de agregação, preservando o período selecionado e a
  posição de rolagem. *(dirigido a evento)*
- **RF-33** — Quando o período é trocado na tela, o sistema deve recalcular a
  tabela de agregação, os dois cruzamentos e a série de 13 meses, preservando o
  eixo selecionado. *(dirigido a evento)*
- **RF-34** — O sistema deve exibir na tela de Gastos o resíduo do período —
  quantos lançamentos e quanto dinheiro caíram em `Outros` por falta de regra —
  com um caminho direto para a tela de Regras. *(ubíquo)*
- **RF-35** — O sistema deve exibir na tela de Gastos os dois cruzamentos,
  variável × supérfluo e fixa × essencial, cada um com seu total do período.
  *(ubíquo)*
- **RF-36** — Quando uma linha da tabela de agregação é acionada, a tela deve
  abrir a lista de transações daquela linha sem trocar de página e sem perder o
  eixo, o período nem os cruzamentos já renderizados. *(dirigido a evento)*
- **RF-37** — Se o período selecionado não tem lançamento de gasto, então a tela
  deve mostrar um estado vazio que diz o que aconteceu e qual é o próximo ato —
  escolher outro período —, nunca uma tabela sem linhas. *(comportamento
  indesejado)*
- **RF-38** — Se o gráfico da evolução não carrega, então a tela deve mostrar os
  13 pontos da série em forma legível de tabela, com mês e valor, sem espaço
  vazio: o gráfico vem de CDN e a tela não depende de rede para ser lida.
  *(comportamento indesejado)*
- **RF-48** — Enquanto nenhuma regra tem essencialidade `supérfluo`, o bloco da
  lista de corte deve dizer que nada foi marcado como supérfluo ainda, apontar a
  tela de Regras como próximo ato e listar as cinco maiores categorias de
  `variável × importante` do período como candidatas — no período de 01/03/2026
  a 31/08/2026, `Services` −R$ 8.774,12, `Transfers` −R$ 6.220,71,
  `Transfer - Bank Slip` −R$ 5.239,59, `Transfer - PIX` −R$ 4.685,15 e
  `Eating out` −R$ 4.360,13. Um bloco vazio, ou um total zero sem explicação, é
  o que faz a tela mais importante do item nascer muda. *(dirigido a estado)*

### Tela de Regras

- **RF-39** — Quando `GET /regras` chega com sessão válida, o sistema deve
  responder 200 com a lista das regras de `category_rules`, cada uma com o
  casamento que aplica, o grupo, a natureza, a essencialidade e quantos
  lançamentos ela alcança hoje. *(dirigido a evento)*
- **RF-40** — Quando uma regra é criada, editada ou removida na tela, o sistema
  deve gravar a mudança e confirmar na própria tela quantos lançamentos foram
  reclassificados, e a consulta seguinte da tela de Gastos reflete o novo
  resultado. *(dirigido a evento)*
- **RF-41** — Enquanto o resíduo é maior que zero, a tela de Regras deve exibir
  no topo as categorias e os beneficiários sem regra, ordenados pelo dinheiro
  que carregam, para o dono corrigir onde importa primeiro. *(dirigido a estado)*
- **RF-42** — Se a expressão de uma regra não compila, então o sistema deve
  recusar a gravação com mensagem que aponta a expressão recebida, sem alterar
  nenhuma regra existente e sem reclassificar nada. *(comportamento indesejado)*
- **RF-43** — Se uma regra é removida, então o sistema deve reclassificar os
  lançamentos que ela alcançava pelas regras restantes, e os que sobrarem sem
  regra caem no resíduo de RF-12, contados na tela. *(comportamento indesejado)*

### Interface das duas telas

- **RF-44** — O sistema deve renderizar as telas de Gastos e de Regras com os
  tokens declarados em `product/00-linguagem-visual.md` e definidos em
  `app/static/css/tokens.css`, nos dois temas, com `tabular-nums` em toda cifra e
  o sinal `−` colado ao valor negativo; nenhum template deste item traz cor em
  hexadecimal, `rgb()` ou `hsl()`. *(ubíquo)*
- **RF-45** — O sistema deve renderizar as duas telas em 375, 768 e 1440 px sem
  rolagem horizontal do corpo, com a captura de cada largura em `06-capturas/`.
  *(ubíquo)*
- **RF-46** — Enquanto um elemento interativo das duas telas tem o foco do
  teclado, o sistema deve desenhar um contorno visível de ao menos 2 px em volta
  dele. *(dirigido a estado)*
- **RF-47** — Enquanto o navegador declara `prefers-reduced-motion: reduce`, o
  sistema deve entregar as duas telas sem animação e sem transição, com o estado
  final preservado. *(dirigido a estado)*

## Métrica de sucesso

| Métrica | Onde se observa | Alvo |
|---|---|---|
| Os cinco eixos reparticionam o mesmo total | consulta ao `data/dash.sqlite`, período 01/03/2026 a 31/08/2026 | −R$ 103.772,33 em 732 lançamentos, idêntico ao centavo nos cinco eixos |
| Nenhum gasto fica fora da taxonomia | consulta ao `data/dash.sqlite` | zero lançamentos sem grupo, natureza e essencialidade |
| O piso de sobrevivência do mês passa a ter um número | cruzamento fixa × essencial na tela de Gastos | uma média mensal em reais, comparável ao comprometimento fixo de R$ 6.563,57/mês registrado em `docs/plano.md` |

## Restrições herdadas

Da norma do projeto (`CLAUDE.md`), de `docs/plano.md` e do item `001`:

- **Valor em centavos inteiros, negativo = dinheiro saindo** (invariante 22). A
  agregação soma `amount_cents`; formatação em reais é da apresentação.
- **Transferência entre contas próprias e estorno não entram no total de gasto**
  (invariante 25). As flags já existem: o `001` gravou 152 linhas
  `is_transfer = 1` e 9 `is_refund = 1` (RF-14, RF-15 e RF-16 daquele item), e
  este item as consome sem recalcular heurística.
- **O que só o humano sabe é parâmetro editável na tela, nunca constante no
  código** (invariante 26). Aqui isso é a taxonomia inteira: a essencialidade de
  cada categoria é julgamento do dono, e ela mora em `category_rules`.
- **Cálculo financeiro é código determinístico, nunca IA** (invariante 23).
  Classificação e agregação são função testada; o item `009` explica, não soma.
- **Login antes de qualquer rota que devolva dado** (invariante 24). A guarda do
  `001` já cobre as rotas deste item: página sem sessão responde 302 para
  `/login` (RF-26 do `001`), rota `/api/*` responde 401 sem valor de conta no
  corpo (RF-27). Nada disso se reescreve aqui.
- **Antes de escrever as telas, carregar a skill `frontend-design`** (invariante
  27), e `product/00-linguagem-visual.md` é o documento canônico de interface:
  paleta, escala, raio, foco e movimento saem dele, não de preferência da
  sessão.
- **Números congelados em 05/09/2026** (invariante 28). Eles aparecem em
  requisito e em teste, medindo o banco carregado da fonte daquela data; a base
  cresce, e um número dentro do código de produção faria a consulta do mês
  seguinte falhar por estar certa.
- **Sem dependência não declarada** (15). Chart.js entra por CDN, se entrar, e a
  tela permanece legível sem ele (RF-38). **Zero comentário exceto o porquê que
  o código não mostra** (11), **sem TODO** (12), **código em inglês, documentos e
  interface em pt-BR** (16).

Das decisões autônomas deste item (`decisoes-autonomas.md`), que este brief
assume e não reabre: **D1** — beneficiário derivado da descrição normalizada,
gravado em `transactions.payee` por migração nova; **D2** — seed conservador,
`importante` na dúvida, nunca `supérfluo`; **D3** — trilha rápida.

## Riscos

- **O seed conservador deixa a lista de corte quase vazia no primeiro dia.** Por
  construção: nenhuma categoria nasce `supérfluo`. Resposta: a tela de Regras é
  o lugar de corrigir, e a revisão das 77 categorias já está registrada em
  `decisoes-autonomas.md` como o que ficou para o humano. Enquanto ela não
  acontece, o cruzamento variável × supérfluo mostra pouco — e mostra isso
  explicitamente, em vez de fingir uma lista.
- **O beneficiário derivado da descrição pode agrupar demais ou de menos.** A
  descrição normalizada junta o que o banco escreveu igual, não o que é o mesmo
  fornecedor. Resposta: no período medido ela reproduz o topo do relatório de
  origem dígito a dígito (−R$ 12.358,81 em 5 lançamentos), e quando um caso
  quebrar, o conserto é regra na tabela, não código.
- **Regra por expressão sobre a descrição fica cara conforme a base cresce.** O
  SQLite não tem regex nativo, e a classificação roda em lote fora do banco.
  Resposta: o resultado é materializado na linha do lançamento e a consulta de
  agregação lê coluna indexada; só a gravação de regra paga o custo, e ela é
  ato do usuário, não caminho de leitura.
- **Duas regras podem alcançar o mesmo lançamento.** Resposta: RF-11 fixa a
  ordem — descrição antes de categoria, `id` crescente dentro do tipo, primeira
  que casa vence —, o que torna o resultado reproduzível e explicável na tela de
  Regras.
- **Os números medidos envelhecem no primeiro sync do item `006`.** Resposta:
  RF-22 mantém todo total fora do código de produção; os testes medem o banco
  carregado da fonte de 05/09/2026, e é a fonte que fixa o número, não o
  produto.
- **Duas telas novas sem revisor de norma de código para Python.** É o atalho
  declarado em `docs/plano.md`. Resposta: `frontend-design` e
  `product/00-linguagem-visual.md` cobrem o lado da interface, e RF-44 a RF-47
  são verificáveis por teste e por captura, não por opinião.
