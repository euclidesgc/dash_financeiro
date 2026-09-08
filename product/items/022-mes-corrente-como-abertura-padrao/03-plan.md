# Plano — 022-mes-corrente-como-abertura-padrao

**Item:** `022-mes-corrente-como-abertura-padrao` · **Trilha:** rápida ·
**Fonte aprovada:** `01-brief.md` (RF-01 a RF-08) · **Terreno:**
`00-discovery.md` · Uma fase, uma branch integrada em `develop`.

> **Nenhum número da base do dono entra em critério deste plano.** Os valores
> que os critérios cobram são de uma base de trabalho vazia que o próprio teste
> carrega, com seis lançamentos escritos à mão: a medição vale dentro de uma
> worktree recém-criada, onde `data/dash.sqlite` não existe, e não se compara
> com relatório regerável (invariante 28). As citações de arquivo e linha foram
> lidas no repositório neste commit.
>
> Duas armadilhas medidas nesta máquina e já embutidas nos critérios: todo
> comando leva `DASH_ENV_FILE=/dev/null` no ambiente, porque um hook nega
> comando que leia `.env`; e o código de saída se lê do próprio `pytest`, nunca
> através de cano para `tail`, que devolve o exit do `tail`.

## Objetivo

Ao fim da fase `/gastos` abre no mês corrente — do dia 01 do mês da data de
referência até a própria data de referência, inclusive — e responde pela data
pedida em `?data=`, com os mesmos três estados que as outras cinco telas já
têm. As duas consequências da troca ficam ditas na tela: o que já está postado
no mês depois da data de referência é nomeado em lançamentos e em dinheiro sem
entrar em total nenhum, e o valor por cruzamento só se chama "média mensal"
quando a janela cobre meses inteiros.

É **uma** fase porque não há quebra de contrato entre partes: a janela padrão,
a linha do que está adiante e o rótulo do cruzamento são três leituras da mesma
janela, decidida num só ponto (`_selection`), e cortar a fase em duas entregaria
uma tela que abre no mês corrente afirmando "média mensal" sobre cinco dias —
exatamente o defeito que o item existe para não criar.

## O terreno, lido no código

| Sítio | Hoje | O que falta |
|---|---|---|
| `app/routers/spending.py:98` | `default_period(screen_date(None).date)`: o `None` é literal e descarta o `?data=` | ler o parâmetro pelo leitor único e tirar a janela da data que ele devolve |
| `app/queries/period.py:41-47` | seis meses fechados, terminando no último dia do mês anterior | do dia 01 do mês da referência até a referência |
| `app/queries/crossings.py:46,50-52` | `monthly_average_cents` divide o total pelos meses de calendário que a janela toca | nada neste módulo: quem passa a decidir o rótulo é a janela, uma vez por painel |
| `app/templates/gastos.html:14-45` | cabeçalho sem bloco de recusa; formulário `#controles` sem campo `data` | `id="recusa"` e o campo oculto que faz a data pedida voltar no submit |
| `app/templates/fragments/gastos_tabela.html:5-9,40-45` | o total do período, e a cópia do vazio que manda "voltar aos seis meses fechados" | a linha do que está postado adiante, e a cópia do mês corrente |
| `app/templates/fragments/gastos_painel.html:45` | `Média mensal de …`, fixo | rótulo e número decididos pela janela |
| `tests/test_period.py:13-38` | afirmam a janela de seis meses fechados e o parâmetro `months` | afirmam o mês corrente, `month_end` e `covers_whole_months` |
| `tests/test_gastos_screen.py:116-125,307-322` | afirmam a abertura em seis meses fechados | afirmam a abertura no mês corrente |

Dois fatos decidem o desenho e não se re-discutem. `app/plan/objective.py:34-35`
e `:73-75` leem `monthly_average_cents` e montam sempre janela de meses
inteiros (`f"{months[0]}-01"` até `_last_day(months[-1])`); o arquivo pertence a
outro item em execução e este não o toca, então o campo do `Crossing` não muda
de nome nem de tipo. E `app/queries/axes.py:54-61::aggregate` já cobra
`check_period` sobre a janela, então uma janela padrão inválida derruba a tela
inteira, não só um bloco — a janela nova precisa nascer válida em todo dia do
calendário, inclusive no dia 01, quando início e fim são o mesmo dia.

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | O que decidiu | Decisão |
|---|---|---|
| A janela padrão vira função nova ou `default_period` muda no lugar? | `default_period` tem um consumidor só, `app/routers/spending.py:98`, e os testes | muda no lugar, sem nome novo |
| `CLOSED_MONTHS` e o parâmetro `months` ficam? | nenhum módulo fora de `tests/test_period.py` os lê | saem: parâmetro sem consumidor é uma segunda janela padrão que ninguém exercita |
| Onde mora a soma do que está postado adiante? | norma 33 mantém agregação em SQL sob `app/queries`, e norma 30 mantém o router fora da consulta | módulo novo `app/queries/ahead.py` |
| "Lançamentos" da linha do RF-06 são todos, ou só gasto? | a tela é de gasto e todo total dela já exclui transferência e estorno (invariante 25) | só gasto, pelo mesmo filtro `SPENDING` de `app/queries/spending.py:8` |
| Quando a linha do que está adiante aparece? | a frase afirma que aqueles lançamentos estão **fora** do total; numa janela que já os alcança a frase é falsa | quando há lançamento no intervalo **e** o fim da janela é anterior ou igual à data de referência |
| `app/queries/crossings.py` muda? | `app/plan/objective.py` lê `monthly_average_cents` e este item não pode tocar aquele arquivo | não: o rótulo é propriedade da janela, decidido uma vez por painel |
| Onde mora a pergunta "a janela cobre meses inteiros"? | é aritmética de calendário sobre os dois extremos, como `shift` | `app/queries/period.py::covers_whole_months` |
| `/gastos` ganha campo oculto `data`? | `app/templates/simulador.html` e `app/templates/consultor.html` já carregam `<input type="hidden" name="data">`, e o formulário de `/gastos` é GET para a própria tela | sim, com a data já resolvida |
| A série de treze meses passa a cortar no dia da referência? | `monthly_series` agrupa por mês inteiro, mora em `app/queries/series.py` — fora do que este item toca — e nenhum RF pede | não. Pendência registrada abaixo |
| Alguma migração? | nenhuma tabela muda | não |
| Portão novo em `scripts/gates/`? | quem executa os testes desta fase é `pytest`, que o CI já roda | não: `scripts/gates/` e `scripts/lint.sh` não são tocados |

---

## Fase 1 — A abertura no mês corrente, a data pedida e os dois rótulos (api)

**Objetivo da fase:** `/gastos` abre do dia 01 do mês da data de referência até
a própria data de referência, responde pela data pedida em `?data=`, nomeia o
que já está postado no mês depois dela e só chama de "média mensal" o valor de
uma janela de meses inteiros.

**Critérios de aceite:**

- [ ] `estrutural` — RF-01, RF-02, RF-06
      `app/queries/period.py` define `month_end` e `covers_whole_months` e
      **não** define `CLOSED_MONTHS`; existe `app/queries/ahead.py` exportando
      `posted_ahead` e a classe `Ahead` com os campos `entries` e
      `amount_cents`; `app/routers/spending.py` importa `DATE_FIELD` e
      `screen_date` de `app.routers.reference` e **não** contém a expressão
      `screen_date(None)`; e `app/templates/fragments/gastos_tabela.html` não
      contém a expressão `meses fechados`.

- [ ] `comportamental` — RF-01, RF-04
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null` e `DASH_TODAY=2026-09-05` no ambiente do
      processo, sessão autenticada e uma base de trabalho vazia onde foram
      carregados seis lançamentos de gasto, todos na categoria que a semente da
      taxonomia classifica no cruzamento de piso: `2026-08-20` de −R$ 111,00,
      `2026-09-01` de −R$ 200,00, `2026-09-05` de −R$ 30,00, `2026-09-06` de
      −R$ 40,00, `2026-09-30` de −R$ 62,00 e `2026-10-02` de −R$ 77,00
      *Quando* `GET /gastos` é buscada **sem nenhuma query string**
      *Então* a resposta é `200`, o HTML traz `value="2026-09-01"` e
      `value="2026-09-05"` nos campos `inicio` e `fim` do formulário
      `id="controles"`, contém a frase `2 lançamentos de 01/09/2026 a
      05/09/2026` e a cifra `−R$ 230,00`, e **não** contém `id="recusa"`. Hoje
      a mesma requisição abre em `de 01/03/2026 a 31/08/2026` e traz
      `1 lançamento` com a cifra `−R$ 111,00`, porque a janela é de seis meses
      fechados e o mês em curso fica inteiro de fora

- [ ] `comportamental` — RF-02
      *Dado* o painel servido com `DASH_ENV_FILE=/dev/null` e
      `DASH_TODAY=2026-09-05` no ambiente do processo, sessão autenticada e a
      base de trabalho com os seis lançamentos de gasto `2026-08-20` de
      −R$ 111,00, `2026-09-01` de −R$ 200,00, `2026-09-05` de −R$ 30,00,
      `2026-09-06` de −R$ 40,00, `2026-09-30` de −R$ 62,00 e `2026-10-02` de
      −R$ 77,00
      *Quando* `GET /gastos?data=2026-08-20` é buscada, **sem** `inicio` e
      **sem** `fim`
      *Então* a resposta é `200`, o HTML traz `value="2026-08-01"` e
      `value="2026-08-20"` nos campos `inicio` e `fim`, contém a frase
      `1 lançamento de 01/08/2026 a 20/08/2026` e a cifra `−R$ 111,00`, traz
      `<input type="hidden" name="data" value="2026-08-20">` e **não** contém
      `id="recusa"`. Hoje a data pedida é descartada e a tela responde pela
      janela da data de referência do processo

- [ ] `comportamental` — RF-03
      *Dado* o painel servido com `DASH_ENV_FILE=/dev/null` e
      `DASH_TODAY=2026-09-05` no ambiente do processo, sessão autenticada e a
      base de trabalho com os seis lançamentos de gasto `2026-08-20` de
      −R$ 111,00, `2026-09-01` de −R$ 200,00, `2026-09-05` de −R$ 30,00,
      `2026-09-06` de −R$ 40,00, `2026-09-30` de −R$ 62,00 e `2026-10-02` de
      −R$ 77,00
      *Quando* `GET /gastos?data=banana` é buscada
      *Então* a resposta é `200`, o HTML contém `id="recusa"` com o texto
      `data inválida: data (banana)`, e os campos `inicio` e `fim` trazem
      `value="2026-09-01"` e `value="2026-09-05"` — a tela recusa dizendo, e
      responde pela data de referência do processo. Hoje a tela responde em
      silêncio e nenhum `id="recusa"` é impresso em `/gastos`

- [ ] `comportamental` — RF-05
      *Dado* o painel servido com `DASH_ENV_FILE=/dev/null` e
      `DASH_TODAY=2026-09-05` no ambiente do processo, sessão autenticada e a
      base de trabalho com os seis lançamentos de gasto `2026-08-20` de
      −R$ 111,00, `2026-09-01` de −R$ 200,00, `2026-09-05` de −R$ 30,00,
      `2026-09-06` de −R$ 40,00, `2026-09-30` de −R$ 62,00 e `2026-10-02` de
      −R$ 77,00
      *Quando* `GET /gastos?inicio=2026-08-01&fim=2026-08-31` é buscada e, na
      mesma execução, `GET /gastos?inicio=ontem&fim=2026-08-31`
      *Então* a primeira responde `200` e traz a frase `1 lançamento de
      01/08/2026 a 31/08/2026` com a cifra `−R$ 111,00` — o par explícito vence
      o padrão —, e a segunda responde `200` e traz `value="2026-09-01"` e
      `value="2026-09-05"` nos campos `inicio` e `fim` — o valor ilegível cai
      no padrão em vez de derrubar a tela

- [ ] `comportamental` — RF-06
      *Dado* o painel servido com `DASH_ENV_FILE=/dev/null` e
      `DASH_TODAY=2026-09-05` no ambiente do processo, sessão autenticada e a
      base de trabalho com os seis lançamentos de gasto `2026-08-20` de
      −R$ 111,00, `2026-09-01` de −R$ 200,00, `2026-09-05` de −R$ 30,00,
      `2026-09-06` de −R$ 40,00, `2026-09-30` de −R$ 62,00 e `2026-10-02` de
      −R$ 77,00
      *Quando* `GET /gastos` é buscada sem query string
      *Então* a resposta é `200`; o recorte do HTML que vai de `id="posterior"`
      até o primeiro `</p>` depois dele contém `2 lançamento`, a cifra
      `−R$ 102,00` e a data `05/09/2026`, e **não** contém `77,00`; e a frase
      do total da janela continua sendo `2 lançamentos de 01/09/2026 a
      05/09/2026` com a cifra `−R$ 230,00`. O recorte é declarado porque a
      página inteira traz outras cifras e outras contagens de lançamento; o
      lançamento de outubro é o controle negativo, sem o qual somar o mês
      seguinte passaria despercebido

- [ ] `comportamental` — RF-06
      *Dado* o painel servido com `DASH_ENV_FILE=/dev/null` e
      `DASH_TODAY=2026-09-05` no ambiente do processo, sessão autenticada e a
      base de trabalho com os seis lançamentos de gasto `2026-08-20` de
      −R$ 111,00, `2026-09-01` de −R$ 200,00, `2026-09-05` de −R$ 30,00,
      `2026-09-06` de −R$ 40,00, `2026-09-30` de −R$ 62,00 e `2026-10-02` de
      −R$ 77,00
      *Quando* `GET /gastos?inicio=2026-09-01&fim=2026-09-30` é buscada
      *Então* a resposta é `200`, o HTML **não** contém `id="posterior"`, e a
      frase do total é `4 lançamentos de 01/09/2026 a 30/09/2026` com a cifra
      `−R$ 332,00` — numa janela que já alcança os lançamentos, dizer que eles
      estão fora do total seria mentira, e os quatro somam

- [ ] `comportamental` — RF-07
      *Dado* o painel servido com `DASH_ENV_FILE=/dev/null` e
      `DASH_TODAY=2026-09-05` no ambiente do processo, sessão autenticada e a
      base de trabalho com os seis lançamentos de gasto `2026-08-20` de
      −R$ 111,00, `2026-09-01` de −R$ 200,00, `2026-09-05` de −R$ 30,00,
      `2026-09-06` de −R$ 40,00, `2026-09-30` de −R$ 62,00 e `2026-10-02` de
      −R$ 77,00, todos na categoria que a semente da taxonomia classifica no
      cruzamento de piso
      *Quando* `GET /gastos?inicio=2026-08-20&fim=2026-09-05` é buscada — uma
      janela que toca dois meses de calendário sem cobrir nenhum inteiro
      *Então* a resposta é `200` e o recorte do HTML que vai de
      `id="cruzamentos"` até `id="residuo"` contém a expressão `No período` e a
      cifra `−R$ 341,00`, e **não** contém a expressão `Média mensal` nem a
      cifra `−R$ 170,50`. A cifra ausente é o total dividido pelos dois meses
      de calendário que a janela toca, que é o que a tela imprime hoje sob o
      rótulo de média mensal

- [ ] `comportamental` — RF-07, RF-08
      *Dado* o painel servido com `DASH_ENV_FILE=/dev/null` e
      `DASH_TODAY=2026-09-05` no ambiente do processo, sessão autenticada e a
      base de trabalho com os seis lançamentos de gasto `2026-08-20` de
      −R$ 111,00, `2026-09-01` de −R$ 200,00, `2026-09-05` de −R$ 30,00,
      `2026-09-06` de −R$ 40,00, `2026-09-30` de −R$ 62,00 e `2026-10-02` de
      −R$ 77,00, todos na categoria que a semente da taxonomia classifica no
      cruzamento de piso
      *Quando* `GET /gastos?inicio=2026-03-01&fim=2026-08-31` é buscada — seis
      meses inteiros, a forma de janela sobre a qual os números congelados de
      `docs/plano.md` foram medidos
      *Então* a resposta é `200` e o recorte do HTML que vai de
      `id="cruzamentos"` até `id="residuo"` contém a expressão `Média mensal` e
      a cifra `−R$ 18,50` — o único lançamento da janela, de −R$ 111,00,
      dividido pelos seis meses que ela cobre, que é o mesmo número de hoje

- [ ] `comando` — RF-01, RF-06, RF-07, RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_period.py tests/test_ahead.py tests/test_crossings.py
      tests/test_gastos_screen.py` sai com código `0`, lido do próprio `pytest`
      e não através de cano para outro comando. `tests/test_period.py` afirma
      `default_period(date(2026, 9, 5)) == ("2026-09-01", "2026-09-05")`,
      `default_period(date(2026, 9, 1)) == ("2026-09-01", "2026-09-01")`,
      `month_end(date(2024, 2, 10)) == date(2024, 2, 29)` e
      `covers_whole_months` verdadeiro para `("2026-03-01", "2026-08-31")` e
      falso para `("2026-03-02", "2026-08-31")` e para
      `("2026-03-01", "2026-08-30")`; `tests/test_ahead.py` afirma que
      transferência entre contas próprias e estorno não entram na contagem nem
      na soma; e `tests/test_crossings.py` segue afirmando que a média mensal
      de `2026-03-01` a `2026-08-31` é o total dividido por seis

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Modificar `app/queries/period.py`: a janela padrão vira o mês
      corrente, e a pergunta sobre meses inteiros nasce.**
      `default_period(today: date) -> tuple[str, str]` passa a devolver
      `(date(today.year, today.month, 1).isoformat(), today.isoformat())`;
      `CLOSED_MONTHS` e o parâmetro `months` saem. Nascem
      `month_end(anchor: date) -> date`, que é `shift` para o mês seguinte menos
      um dia, e `covers_whole_months(start: str, end: str) -> bool`, verdadeira
      quando o início cai no dia 01 e o fim é o último dia do seu mês. `shift`,
      `day`, `month`, `check_period`, `INVALID_DATE` e `_INVALID_PERIOD` ficam
      como estão — `app/commitments/live.py:22` consome `shift`.
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-01, RF-07. O comentário de `:42-44` explica a decisão
      que este item reverte e é reescrito para dizer por que a janela termina na
      data de referência e não no fim do mês: a tela responde "quanto saiu", e
      somar parcela postada para data futura a faria responder outra pergunta
      (norma 11). `covers_whole_months` mora aqui porque é aritmética de
      calendário sobre os mesmos extremos que `shift` já resolve, e porque quem
      pergunta é a tela sobre a **janela**, não sobre o cruzamento.

- [ ] **1.2 — Criar `app/queries/ahead.py`: o que já está postado adiante.**
      Método:
      ```python
      @dataclass(frozen=True)
      class Ahead:
          entries: int
          amount_cents: int

      def posted_ahead(conn: sqlite3.Connection, *, after: str, until: str) -> Ahead
      ```
      Uma consulta só, com `count(*)` e `coalesce(sum(amount_cents), 0)` sobre
      `transactions`, filtrando por `SPENDING` importado de
      `app.queries.spending` e por `date > ? AND date <= ?`.
      *Considerando:* nada de 1.1 — o módulo recebe os dois extremos prontos.
      *Justificativa:* RF-06 e norma 33: contagem e soma são agregação, e
      agregação mora em `app/queries`. Módulo novo em vez de mais uma consulta
      dentro do router porque a norma 30 mantém o router fora da construção de
      consulta, e porque `app/queries/spending.py` e `app/queries/axes.py`
      pertencem a outros itens em execução simultânea. O limite inferior é
      **estrito** (`date > ?`): a data de referência é o último dia que a janela
      da tela soma, e incluí-la aqui faria os dois números da mesma tela
      contarem o mesmo lançamento. O filtro `SPENDING` é o mesmo de todo total
      da tela, então transferência entre contas próprias e estorno ficam de fora
      (invariante 25).

- [ ] **1.3 — Modificar `app/routers/spending.py`: a data pedida entra, e a
      janela nasce dela.**
      `_selection` passa a
      `reference = screen_date(request.query_params.get(DATE_FIELD))` e
      `default_start, default_end = default_period(reference.date)`, e devolve
      `(axis, start, end, reference)`; as quatro rotas passam a desempacotar
      quatro valores. `_base` recebe a referência e leva
      `"reference": reference.date.isoformat()` ao contexto. `_table_context`
      leva `"ahead"`, vindo de um auxiliar `_ahead(conn, reference, end)` que
      devolve `Ahead(0, 0)` quando `end > reference.date.isoformat()` e
      `posted_ahead(conn, after=reference.date.isoformat(),
      until=month_end(reference.date).isoformat())` no resto.
      `_panel_context` leva `"whole_months": covers_whole_months(start, end)`.
      `spending_screen` acrescenta `context["notice"] = reference.notice`.
      *Considerando 1.1 e 1.2:* a janela, a pergunta sobre meses inteiros e a
      soma do que está adiante chegam prontas, e a rota só traduz HTTP.
      *Justificativa:* RF-02 a RF-07. O `None` de hoje em `screen_date(None)` é
      o defeito: `/gastos` é a única das seis telas que chama o leitor único e
      joga fora o que o dono pediu. A guarda `end > referência` no auxiliar
      existe porque a linha da tela **afirma** que aqueles lançamentos estão
      fora do total: numa janela que já os alcança a afirmação é falsa, e frase
      verdadeira impressa na hora errada é o mesmo defeito que número que some.
      `notice` só entra no contexto da tela inteira porque os três fragmentos
      são pedidos pelo htmx com `inicio` e `fim` explícitos, nunca com `data`.

- [ ] **1.4 — Modificar `app/templates/gastos.html`: a recusa e a data que
      volta no submit.**
      No cabeçalho, `{% if notice %}<p class="notice" id="recusa"
      role="alert">{{ notice }}</p>{% endif %}`, na mesma forma de
      `app/templates/comprometido.html:11-13`,
      `app/templates/simulador.html:10-12`,
      `app/templates/consultor.html:12-14` e
      `app/templates/dividas.html:10-12`. Dentro do formulário
      `id="controles"`, `<input type="hidden" name="data" value="{{ reference }}">`.
      Carregue a skill `frontend-design` antes de tocar a tela (norma 27).
      *Considerando 1.3:* `notice` e `reference` chegam no contexto.
      *Justificativa:* RF-03. O texto é o `{{ notice }}` cru, que é o mesmo
      `data inválida: data (…)` que as outras telas imprimem, porque a frase vem
      de `app/queries/period.py:8::INVALID_DATE` e uma segunda cópia faria a
      mesma recusa ter duas redações. O campo oculto existe porque o formulário
      é um GET para a própria tela: sem ele o primeiro "Aplicar eixo e período"
      apaga a data pedida, e a linha do que está adiante passa a falar de outro
      dia, que o dono não escolheu.

- [ ] **1.5 — Modificar `app/templates/fragments/gastos_tabela.html`: a linha do
      que está adiante, e a cópia do vazio.**
      Abaixo da frase do total (`:8`), dentro de `{% if ahead['entries'] %}`:
      `<p class="lede" id="posterior">` dizendo quantos lançamentos do mês já
      estão postados depois de `{{ reference|dia }}`, com a soma em
      `<span class="cifra">{{ ahead['amount_cents']|brl }}</span>`, e afirmando
      que eles estão fora deste total. A cópia do vazio (`:42-44`) troca "seis
      meses fechados" pelo mês corrente, no texto e no rótulo do botão.
      *Considerando 1.3:* `ahead` e `reference` chegam no contexto do fragmento,
      então a linha sobrevive à troca por htmx.
      *Justificativa:* RF-01, RF-06. A linha fica colada no total que ela
      qualifica porque é esse total que ela ressalva; posta noutro painel, ela
      vira curiosidade. A cópia do vazio manda o dono para a janela onde a tela
      abre, e depois da 1.1 essa janela é o mês corrente — mantê-la como está
      seria a tela ensinando um padrão que ela não tem mais.

- [ ] **1.6 — Modificar `app/templates/fragments/gastos_painel.html`: o rótulo
      segue a janela.**
      A linha `:45` passa a duas: com `whole_months`, `Média mensal de
      {{ cross['monthly_average_cents']|brl }}`; sem, `No período,
      {{ cross['total_cents']|brl }}`.
      *Considerando 1.3:* `whole_months` chega no contexto do painel.
      *Justificativa:* RF-07. É a média do cruzamento fixa × essencial que
      dimensiona a reserva do objetivo: "média mensal" impresso sobre cinco dias
      é um rótulo que vira decisão errada de dinheiro. Dividir por fração de mês
      inventaria precisão que a base não tem, então fora de meses inteiros o
      número é o total e o rótulo diz isso.

- [ ] **1.7 — Modificar `tests/test_period.py`.**
      Os testes de `default_period` passam a afirmar a janela do mês corrente,
      incluindo o dia 01 (início e fim no mesmo dia) e o último dia do mês; o
      import de `CLOSED_MONTHS` e os testes do parâmetro `months` saem; entram
      os de `month_end` — fevereiro de ano bissexto e virada de ano — e os de
      `covers_whole_months`, com os dois lados que reprovam: início fora do dia
      01 e fim antes do último dia do mês. Os testes de `check_period`
      (`:41-54`) não são tocados.
      *Considerando 1.1.*
      *Justificativa:* RF-01, RF-07. `covers_whole_months` é a régua do rótulo,
      e uma régua sem os dois vizinhos de fora aprova qualquer janela.

- [ ] **1.8 — Criar `tests/test_ahead.py`.**
      Sobre a fixture `taxonomy_conn` de `tests/conftest.py:95-101` e o auxiliar
      `load`: lançamento anterior ao limite, lançamento **no** limite inferior —
      que não conta —, dois dentro, um depois do limite superior; uma
      transferência entre contas próprias e um estorno dentro do intervalo, que
      não entram; e o intervalo vazio, que devolve `Ahead(0, 0)`.
      *Considerando 1.2.*
      *Justificativa:* RF-06 e invariante 25. O lançamento exatamente na data de
      referência é o caso que separa o limite estrito do frouxo, e é o único que
      faria a tela contar o mesmo dinheiro duas vezes sem que nenhum total
      mudasse de valor — defeito que só aparece somando as duas linhas à mão.

- [ ] **1.9 — Modificar `tests/test_gastos_screen.py`.**
      `test_the_screen_opens_on_the_six_closed_months` (`:116`) passa a afirmar
      a abertura no mês corrente, e `:307-322` troca a janela esperada sob
      `DASH_TODAY=2026-05-15` de `de 01/11/2025 a 30/04/2026` para
      `de 01/05/2026 a 15/05/2026`, mantendo a antiga como controle negativo.
      Entra uma fixture de cliente com `DASH_TODAY=2026-09-05` e os seis
      lançamentos de −R$ 111,00 em `2026-08-20`, −R$ 200,00 em `2026-09-01`,
      −R$ 30,00 em `2026-09-05`, −R$ 40,00 em `2026-09-06`, −R$ 62,00 em
      `2026-09-30` e −R$ 77,00 em `2026-10-02`, todos na categoria de piso do
      `vocabulary` (`:63-83`), e sobre ela os testes da abertura, da data pedida
      e aceita, da data recusada, do par explícito e do valor ilegível, da linha
      do que está adiante e da sua ausência quando a janela alcança os
      lançamentos, e dos dois rótulos de cruzamento. A fixture `window`
      (`:58-60`) continua lendo a janela pela mesma via da rota.
      *Considerando 1.3 a 1.6.*
      *Justificativa:* RF-01 a RF-08. Os seis lançamentos são escolhidos para
      que cada número da tela seja único: o de outubro reprova quem contar o mês
      seguinte, o de `2026-09-05` reprova quem tratar o fim da janela como
      exclusivo, e a janela de `2026-08-20` a `2026-09-05` é a única que separa
      o total da média, porque numa janela dentro de um mês só a divisão é por
      um e os dois números coincidem.

> Nenhuma etapa cria portão, regra de lint ou configuração verificável: o
> instrumento desta fase são os testes, e quem os executa é `pytest`, que o CI
> já roda. `scripts/gates/` e `scripts/lint.sh` não são tocados.

---

## Execução sugerida

Fase única, numa branch só, integrada em `develop`. Ela toca
`app/queries/period.py`, `app/queries/ahead.py` (novo),
`app/routers/spending.py`, `app/templates/gastos.html`,
`app/templates/fragments/gastos_tabela.html`,
`app/templates/fragments/gastos_painel.html`, `tests/test_period.py`,
`tests/test_ahead.py` (novo) e `tests/test_gastos_screen.py`.

Nenhum desses caminhos é `app/plan/objective.py`, `app/routers/reference.py`,
`app/main.py`, `app/routers/settings.py`, `app/templates/configuracao.html`,
`app/debts/`, `app/taxonomy/`, `app/advisor/` ou `app/migrations/`, que estão
com os outros cinco itens em execução simultânea. Os dois fragmentos tocados são
servidos só por `/gastos`, e `app/queries/ahead.py` nasce sem consumidor fora
deste item — arquivo novo não conflita no merge.

## Pendências que viram item de roadmap

- **A última barra do gráfico mostra o mês inteiro enquanto o total da tela para
  na data de referência.** `app/queries/series.py:19-23::monthly_series` agrupa
  por mês de calendário e não recebe o dia do corte, então no mês corrente a
  barra soma também os lançamentos que a linha do RF-06 nomeia como fora do
  total. As duas leituras são verdadeiras e discordam pelo mesmo dinheiro.
  Nenhum RF pede a mudança, e `app/queries/series.py` está fora do que este item
  pode tocar.
- **Os três fragmentos de `/gastos` não imprimem recusa.** `/gastos/tabela`,
  `/gastos/painel` e `/gastos/detalhe` resolvem a data pelo mesmo leitor, mas
  quem os pede é o htmx, sempre com `inicio` e `fim` explícitos. Um pedido feito
  à mão a `/gastos/tabela?data=banana` responde pela data de referência em
  silêncio. RF-03 fala da tela, e ampliar para os fragmentos seria requisito
  nascido no plano.

## Validações de campo pendentes

- **A leitura da abertura sobre a base real do dono.** O brief nomeia o risco de
  a abertura sobre poucos dias parecer tela vazia, e a resposta a ele é um
  julgamento de quem olha o painel rodando com os próprios dados — nenhum
  critério tipado mede se a tela "parece vazia". O que fica sem verificação
  automática é só isso: a tela abrindo em setembro de 2026 sobre a base do dono,
  com a linha do que está postado adiante e o rótulo "no período" no lugar da
  média mensal. Todo o resto se observa por requisição HTTP e leitura do HTML
  sobre base de trabalho carregada pelo teste, com a data de referência fixada
  por variável de ambiente; nada depende de aparelho físico, permissão de
  plataforma ou rede real.
