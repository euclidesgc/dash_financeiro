# Discovery — 002-gastos-tres-eixos

**Item do roadmap:** `002-gastos-tres-eixos` — Os gastos se leem por grupo,
categoria, beneficiário, **natureza** (fixa · variável · eventual) e
**essencialidade** (essencial · importante · supérfluo), em qualquer período,
com drill-down até a transação. O cruzamento variável × supérfluo é a lista de
corte; fixa × essencial é o piso de sobrevivência. As regras de classificação
são tabela editável na tela, não código.

**Data:** 2026-09-06

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim | Depende só do `001`, que está concluído: o banco tem os 1.942 lançamentos com sinal normalizado e as flags de transferência e estorno. |
| Negociável | sim | Fixo: os cinco eixos, os dois cruzamentos e a classificação como tabela. Conversável: como o beneficiário é derivado, qual o mapeamento inicial das 77 categorias, como a tela apresenta a evolução. |
| Valioso | sim | É a primeira tela que responde uma pergunta que muda decisão: onde cortar sem virar monge. Sem os três eixos, o painel só sabe dizer "você gastou R$ 103.772,33". |
| Estimável | sim | Quatro fases: taxonomia e motor · consultas de agregação · tela de gastos · tela de regras. |
| Pequeno | sim | Cada fase toca no máximo duas famílias de prova, e nenhuma depende de terceiro. |
| Testável | sim | Todo agregado se compara com número congelado em 05/09/2026, reproduzido pela fonte que já está no banco. |

**Veredicto do INVEST:** segue como está.

## História

Como dono deste painel, quero ler meus gastos por grupo, categoria,
beneficiário, natureza e essencialidade, em qualquer período, e descer de
qualquer agregado até a transação que o compõe, para descobrir onde cortar sem
cortar o que sustenta a casa.

## Regras e exemplos

### R1 — Os cinco eixos leem o mesmo período, e qualquer um deles pode agrupar

- **E1.1** — Período de 01/03/2026 a 31/08/2026, eixo **categoria**: `School`
  no topo com −R$ 12.992,18 em 20 lançamentos, `Real estate financing` em
  seguida com −R$ 12.358,81 em 5, e o total do período é −R$ 103.772,33 em 732
  lançamentos, distribuídos em 52 categorias.
- **E1.2** — O mesmo período, eixo **beneficiário**: `débito prestação
  habitacional` no topo com −R$ 12.358,81 em 5 lançamentos, e `pagamento de
  boleto sociedade de assistência` em seguida com −R$ 10.880,05 em 7.
- **E1.3** — O mesmo período, eixo **natureza** ou **essencialidade**: a soma
  das linhas devolvidas é exatamente −R$ 103.772,33, em qualquer eixo. Trocar o
  eixo reparticiona o mesmo total; nunca muda o total.

### R2 — A classificação é tabela, não código

- **E2.1** — `category_rules` casa por categoria da Pluggy ou por expressão
  sobre a descrição, e cada regra declara grupo, natureza e essencialidade.
  Mudar a essencialidade de `Eating out` de `importante` para `supérfluo` na
  tela reclassifica os 128 lançamentos daquela categoria, sem reingestão e sem
  reiniciar o processo.
- **E2.2** — Nenhum nome de categoria, grupo, natureza ou essencialidade aparece
  como literal dentro de uma condição no código de consulta: a consulta lê a
  tabela.

### R3 — O vocabulário dos três eixos é fechado

- **E3.1** — Os grupos são exatamente dez: Moradia, Educação, Transporte,
  Alimentação, Comer fora e lazer, Saúde, Serviços e assinaturas, Dívidas e
  juros, Transferências, Outros.
- **E3.2** — A natureza é uma de três: fixa, variável, eventual. A
  essencialidade é uma de três: essencial, importante, supérfluo.
- **E3.3** — Uma regra que declare grupo, natureza ou essencialidade fora dessas
  listas é recusada na gravação, com mensagem que nomeia o valor inválido.

### R4 — Todo lançamento de gasto tem os três eixos, e o que não casa aparece

- **E4.1** — Os dados trazem 77 categorias distintas — 74 vindas da Pluggy e o
  resto inferido na consolidação, com 21 lançamentos de categoria inferida e 15
  em `Não classificado`. Depois da carga da taxonomia, **nenhum** lançamento
  fica sem grupo, natureza e essencialidade.
- **E4.2** — O que nenhuma regra alcança cai no grupo `Outros` com natureza
  `eventual` e essencialidade `importante`, e a tela mostra quantos lançamentos
  e quanto dinheiro estão nesse balde — porque um resíduo silencioso é um
  resíduo que ninguém corrige.

### R5 — O total nunca conta o que não é gasto

- **E5.1** — O total do período exclui transferência entre contas próprias,
  pagamento de fatura e estorno, que o item `001` já marcou: as 152 linhas com
  `is_transfer = 1` e as 9 com `is_refund = 1` ficam fora, em todo eixo.
- **E5.2** — PIX e boleto para terceiros **são** gasto e entram: no período,
  `Transfer - PIX` soma −R$ 4.685,15 em 58 lançamentos e
  `Transfer - Bank Slip` soma −R$ 5.239,59 em 1.

### R6 — De qualquer agregado se chega à transação

- **E6.1** — Clicar na linha `School` do período de 01/03/2026 a 31/08/2026
  lista as 20 transações que somam −R$ 12.992,18, cada uma com data, descrição,
  conta e valor.
- **E6.2** — A soma dos valores da lista aberta é igual, ao centavo, ao valor da
  linha de onde ela foi aberta.

### R7 — Os dois cruzamentos que decidem

- **E7.1** — O cruzamento **variável × supérfluo** devolve a lista de corte,
  ordenada por valor, com o total do período — é a resposta a "onde cortar sem
  virar monge".
- **E7.2** — O cruzamento **fixa × essencial** devolve o piso de sobrevivência
  do mês, que é o número que dimensiona a reserva do item `007`.

### R8 — A evolução mostra treze meses

- **E8.1** — A série de 13 meses até 08/2026 traz um ponto por mês, e o ponto de
  08/2026 vale −R$ 19.217,11 — a despesa daquele mês, igual à do relatório de
  origem.
- **E8.2** — Mês sem lançamento aparece como zero, não some da série: buraco
  invisível numa série temporal mente sobre a tendência.

## Perguntas em aberto

Nenhuma.

Duas dúvidas apareceram e nenhuma delas é pergunta para o dono:

1. **Como o beneficiário é derivado.** A consolidação já produz uma descrição
   normalizada, e agrupar por ela reproduz o "top beneficiários" do relatório de
   origem, dígito a dígito. É decisão técnica, registrada em
   `decisoes-autonomas.md`.
2. **Qual a essencialidade inicial de cada uma das 77 categorias.** Isto seria
   pergunta para o dono se fosse constante no código — mas o próprio item manda
   que seja tabela editável na tela. O seed é um palpite declarado, conservador
   (na dúvida, `importante`, nunca `supérfluo`), e a tela é o lugar de corrigir.
   Marcar algo como supérfluo por conta própria seria o painel decidindo o que a
   família dele pode cortar.

## Trilha

**Trilha: rápida.**

| Gatilho | Verdadeiro | Evidência |
|---|---|---|
| Zero perguntas em aberto | sim | Nenhuma pergunta sobrou; as duas dúvidas viraram decisão registrada. |
| Uma stack só | sim | Python 3.12 servindo HTML por Jinja2 e fragmentos HTMX; sem segundo runtime. |
| Sem mudança de contrato | sim | Não há OpenAPI versionado nem consumidor externo; as rotas servem o próprio app. |
| Sem dependência nova | sim | Tudo que o item precisa já está no `pyproject.toml` desde o `001`. Chart.js, se a evolução pedir gráfico, entra por CDN e não por dependência de build — e a tela precisa continuar legível sem ele. |

Os quatro gatilhos são verdadeiros, e a decisão do dono para este item, tomada
antes da corrida, também é a trilha rápida. Régua e decisão coincidem.
