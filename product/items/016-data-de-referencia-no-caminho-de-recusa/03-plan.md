# Plano — 016-data-de-referencia-no-caminho-de-recusa

**Item:** `016-data-de-referencia-no-caminho-de-recusa` · **Trilha:** rápida ·
**Fonte aprovada:** `01-brief.md` (aprovado em 07/09/2026) · **Terreno:**
`00-discovery.md` · Três fases, em sequência.

> **Todo número deste plano foi medido por execução**, não lido: sonda de
> 07/09/2026 com `DASH_TODAY=2026-09-05` no processo, relógio real em
> `2026-09-07`, base carregada e sessão autenticada. Nenhum número é remedido
> aqui.

## Objetivo

Ao fim das três fases existe **um** leitor da data de referência de tela, e as
seis rotas que hoje reimplementam o seu o consomem. Toda tela responde pela data
que `app/config.py:55-60::reference_date()` decide — inclusive quando o dono não
pede data nenhuma, inclusive quando a data digitada é recusada. Data ISO que
quebra a aritmética de calendário é recusada com a tela de pé, não com 500. E a
tela que recusa diz que recusou.

A quebra é por **contrato, não por tela**: a fase 1 fixa a forma do dado que as
outras duas consomem — três saídas, não duas —, porque os consumidores fazem
perguntas diferentes ao leitor. `/objetivo` grava ponto quando **não houve
recusa**, `/` imprime a ressalva de posição quando **houve pedido**, e essas
duas respostas divergem exatamente na ausência de `?data=`, que é o caminho
normal de entrada nas telas. Premissa errada de contrato se espalha para os seis
consumidores de uma vez, e o risco nomeado no brief (`/objetivo` parar de gravar
ponto na navegação normal) só se desarma antes da adoção. Depois disso o corte é
por **defeito observável**: a fase 2 leva as duas rotas que devolvem 500 e a
tela que acusa erro que ninguém cometeu; a fase 3 leva as três que recusam em
silêncio, a janela padrão de `/gastos` e a varredura que prova que não sobrou
sítio.

## O terreno, medido

| Sítio | Hoje | O que falta |
|---|---|---|
| `app/routers/summary.py:82-90` | `_reference` devolve `(date, notice)`, sem faixa | faixa; `date.today()` → referência |
| `app/routers/summary.py:121` | `asked_today` compara com `date.today()` | comparar com o pedido, não com o relógio |
| `app/routers/commitments.py:76-82` | `_reference` devolve `date`, sem faixa e sem aviso | faixa, aviso, referência |
| `app/routers/plan.py:43-64` | **com** faixa — é o único correto nesse ponto —, mas `_reference` devolve `tuple[date, bool]`: ausência e data aceita colapsam em `accepted=True`, duas saídas | passar a consumir o leitor, e devolver a faixa a ele |
| `app/routers/whatif.py:90-95` | faixa importada de `plan`, sem aviso | aviso, referência |
| `app/routers/advisor.py:90-95` | idem | aviso, referência |
| `app/routers/spending.py:93-105` | janela padrão por `default_period(date.today())` | referência |

Dois fatos decidem o desenho e não se re-discutem: `day(None, "data")` levanta
`InvalidPeriodError` (`app/queries/period.py:16-19`), então **a ausência de
`?data=` desce pelo ramo de recusa** — é o caminho normal, não a borda; e
`0001-01-01` é ISO legível que estoura em `app/queries/period.py:52`
(`year 0 is out of range`), alcançado por `app/commitments/live.py:22 live_floor`
→ `shift`.

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | O que decidiu | Decisão |
|---|---|---|
| Onde mora o leitor? | `app/routers/render.py` já é apoio de rota dentro de `app/routers/` sem ser rota | `app/routers/reference.py` |
| Quantas saídas o leitor devolve? | `/objetivo` decide gravar ponto pela **recusa** (`app/routers/plan.py:34-37`) e `/` decide a ressalva de posição pelo **pedido** (`app/routers/summary.py:121`): são duas perguntas diferentes, que só divergem quando não há `?data=` | três: `date`, `asked`, `notice` |
| Qual a faixa? | `app/routers/plan.py:43-44` já a usa para o mesmo defeito | `2000-01-01` a `2100-12-31`, agora no leitor |
| Que texto o aviso traz quando a data é legível mas fora da faixa? | `day()` já escreve `data inválida: {campo} ({valor})` para o defeito irmão | a mesma frase, com a constante exportada de `app/queries/period.py` |
| `?data=` presente e vazio | `app/routers/plan.py:56` já trata como ausência | ausência de pedido, sem aviso |
| A ressalva de posição em `/` | RF-11 e RF-12 | aparece quando houve **data pedida e aceita**; some quando não houve pedido |
| POST com data recusada mostra aviso? | O `notice` do POST é a resposta à ação que o dono acabou de fazer | não: os POST seguem como hoje. Lacuna registrada no retorno |
| `/gastos` usa o leitor ou `reference_date()` direto? | RF-01 pede caminho único | `screen_date(None).date` |
| Algum template muda? | As cinco telas já imprimem `id="recusa"` a partir de `notice`/`refused` | **nenhum** arquivo de `app/templates/` é tocado, e por isso nenhuma fase é fase de tela |
| Os pontos de `plan_snapshots` já gravados pelo relógio são migrados? | `DASH_TODAY` não existe no `.env` do dono, então em produção a data de referência **é** o relógio e os pontos antigos nasceram da origem certa | não: **nenhuma fase migra a série**. A mistura de origens só existe dentro de execução de validador, sobre cópia da base |
| Guarda permanente contra o sétimo sítio | Norma 20 — erro repetido vira causa raiz | teste em `tests/test_route_guard.py`, executado por `pytest`; nenhum portão novo em `scripts/gates/` |

---

## Fase 1 — O leitor único da data de tela (api)

**Objetivo da fase:** existe um leitor só que devolve a data de referência, se
houve pedido aceito e o texto da recusa — e nenhuma rota ainda o consome.

**Critérios de aceite:**

- [ ] `estrutural` — RF-01, RF-06
      Existe `app/routers/reference.py`, e ele exporta `screen_date`, a classe
      `Reference` com os campos `date`, `asked` e `notice`, e as constantes
      `EARLIEST` valendo `date(2000, 1, 1)` e `LATEST` valendo
      `date(2100, 12, 31)`. O arquivo **não** contém a expressão `date.today()`.
- [ ] `comportamental` — RF-02, RF-04
      *Dado* o processo com `DASH_TODAY=2026-09-05` no ambiente (05/09/2026 já
      passou, então o relógio do processo nunca coincide com ela)
      *Quando* `app.routers.reference.screen_date(None)` é chamada
      *Então* o resultado tem `.date` igual a `date(2026, 9, 5)`, `.asked` igual
      a `False` e `.notice` igual a `None`
- [ ] `comportamental` — RF-05
      *Dado* o processo com `DASH_TODAY=2026-09-05` no ambiente
      *Quando* `app.routers.reference.screen_date("")` e
      `app.routers.reference.screen_date("   ")` são chamadas
      *Então* as duas devolvem `.date` igual a `date(2026, 9, 5)`, `.asked`
      igual a `False` e `.notice` igual a `None` — parâmetro vazio é ausência de
      pedido, e ausência de pedido não é recusa
- [ ] `comportamental` — RF-06
      *Dado* o processo com `DASH_TODAY=2026-09-05` no ambiente
      *Quando* `app.routers.reference.screen_date("2100-12-31")` e
      `app.routers.reference.screen_date("2000-01-01")` são chamadas
      *Então* a primeira devolve `.date` igual a `date(2100, 12, 31)` e a
      segunda `.date` igual a `date(2000, 1, 1)`, ambas com `.asked` igual a
      `True` e `.notice` igual a `None` — os dois limites são aceitos, e não
      presumidos
- [ ] `comportamental` — RF-07
      *Dado* o processo com `DASH_TODAY=2026-09-05` no ambiente
      *Quando* `app.routers.reference.screen_date("banana")` é chamada
      *Então* o resultado tem `.date` igual a `date(2026, 9, 5)`, `.asked` igual
      a `False` e `.notice` igual à string `data inválida: data (banana)`
- [ ] `comportamental` — RF-08
      *Dado* o processo com `DASH_TODAY=2026-09-05` no ambiente
      *Quando* `app.routers.reference.screen_date("0001-01-01")` e
      `app.routers.reference.screen_date("2101-01-01")` são chamadas
      *Então* nenhuma das duas levanta exceção; as duas devolvem `.date` igual a
      `date(2026, 9, 5)` e `.asked` igual a `False`, e `.notice` vale
      `data inválida: data (0001-01-01)` e `data inválida: data (2101-01-01)`
- [ ] `comando` — RF-03
      `rtk proxy env -u DASH_TODAY DASH_ENV_FILE=/dev/null .venv/bin/python -c
      "from datetime import date; from app.routers.reference import screen_date;
      assert screen_date(None).date == date.today()"` sai com código `0` — e
      levanta `AssertionError` com código `1` se o leitor deixar de cair no
      relógio quando a variável não existe. Um comando que apenas imprimisse a
      comparação sairia com código zero nos dois casos
- [ ] `comando` — RF-01, RF-05, RF-06, RF-07, RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_screen_reference.py` sai com código `0`, e o arquivo exercita a
      data aceita, a ausência em três formas (`None`, `""` e espaço em branco),
      a data ilegível e a data legível fora da faixa nos dois lados

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Modificar `app/queries/period.py`: a frase da recusa fica
      pública.**
      `_INVALID_DATE` passa a `INVALID_DATE`, com o mesmo texto
      `data inválida: {field} ({value})`; `day` e `month` continuam a usá-la.
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-07, RF-08. O leitor recusa por **faixa**, onde `day()`
      nem é chamada, e precisa da mesma frase; duplicar a string faria a mesma
      tela dizer duas coisas para o mesmo defeito, e a próxima correção de texto
      pegaria uma metade. Nenhum outro módulo lê o nome antigo — medido.

- [ ] **1.2 — Criar `app/routers/reference.py`: o leitor, com três saídas e a
      faixa.**
      Método:
      ```python
      EARLIEST = date(2000, 1, 1)
      LATEST = date(2100, 12, 31)

      @dataclass(frozen=True)
      class Reference:
          date: date
          asked: bool
          notice: str | None

      def screen_date(asked: object) -> Reference
      ```
      Ausência (`None`, string vazia ou só espaço) devolve
      `Reference(reference_date(), False, None)`; data ilegível e data fora da
      faixa devolvem `Reference(reference_date(), False, INVALID_DATE.format(...))`;
      data legível dentro da faixa devolve `Reference(asked_date, True, None)`.
      O campo do formulário é `data` em todas as telas, e é o nome que entra na
      frase.
      *Considerando 1.1:* a frase vem de `app/queries/period.py`, não de um
      literal local.
      *Justificativa:* RF-01 a RF-08. **Três** saídas porque dois consumidores
      fazem duas perguntas diferentes: `/objetivo` grava ponto quando **não
      houve recusa** (`notice is None`, `app/routers/plan.py:34-37`) e `/`
      imprime a ressalva de posição quando **houve pedido** (`asked`,
      `app/routers/summary.py:121`). As duas respostas coincidem em toda entrada
      menos uma — a ausência de `?data=`, onde `notice is None` é verdadeiro e
      `asked` é falso —, e é justamente a entrada mais comum; um leitor de duas
      saídas obrigaria um dos dois a usar a resposta do outro. A faixa não é
      zelo: `0001-01-01` é ISO legível e derruba duas rotas em
      `app/queries/period.py:52`, e endurecer `shift` está fora de escopo por
      decisão do brief. O módulo mora em `app/routers/` porque
      `app/routers/render.py` já é apoio de rota que não é rota, e porque o
      leitor traduz um parâmetro de query — que é o trabalho que a norma 30
      reserva à camada de rota.

- [ ] **1.3 — Criar `tests/test_screen_reference.py`.**
      Os três estados; os dois limites da faixa e os dois vizinhos de fora
      (`1999-12-31`, `2101-01-01`); a ausência nas três formas; a data ilegível;
      a origem da data com `DASH_TODAY` presente (`monkeypatch.setenv`) e
      ausente — este com
      `monkeypatch.delenv("DASH_TODAY", raising=False)`, porque a variável não
      está no ambiente da suíte nem em `tests/conftest.py:14-19`, e sem
      `raising=False` o próprio teste levanta `KeyError: 'DASH_TODAY'` antes de
      exercitar coisa alguma — medido.
      *Considerando 1.2.*
      *Justificativa:* RF-01 a RF-08. Três testes já tocam `DASH_TODAY` —
      `tests/test_config.py:82` passa um mapping direto à função, e
      `tests/test_configuracao_screen.py:37` e `tests/test_commitments_engine.py:177`
      e `:182` já fixam a variável no ambiente do processo. O buraco é mais
      estreito e é ele que sustenta a fase: **nenhum teste fixa `DASH_TODAY` e
      afirma qual data uma rota renderizou**, que é por onde os seis sítios
      passaram sem ninguém notar.

---

## Fase 2 — As duas telas que caem, e a que acusa sem motivo (api)

**Objetivo da fase:** `/` e `/comprometido` respondem pela data de referência,
recusam data fora do calendário com a tela de pé, e param de alertar sobre uma
data que ninguém digitou.

**Critérios de aceite:**

- [ ] `comportamental` — RF-02, RF-04, RF-07, RF-09
      *Dado* o painel servido a partir deste repositório com
      `DASH_TODAY=2026-09-05` no ambiente do processo (05/09/2026 já passou,
      então o relógio nunca coincide com ela), base carregada e sessão
      autenticada
      *Quando* `GET /` é buscada **sem nenhuma query string** e, na mesma
      execução, `GET /?data=banana`
      *Então* a primeira responde `200`, o HTML **não** contém `id="recusa"`, e
      o trecho entre `id="projecao"` e o `</section>` seguinte contém
      `05/09/2026`; a segunda responde `200`, **contém** `id="recusa"` e a frase
      `A tela responde pela data de hoje.` — o segundo pedido é o controle
      positivo, sem o qual a ausência do alerta passaria numa página em branco
      ou num erro mudo. Hoje a primeira traz o alerta e imprime a data do
      relógio
- [ ] `comportamental` — RF-05
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` no ambiente do
      processo, base carregada e sessão autenticada
      *Quando* `GET /?data=` é buscada, com o parâmetro presente e vazio
      *Então* a resposta é `200`, o HTML **não** contém `id="recusa"`, e o
      trecho entre `id="projecao"` e o `</section>` seguinte contém `05/09/2026`
- [ ] `comportamental` — RF-06
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` no ambiente do
      processo, base carregada e sessão autenticada
      *Quando* `GET /?data=2100-12-31` é buscada
      *Então* a resposta é `200`, o HTML **não** contém `id="recusa"`, e o
      trecho entre `id="projecao"` e o `</section>` seguinte contém
      `31/12/2100` — a faixa recusa o que quebra a aritmética de mês, não o que
      é distante. Este é **guarda de não-regressão da faixa nova, não medida da
      fase**: hoje esta requisição já responde `200` sem `id="recusa"`, porque
      `app/routers/summary.py:82-90` não tem faixa nenhuma para aplicar. O
      critério existe para que a faixa, ao entrar, não passe a recusar o próprio
      limite superior
- [ ] `comportamental` — RF-08, RF-09
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` no ambiente do
      processo, base carregada e sessão autenticada
      *Quando* `GET /?data=0001-01-01` é buscada
      *Então* a resposta é `200`, **não** `500`; o HTML contém `id="recusa"`; e
      o trecho entre `id="projecao"` e o `</section>` seguinte contém
      `05/09/2026`. Hoje esta requisição levanta `ValueError: year 0 is out of
      range` e devolve `500`
- [ ] `comportamental` — RF-08, RF-09
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` no ambiente do
      processo, base carregada e sessão autenticada
      *Quando* `GET /comprometido?data=0001-01-01` é buscada
      *Então* a resposta é `200`, **não** `500`; o HTML contém `id="recusa"`; e
      o trecho entre `id="calendario"` e o `</section>` seguinte contém
      `>05/09/2026<`. Hoje esta requisição devolve `500`
- [ ] `comportamental` — RF-02, RF-04, RF-07, RF-09
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` no ambiente do
      processo, base carregada e sessão autenticada
      *Quando* `GET /comprometido` é buscada sem query string e, na mesma
      execução, `GET /comprometido?data=banana`
      *Então* as duas respondem `200` e o trecho entre `id="calendario"` e o
      `</section>` seguinte traz `>05/09/2026<` e `>20/10/2026<` nas duas; a
      primeira **não** contém `id="recusa"` e a segunda **contém** — o par é o
      controle positivo da ausência. Hoje as duas imprimem a data do relógio e
      nenhuma das duas traz `id="recusa"`
- [ ] `comportamental` — RF-11, RF-12
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` no ambiente do
      processo, base carregada e sessão autenticada, e `HOJE` sendo a data do
      relógio do dia em que a medição roda, em ISO (o que
      `date.today().isoformat()` devolve na máquina que mede)
      *Quando* `GET /` é buscada sem query string e, na mesma execução,
      `GET /?data=<HOJE>` — a data do relógio, pedida explicitamente
      *Então* a primeira **não** contém a frase `A posição é sempre a atual` e a
      segunda **contém**. Hoje **nenhuma das duas** contém: sem `?data=` a tela
      cai no relógio e a comparação `today == date.today()`
      (`app/routers/summary.py:121`) esconde a frase pelo motivo errado, e com
      `?data=<HOJE>` a mesma comparação a esconde de novo. Pedir a data do
      relógio é a única entrada em que "a data que responde é a do relógio" e
      "não houve pedido" dão respostas diferentes — com qualquer outra data o
      par já passaria hoje, antes da fase
- [ ] `estrutural` — RF-01
      `app/routers/summary.py` e `app/routers/commitments.py` não contêm a
      expressão `date.today()` e não definem função chamada `_reference`;
      `app/routers/summary.py` importa **`screen_date` e `Reference`** de
      `app.routers.reference`, porque o parâmetro anotado de `_answer` passa a
      ser a classe e não a data; e `app/routers/commitments.py` importa
      `screen_date` de `app.routers.reference`
- [ ] `comando` — RF-02, RF-04, RF-05, RF-08, RF-11, RF-12
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_resumo_screen.py tests/test_comprometido_screen.py` sai com
      código `0`, e os dois arquivos trazem testes que chamam a rota **sem** o
      parâmetro `data`, com `DASH_TODAY` fixado no ambiente

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **2.1 — Modificar `app/routers/summary.py`: o leitor entra, e o rótulo
      "hoje" deixa de olhar o relógio.**
      `_reference` (linhas 82-90) é apagada. `GET /` passa a
      `reference = screen_date(request.query_params.get(DATE_FIELD))` e responde
      com `notice=reference.notice`; `POST /sincronizar` usa `reference.date` e
      mantém o seu próprio aviso. A chave de contexto `asked_today`
      (linha 121) sai de `_context` e passa a valer `not reference.asked` dentro
      de `_answer`, com o comentário que a explica indo junto.
      Método: `def _answer(request: Request, conn: sqlite3.Connection,
      reference: Reference, *, notice: str | None = None,
      status_code: int = 200) -> Response`
      Os imports `InvalidPeriodError` e `day` ficam órfãos e saem.
      *Considerando 1.2:* as três saídas chegam prontas, e a rota não decide
      mais nada sobre a data.
      *Justificativa:* RF-01, RF-02, RF-04, RF-05, RF-06, RF-08, RF-11, RF-12.
      `asked_today` muda de dono porque é sobre **o que foi pedido**, não sobre
      números do mês: enquanto ele comparar com `date.today()`, a tela imprime a
      ressalva de posição sobre a própria data de referência. Import órfão
      reprova `ruff check`, que é o portão que a norma 35 nomeia.

- [ ] **2.2 — Modificar `app/routers/commitments.py`: o leitor entra, e a
      recusa deixa de ser silenciosa.**
      `_reference` (linhas 76-82) é apagada. `GET /comprometido` passa a
      `reference = screen_date(...)` e chama
      `_answer(request, conn, reference.date, notice=reference.notice)`; `_mark`
      usa `screen_date(asked).date` e **não** ocupa o `notice`, que é a resposta
      da ação. Imports órfãos saem.
      *Considerando 1.2* e *2.1* — a mesma forma de adoção nas duas rotas.
      *Justificativa:* RF-01, RF-02, RF-04, RF-07, RF-08, RF-09. A faixa que
      falta aqui é exatamente a que derruba a rota: `live_floor`
      (`app/commitments/live.py:22`) chama `shift`, que estoura em
      `app/queries/period.py:52`. `app/templates/comprometido.html:11-12` já
      renderiza `id="recusa"` a partir de `notice` — a tela não muda, só passa a
      receber o que dizer.

- [ ] **2.3 — Modificar `tests/test_resumo_screen.py`.**
      Testes novos, sem passar pelo auxiliar `_screen`: sem query string
      (referência e ausência de alerta), `?data=` vazio, `?data=0001-01-01`
      (hoje `500`), `?data=2100-12-31`, e o par da ressalva de posição —
      ausente sem pedido, presente quando a data pedida é a do relógio
      (`date.today().isoformat()` montado no próprio teste). `DASH_TODAY` entra
      por `monkeypatch.setenv`.
      *Considerando 2.1* e o risco nomeado no brief: `_screen`
      (`tests/test_resumo_screen.py:24-25`) manda `?data=` **sempre**, e é por
      isso que a classe inteira nunca foi exercida.
      *Justificativa:* RF-02, RF-04, RF-05, RF-06, RF-08, RF-11, RF-12. O par da
      ressalva usa a data do relógio porque com qualquer outra data ele passa
      hoje, sem nada implementado: a comparação atual é contra o relógio, e só
      pedir o próprio relógio separa "a data bate" de "não houve pedido". O
      teste de `tests/test_resumo_screen.py:211-215` — `?data=banana` traz
      `id="recusa"` — continua valendo e não é reescrito.

- [ ] **2.4 — Modificar `tests/test_comprometido_screen.py`.**
      Testes novos: sem query string, `?data=banana` e `?data=0001-01-01`,
      afirmando o `200`, a presença ou ausência de `id="recusa"` e a janela
      `05/09/2026`–`20/10/2026`.
      *Considerando 2.2.*
      *Justificativa:* RF-02, RF-04, RF-07, RF-08, RF-09. As constantes
      `WINDOW_START` e `WINDOW_END` do arquivo já são essas duas datas, medidas
      sobre `?data=2026-09-05`: o teste novo prova que a mesma janela sai **sem**
      o parâmetro.

---

## Fase 3 — As quatro rotas que faltam, e a varredura (api)

**Objetivo da fase:** `/objetivo`, `/simulador`, `/consultor` e `/gastos` passam
ao leitor único, as três que recusavam em silêncio passam a dizer, e nenhuma
função de rota volta a decidir a data por conta própria.

**Critérios de aceite:**

- [ ] `comportamental` — RF-02, RF-04
      *Dado* o painel servido a partir deste repositório com
      `DASH_TODAY=2026-09-05` no ambiente do processo (05/09/2026 já passou,
      então o relógio nunca coincide com ela), base carregada e sessão
      autenticada
      *Quando* `GET /simulador` e `GET /consultor` são buscadas **sem query
      string**
      *Então* as duas respondem `200`, nenhuma contém `id="recusa"`, e as duas
      trazem `<input type="hidden" name="data" value="2026-09-05">` — hoje as
      duas trazem a data do relógio nesse campo
- [ ] `comportamental` — RF-07, RF-09
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` no ambiente do
      processo, base carregada e sessão autenticada
      *Quando* `GET /simulador?data=banana` e `GET /consultor?data=banana` são
      buscadas
      *Então* as duas respondem `200`, as duas contêm `id="recusa"` com o texto
      `data inválida: data (banana)`, e as duas trazem
      `<input type="hidden" name="data" value="2026-09-05">` — hoje as duas
      respondem em silêncio, pela data do relógio
- [ ] `comportamental` — RF-02, RF-09, RF-14, RF-15
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` no ambiente do
      processo e sessão autenticada, sobre uma **cópia de trabalho** da base
      carregada (a rota grava na tabela `plan_snapshots`), com
      `DELETE FROM plan_snapshots WHERE reference_date IN ('2026-08-01', '2026-09-05')`
      já executado nessa cópia, para que as duas datas da medição comecem
      ausentes
      *Quando* `GET /objetivo?data=2026-08-01` é buscada, depois
      `GET /objetivo?data=0001-01-01`, e a consulta
      `SELECT reference_date FROM plan_snapshots WHERE scenario = 'base'` é lida
      **nesse ponto**; e depois `GET /objetivo` sem query string, com a mesma
      consulta lida de novo
      *Então* as três respostas são `200`; a segunda contém `id="recusa"` e a
      primeira e a terceira não; a **primeira leitura** da consulta contém
      `2026-08-01` e **não** contém `2026-09-05` — a data recusada não gravou
      ponto; e a **segunda leitura** contém `2026-09-05` — a navegação sem
      parâmetro gravou, sob a data de referência e não sob o relógio, que é o
      que ela grava hoje. A tabela é lida por SQL, e não pelo HTML, porque
      `app/templates/objetivo.html:117` só renderiza `data-ponto` quando a série
      tem mais de um ponto, e `UNIQUE (reference_date, scenario)`
      (`app/migrations/sql/007_plan.sql:12`) impede que a repetição de uma data
      vire linha nova: pela tela não há como distinguir gravou de não gravou
- [ ] `comportamental` — RF-10
      *Dado* o painel servido com `DASH_TODAY=2026-09-05` no ambiente do
      processo, sobre uma cópia de trabalho da base, e sessão autenticada
      *Quando* `POST /simulador/fato` grava `nome=quitacao-cdc`,
      `valor=1.000,00`, `validade=2026-09-06`, e depois grava
      `nome=transporte-sem-carro`, `valor=500,00`, `validade=2026-09-04`, e em
      seguida `GET /simulador` é buscada sem query string
      *Então*, no recorte do HTML que vai de `data-fato="quitacao-cdc"` até o
      primeiro `</tr>` depois dele, a palavra `vencido` **não** aparece; e no
      recorte equivalente de `data-fato="transporte-sem-carro"` — de
      `data-fato="transporte-sem-carro"` até o primeiro `</tr>` depois dele — a
      palavra `vencido` **aparece**. O recorte é declarado porque o atributo e a
      marca ficam a quatro linhas de distância na mesma linha da tabela
      (`app/templates/simulador.html:120` e `:124`), e lido linha a linha o
      critério passaria sem nada implementado. O segundo fato é o controle
      positivo, sem o qual a ausência da marca passaria numa tabela vazia. Hoje
      os dois recortes trazem `vencido`, porque a marca é decidida contra o
      relógio
- [ ] `comportamental` — RF-13
      *Dado* o painel servido a partir deste repositório com
      `DASH_TODAY=2026-05-15` no ambiente do processo — um mês diferente do de
      qualquer relógio possível na execução, que é o que torna a medição
      discriminante —, base carregada e sessão autenticada
      *Quando* `GET /gastos` é buscada **sem `inicio` e sem `fim`**
      *Então* a resposta é `200` e o HTML contém a frase
      `de 01/11/2025 a 30/04/2026` — a janela dos seis meses fechados antes da
      data de referência. Com o relógio em setembro de 2026 a janela de hoje é
      `de 01/03/2026 a 31/08/2026`, e essa frase **não** aparece
- [ ] `estrutural` — RF-01
      `app/routers/plan.py`, `app/routers/whatif.py`, `app/routers/advisor.py` e
      `app/routers/spending.py` não contêm a expressão `date.today()` e não
      definem função chamada `_reference`; os quatro importam `screen_date` de
      `app.routers.reference`; `app/routers/plan.py` não define `EARLIEST` nem
      `LATEST`; e nem `app/routers/whatif.py` nem `app/routers/advisor.py`
      importam qualquer nome de `app.routers.plan`

**Critérios de integração:**

- [ ] `comando` — RF-01
      `rtk proxy grep -REn --exclude-dir=__pycache__ "date\.today\(\)"
      app/routers` não imprime nenhuma linha. Os arquivos que hoje casam com esse
      padrão são `summary.py`, `commitments.py`, `plan.py`, `whatif.py`,
      `advisor.py` e `spending.py`; o critério prova que nenhuma rota voltou a
      resolver a data de tela por conta própria
- [ ] `comportamental` — RF-02, RF-09
      *Dado* o painel servido a partir deste repositório com
      `DASH_TODAY=2026-09-05` no ambiente do processo, sessão autenticada e uma
      **cópia de trabalho** da base carregada (`GET /objetivo` grava), com
      `DELETE FROM plan_snapshots WHERE reference_date = '2026-09-05'` já
      executado nessa cópia
      *Quando* `GET /`, `GET /comprometido`, `GET /objetivo`, `GET /simulador` e
      `GET /consultor` são buscadas sem query string na mesma execução, e depois
      as cinco de novo com `?data=banana`
      *Então* nas cinco primeiras a data de referência que a tela usa é
      `2026-09-05` — `id="projecao"` contém `05/09/2026` em `/`,
      `id="calendario"` contém `>05/09/2026<` em `/comprometido`, o campo
      `<input type="hidden" name="data" value="2026-09-05">` aparece em
      `/simulador` e `/consultor`, e para `/objetivo` a consulta
      `SELECT reference_date FROM plan_snapshots WHERE scenario = 'base'`,
      lida depois da requisição, contém `2026-09-05` (a tela de `/objetivo` não
      imprime a data de referência fora da tabela da linha do tempo, que só
      aparece com mais de um ponto na série) — e nenhuma das cinco contém
      `id="recusa"`; nas cinco segundas todas respondem `200` e **todas**
      contêm `id="recusa"`. Hoje as cinco primeiras respondem pela data do
      relógio, `/` traz alerta sem motivo, e três das cinco segundas silenciam
- [ ] `comando` — RF-01, RF-10, RF-11, RF-12, RF-13, RF-14, RF-15
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_resumo_screen.py tests/test_comprometido_screen.py
      tests/test_simulador_screen.py tests/test_consultor_screen.py
      tests/test_gastos_screen.py tests/test_plan.py tests/test_route_guard.py`
      sai com código `0`, e `tests/test_route_guard.py` define as funções
      `test_no_router_resolves_the_screen_date_by_itself` — que varre os
      arquivos de `app/routers/` procurando `date.today()` e falha nomeando cada
      arquivo encontrado — e
      `test_the_sweep_accuses_a_source_that_calls_the_clock` — que entrega à
      mesma varredura um texto-fonte contendo `date.today()` e afirma que ela o
      acusa. As duas são novas: o arquivo já traz
      `test_every_registered_route_requires_session` e
      `test_the_login_form_is_the_open_door`, que são a guarda de sessão e
      seguem intactos. Sem a segunda das novas, uma varredura quebrada passaria
      em verde para sempre

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **3.1 — Modificar `app/routers/whatif.py`: o leitor entra, e `/simulador`
      passa a dizer que recusou.**
      `_reference` (linhas 90-95) é apagada, junto do import
      `from app.routers.plan import EARLIEST, LATEST`. `GET /simulador` passa a
      `reference = screen_date(request.query_params.get(DATE_FIELD))` e chama
      `_answer(request, conn, reference.date, notice=reference.notice)`; os dois
      POST usam `screen_date(data).date` e mantêm o `notice` da ação. Imports
      órfãos de `app.queries.period` saem.
      *Considerando 1.2:* a faixa passa a vir do leitor, e não mais de `plan`.
      *Justificativa:* RF-01, RF-02, RF-04, RF-07, RF-09.
      `app/templates/simulador.html:10-11` já renderiza `id="recusa"` a partir
      de `notice`: a tela não muda, só passa a receber o que dizer. Os POST
      seguem como hoje porque o `notice` deles responde à ação que o dono acabou
      de fazer, e o `data` que eles recebem vem do campo oculto que a própria
      tela preenche.

- [ ] **3.2 — Modificar `app/routers/advisor.py`: a mesma adoção em
      `/consultor`.**
      `_reference` (linhas 90-95) e o import de `EARLIEST`/`LATEST` são
      apagados; `GET /consultor` passa `notice=reference.notice`; os três POST
      usam `screen_date(data).date`. Com `_reference` fora, o import
      `from app.queries.period import InvalidPeriodError, day`
      (`app/routers/advisor.py:20`) fica órfão e **sai**: os dois nomes só eram
      usados dentro dela, e import não usado reprova `ruff check` (F401) em
      `scripts/lint.sh`.
      *Considerando 3.1:* é o caso idêntico ao lado, e se corrige junto.
      *Justificativa:* RF-01, RF-02, RF-04, RF-07, RF-09.
      `app/templates/consultor.html:12-13` já tem o `id="recusa"`.

- [ ] **3.3 — Modificar `app/routers/plan.py`: a única rota certa passa a
      consumir o leitor.**
      `_reference` (linhas 47-64) e as constantes `EARLIEST`/`LATEST`
      (linhas 43-44) são apagadas. `GET /objetivo` passa a
      `reference = screen_date(...)`, grava ponto quando `reference.notice is
      None` e define `context["refused"] = reference.notice is not None`. O
      import `from app.queries.period import InvalidPeriodError, day`
      (`app/routers/plan.py:13`) fica órfão com a saída de `_reference` e
      **sai** — import não usado reprova `ruff check` (F401) em
      `scripts/lint.sh`.
      *Considerando 1.2* (o leitor devolve as três saídas) e *3.1 e 3.2* (os
      dois importadores das constantes já não dependem delas — invertida a
      ordem, o app não sobe).
      *Justificativa:* RF-01, RF-02, RF-14, RF-15. Esta é a rota que o item mais
      arrisca, e a armadilha é uma só: a decisão de gravar ponto é por
      **`reference.notice is None`**, nunca por `reference.asked`. Medidos lado
      a lado, `notice is None` reproduz o `accepted` de hoje em **todas** as
      entradas, enquanto `asked` diverge justamente na ausência de parâmetro —
      trocar um pelo outro faz a linha do tempo parar de crescer na navegação
      normal, que é a regressão que este item existe para evitar.
      `tests/test_plan.py:170` e `:220` já fixam os dois lados desse
      comportamento. O comentário que explica por que a recusa não grava ponto
      viaja com a lógica.

- [ ] **3.4 — Modificar `app/routers/spending.py`: a janela padrão sai da
      referência.**
      `_selection` (linhas 93-105) passa a `default_period(screen_date(None).date)`;
      `check_period` e o tratamento de `InvalidPeriodError` do período ficam
      como estão. O import `from datetime import date` fica órfão e sai.
      *Considerando 1.2:* `screen_date(None)` é literalmente "nenhuma data
      pedida", e é isso que `/gastos` tem — a tela aceita `inicio` e `fim`, não
      `data`.
      *Justificativa:* RF-01, RF-13. Passar pelo leitor em vez de chamar
      `reference_date()` direto mantém **um** caminho, que é o que RF-01 pede;
      e `/gastos` não ganha aviso de recusa porque ela não pede data de
      referência — está no não-escopo do brief.

- [ ] **3.5 — Criar `tests/test_simulador_screen.py` e
      `tests/test_consultor_screen.py`, e ampliar `tests/test_plan.py` e
      `tests/test_gastos_screen.py`.**
      Simulador: sem query string, `?data=banana`, e o fato com
      `valid_until = 2026-09-06` que **não** é vencido sob `DASH_TODAY=2026-09-05`,
      ao lado de um com `2026-09-04` que é — a asserção recorta a linha da
      tabela, do `data-fato` até o `</tr>` seguinte. Consultor: sem query string
      e `?data=banana`. `test_plan.py`: sob `DASH_TODAY=2026-09-05`, a sequência
      data aceita distinta (`?data=2026-08-01`) → data recusada
      (`?data=0001-01-01`) → sem query string, conferindo `plan_snapshots` por
      SQL entre a segunda e a terceira. `test_gastos_screen.py`: a janela padrão
      sob `DASH_TODAY=2026-05-15`, **e a fixture `window`
      (`tests/test_gastos_screen.py:58-60`)**, que hoje espelha a rota com
      `default_period(date.today())` e é consumida em `:230`, passa a
      `default_period(screen_date(None).date)`.
      *Considerando 3.1 a 3.4.*
      *Justificativa:* RF-02, RF-04, RF-07, RF-09, RF-10, RF-13, RF-14. O fato
      vencido é o defeito que originou o item: `_stale`
      (`app/settings/store.py:25-26`) recebe o relógio pela cadeia
      `whatif.py:40 → _reference → _answer → _context → facts(today) →
      stored(today)`, e "vencido" passa a significar coisas diferentes no painel
      e no relatório regerável. A sequência de `test_plan.py` pede duas datas
      distintas — como `tests/test_plan.py:186-189` já faz — porque
      `UNIQUE (reference_date, scenario)` funde a repetição numa linha só, e a
      fixture `window` tem de ler a data pela mesma via que a rota, senão diverge
      dela em toda execução com `DASH_TODAY` no ambiente.

- [ ] **3.6 — Modificar `tests/test_route_guard.py`: o guarda contra o sétimo
      sítio.**
      Dois testes **novos**, ao lado dos dois de guarda de sessão que o arquivo
      já traz (`test_every_registered_route_requires_session` e
      `test_the_login_form_is_the_open_door`, que não são tocados):
      `test_no_router_resolves_the_screen_date_by_itself`, que lê os arquivos de
      `app/routers/`, coleta os que contêm `date.today()` e falha nomeando cada
      um; e `test_the_sweep_accuses_a_source_that_calls_the_clock`, que entrega
      ao mesmo auxiliar de varredura um texto-fonte com `date.today()` dentro e
      afirma que ele é acusado. Quem executa os dois é `pytest`, que o CI já
      roda; **nenhum portão novo entra em `scripts/gates/`** e o
      `gates_runner.sh` não é tocado.
      *Considerando 3.1 a 3.4:* sem as quatro adoções desta fase e as duas da
      fase 2, o guarda nasce vermelho.
      *Justificativa:* RF-01 e norma 20. O defeito nasceu no item `008`, foi
      medido pelo validador do `015` e chegou a **seis** sítios porque nada
      impedia o sétimo; a causa raiz é o leitor único, e o guarda é o que
      impede a reincidência. O segundo teste existe porque instrumento sem prova
      de que reprova é instrumento que passa em verde depois de quebrado.

---

## Execução sugerida

1. **Fase 1, bloqueante.** As fases 2 e 3 consomem o leitor, e a forma do dado —
   três saídas — é a premissa que, errada, se espalha para os seis sítios de uma
   vez.
2. **Fase 2 depois da 1.** Toca `app/routers/summary.py`,
   `app/routers/commitments.py`, `tests/test_resumo_screen.py` e
   `tests/test_comprometido_screen.py`.
3. **Fase 3 depois da 2.** Toca `app/routers/plan.py`, `app/routers/whatif.py`,
   `app/routers/advisor.py`, `app/routers/spending.py`,
   `tests/test_simulador_screen.py`, `tests/test_consultor_screen.py`,
   `tests/test_plan.py`, `tests/test_gastos_screen.py` e
   `tests/test_route_guard.py`.

As fases 2 e 3 **não** são paralelas, apesar de a interseção dos arquivos ser
vazia. A dependência é de **verificação**: o critério de varredura e o das cinco
telas numa execução só fecham quando as seis rotas estão convertidas, e num par
de worktrees eles reprovariam a frente que faz merge primeiro por trabalho que a
outra ainda não entregou. A sequência custa uma sessão; o paralelo custa um
veredicto falso e a rodada que ele obriga.

## Pendências que viram item de roadmap

- **POST com data recusada não mostra aviso.** RF-07 e RF-09 falam de tela
  aberta (GET), e o `notice` dos POST de `/comprometido`, `/simulador` e
  `/consultor` é a resposta à ação que o dono acabou de fazer. Um POST forjado à
  mão com `data=banana` responde pela referência **em silêncio**. O brief não
  pede o contrário, e resolver aqui seria requisito nascido no plano.
- **A cópia do aviso diz "A tela responde pela data de hoje."** No `.env` do
  dono `DASH_TODAY` não existe: em produção a data de referência **é** o
  relógio, e a frase é literalmente verdadeira — é o que o brief registra no
  não-escopo. A divergência aparece só dentro de execução de validação, onde os
  critérios deste plano fixam a variável e a frase passa a falar de um "hoje"
  que não é o da tela; é artefato do ambiente de medição, não defeito do
  produto. Se `DASH_TODAY` entrar no `.env` do dono, a frase passa a mentir em
  produção e a troca de texto vira item de roadmap.

## Validações de campo pendentes

Nenhuma. Todo comportamento deste item se observa por requisição HTTP, por
leitura do HTML devolvido e por consulta SQL à base de trabalho, com a data de
referência fixada por variável de ambiente; nada depende de aparelho físico,
permissão de plataforma ou rede real.
