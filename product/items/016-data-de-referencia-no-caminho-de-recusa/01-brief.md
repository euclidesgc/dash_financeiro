# Brief — 016-data-de-referencia-no-caminho-de-recusa

**Item:** `016-data-de-referencia-no-caminho-de-recusa` · **Trilha:** rápida

> Este documento funde PRD e spec. O que a trilha rápida corta é documentação,
> nunca verificação: critério tipado, reviewer de stack e validador cego valem
> igual.

## Problema

O painel tem uma data de referência do processo — `reference_date()`, em
`app/config.py:55-60`, que lê `DASH_TODAY` e é quem faz duas execuções sobre a
mesma base responderem igual. Nenhuma tela a usa. Cada rota reimplementa o seu
leitor de data e os seis sítios caem em `date.today()`:
`app/routers/summary.py:82-90`, `app/routers/commitments.py:76-82`,
`app/routers/plan.py:43-64`, `app/routers/whatif.py:90-95`,
`app/routers/advisor.py:90-95` e `app/routers/spending.py:92-104`, este pela
janela padrão. O dono vê um painel e um relatório regerável que discordam da
data, e "vencido" significa coisas diferentes nos dois.

`DASH_TODAY` é a afordância de reprodutibilidade de que o método inteiro
depende: é por ela que um plano, um critério ou um validador compara o painel
com os números congelados de `docs/plano.md`, medidos em 05/09/2026 (norma 28 do
`CLAUDE.md`). Como nenhum dos seis sítios a consulta, todo critério que compare
uma tela com um número congelado mede contra o relógio real, e passa ou reprova
conforme o dia em que roda. É o que dá o tamanho do item: enquanto isso vale,
nenhuma tela do painel é verificável contra a referência congelada.

Três consequências, medidas por execução com `DASH_TODAY=2026-09-05` e o relógio
em `2026-09-07`:

- **O caminho de recusa é o caminho normal.** `day(None, "data")` levanta
  `InvalidPeriodError` (`app/queries/period.py:16-19`), então entrar na tela pelos
  próprios links do painel, sem `?data=`, desce pelo ramo de recusa. `GET /`
  sem query string imprime `id="recusa"` com o texto `data inválida: data (None)`
  — a primeira coisa que o dono vê ao abrir o painel é um alerta vermelho sobre
  uma data que ele não digitou.
- **Data ISO fora do calendário derruba duas rotas.** `GET /?data=0001-01-01` e
  `GET /comprometido?data=0001-01-01` levantam `ValueError: year 0 is out of range`
  em `app/queries/period.py:45-52`. A faixa que `app/routers/plan.py:43-44` já
  usa para o mesmo defeito nunca chegou às outras duas rotas, porque não havia
  lugar comum onde pô-la.
- **Três telas recusam em silêncio.** `/comprometido`, `/simulador` e
  `/consultor` respondem por uma data diferente da pedida sem dizer nada.
  `/` e `/objetivo` já dizem (`app/templates/resumo.html:16-17`,
  `app/templates/objetivo.html:8`).

Nenhum teste fixa `DASH_TODAY` e afirma qual data uma rota renderizou. Os
auxiliares de teste de tela passam `?data=` explícito sempre
(`tests/test_resumo_screen.py:24`), então o caminho sem parâmetro nunca foi
exercido.

## Escopo

Toda tela do painel responde pela data de referência do processo — inclusive
quando o dono não pede data nenhuma, e inclusive quando a data que ele digitou é
recusada. Existe um leitor só dessa data, e ele é o único caminho. Data que
quebra a aritmética de calendário é recusada com a tela de pé, não com erro de
servidor. E quando uma tela recusa, ela diz.

## Não-escopo

- **`DASH_TODAY` malformado continua derrubando o processo alto.**
  `reference_date()` propaga o `ValueError` cru (`app/config.py:60`), e é o
  comportamento certo: um ambiente mal configurado é erro do operador, não data
  pedida pelo usuário. Responder por um dia qualquer sob uma variável ilegível
  faria toda comparação com os números congelados mentir em silêncio.
- **`app/queries/period.py:shift` não é endurecido.** A faixa entra no leitor
  único, que é onde `/objetivo` já a colocou uma vez. `shift` é biblioteca cujos
  outros chamadores recebem data já validada; blindá-la ali é tratar o sintoma no
  lugar errado e deixar o defeito voltar na próxima rota que nascer.
- **O texto do aviso de recusa não muda.** Ele diz "A tela responde pela data de
  hoje." enquanto a tela passa a responder pela data de referência, e a cópia
  fica: `DASH_TODAY` não existe no `.env` do dono nem no `.env.example` — a
  variável só aparece em planos e roteiros de validação, para reproduzir os
  números congelados de `docs/plano.md`. No painel que o dono roda,
  `reference_date()` é o dia do relógio, e "hoje" é literalmente verdade; a
  divergência só existe dentro de execução de validador, que nenhum humano lê.
  Se algum dia `DASH_TODAY` entrar no `.env` do dono, a cópia passa a mentir e a
  troca vira item de roadmap.
- **`/gastos` não ganha aviso de recusa.** Ela não aceita `data`: aceita `inicio`
  e `fim`, e cai na janela padrão. O aviso de recusa é sobre a data de referência
  da tela, e alinhar o período de `/gastos` é outro assunto, com outra régua.
- **Nenhuma rota ganha ou perde parâmetro, e nenhum número financeiro muda.**
  Este item move qual data o cálculo recebe, nunca como ele calcula.

## Requisitos

### A data que toda tela usa

- **RF-01** — O sistema deve resolver a data de referência de tela por um único
  leitor compartilhado, e nenhuma rota deve resolver a sua própria: nenhuma
  função de `app/routers/` que decide a data de uma tela chama `date.today()`.
  São **seis sítios de código** — `summary`, `commitments`, `plan`, `whatif`,
  `advisor` e `spending` —, contagem distinta das **cinco telas** de RF-02, que
  é quantas renderizam a data no HTML.
- **RF-02** — O sistema deve responder pela data de referência do processo nas
  cinco telas que renderizam data de referência — `/`, `/comprometido`,
  `/objetivo`, `/simulador` e `/consultor` — sempre que não há data pedida e
  aceita. Com `DASH_TODAY=2026-09-05` e o relógio em `2026-09-07`, as cinco
  telas renderizam `2026-09-05`. `/gastos` não imprime a data de referência em
  lugar nenhum do seu HTML — imprime a janela de período — e é governada por
  RF-13.
- **RF-03** — Enquanto `DASH_TODAY` não está definido no ambiente, a data de
  referência é o dia corrente do relógio, e quem decide isso é `reference_date()`,
  não a rota.

### Pedir uma data, e não pedir nenhuma

- **RF-04** — Quando uma tela é aberta sem o parâmetro `data`, o sistema deve
  responder pela data de referência **sem** exibir aviso de recusa: `GET /` sem
  query string não traz nenhum elemento `id="recusa"`.
- **RF-05** — Quando o parâmetro `data` chega presente e vazio, o sistema deve
  tratá-lo como ausência de pedido: `GET /?data=` responde 200, sem aviso, pela
  referência `2026-09-05`.
- **RF-06** — Quando a data pedida é legível e está entre `2000-01-01` e
  `2100-12-31`, o sistema deve responder por ela: `GET /?data=2100-12-31` é
  aceita. A faixa recusa o que quebra a aritmética de mês, não o que é distante.

### Quando a data é recusada

- **RF-07** — Se a data pedida é ilegível, então o sistema deve responder 200
  pela data de referência e exibir o aviso de recusa: `GET /?data=banana`,
  `GET /simulador?data=banana`, `GET /consultor?data=banana` e
  `GET /comprometido?data=banana` respondem por `2026-09-05` com o aviso.
- **RF-08** — Se a data pedida é legível mas está fora da faixa, então o sistema
  deve responder 200 pela data de referência e exibir o aviso de recusa, nunca
  500: `GET /?data=0001-01-01` e `GET /comprometido?data=0001-01-01` devolvem 200
  por `2026-09-05`.
- **RF-09** — O sistema deve marcar o aviso de recusa com `id="recusa"` nas cinco
  telas que aceitam `data`: `/`, `/comprometido`, `/objetivo`, `/simulador` e
  `/consultor`.

### O que a data de referência decide

- **RF-10** — O sistema deve decidir se um fato está vencido comparando o
  `valid_until` dele com a data de referência da leitura. Fato com
  `valid_until = 2026-09-06` e `DASH_TODAY=2026-09-05` não aparece vencido em
  `GET /simulador` sem query string.
- **RF-11** — Enquanto a tela de resumo responde pela data de referência, o
  sistema deve omitir a ressalva de que a posição é sempre a atual e a data
  pedida move só a projeção. Com `DASH_TODAY=2026-09-05` e nenhuma data pedida,
  `GET /` não imprime a ressalva.
- **RF-12** — Quando a tela de resumo responde por uma data pedida e aceita,
  diferente da data de referência, o sistema deve imprimir a ressalva de posição.
- **RF-13** — Quando `/gastos` é aberta sem `inicio` e sem `fim`, o sistema deve
  calcular a janela padrão a partir da data de referência: a janela termina no
  último mês fechado antes dela, e não antes do dia do relógio.
- **RF-14** — Quando `/objetivo` responde por uma data aceita ou por ausência de
  pedido, o sistema deve gravar ponto na linha do tempo.
- **RF-15** — Se a data pedida a `/objetivo` é recusada, então o sistema **não**
  deve gravar ponto na linha do tempo: um erro de digitação na URL injetaria um
  ponto que depois não se distingue de uma leitura real.

## Métrica de sucesso

| Métrica | Onde se observa | Alvo |
|---|---|---|
| Telas que renderizam data diferente da referência | Sonda das cinco telas que imprimem a data de referência — `/`, `/comprometido`, `/objetivo`, `/simulador`, `/consultor` — com `DASH_TODAY=2026-09-05` e relógio em outro dia | 0 de 5 |
| Aviso de recusa na navegação sem `?data=` | `GET /` sem query string | ausente |
| Rotas que devolvem 500 para data ISO fora do calendário | `GET /?data=0001-01-01` e `GET /comprometido?data=0001-01-01` | 0 de 2 |

## Riscos

- **A adoção do leitor único regride `/objetivo`, que hoje já está certo.**
  `app/routers/plan.py:56-64` distingue três saídas, não duas: data aceita,
  ausência de pedido e recusa — e grava ponto nas duas primeiras
  (`app/routers/plan.py:34-35`). Um leitor que devolva só `(data, recusou?)`
  colapsa ausência com aceitação ou com recusa, e nos dois casos a linha do tempo
  quebra. Resposta: o leitor devolve as três saídas, e o teste que fixa o
  comportamento de `/objetivo` entra antes da troca, não depois.
- **Os testes de tela mascaram a regressão que este item mais arrisca.** O
  auxiliar passa `?data=` explícito sempre (`tests/test_resumo_screen.py:24`), e
  o caminho sem parâmetro — o que RF-04 governa — nunca foi exercido. Resposta:
  os testes novos chamam a rota sem o parâmetro, sem passar pelo auxiliar.
- **`/` e `/comprometido` ganham uma faixa que hoje não têm, e faixa nova recusa
  o que antes passava.** Resposta: a faixa é a mesma que `/objetivo` já usa
  (`app/routers/plan.py:43-44`), `2000-01-01` a `2100-12-31`; RF-06 fixa
  `2100-12-31` como aceita, de modo que o limite fica verificado e não
  presumido.
