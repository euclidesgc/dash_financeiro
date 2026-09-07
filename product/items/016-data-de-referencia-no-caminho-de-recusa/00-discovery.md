# Discovery — 016-data-de-referencia-no-caminho-de-recusa

**Item do roadmap:** `016-data-de-referencia-no-caminho-de-recusa` — `_reference` de
`app/routers/whatif.py` e de `app/routers/advisor.py` cai em `date.today()` quando a data
pedida é inválida ou está fora da faixa, em vez de `app.config.reference_date()`, que é quem
lê `DASH_TODAY`. Efeito medido pelo validador da fase 1 do `015`: com `DASH_TODAY=2026-09-05`
no processo, `/simulador` e `/consultor` renderizam a data de hoje de verdade — e é esse
`today` que decide se um fato está **vencido**, então uma leitura sem data pedida pode marcar
como vencido o que a data de referência ainda considera válido. Pré-existente desde o item
`008`, fora do diff do `015`. Varrer os demais `date.today()` de rota entra no mesmo item.

**Data:** 2026-09-07

## O que a medição mostrou, e que o roadmap não sabia

Tudo abaixo é execução, não leitura. Sonda com `DASH_TODAY=2026-09-05` e `date.today()`
valendo `2026-09-07`, base carregada, sessão autenticada.

**O caminho de recusa é o caminho normal.** `day(None, "data")` levanta `InvalidPeriodError`
(`app/queries/period.py:16-19`), então **entrar na tela sem `?data=`** — a navegação comum,
a partir dos próprios links do painel — desce pelo mesmo ramo de recusa. Não são dois casos
de borda: é o comportamento padrão de cinco telas.

| Tela | sem `?data=` | ilegível (`banana`) | fora do calendário (`0001-01-01`) | diz que recusou? |
|---|---|---|---|---|
| `/` resumo | **2026-09-07** + alerta espúrio | 2026-09-07 + alerta | **500** | sim, e no caso errado |
| `/comprometido` | 2026-09-07 | 2026-09-07 | **500** | não |
| `/objetivo` | 2026-09-07 (aceito) | 2026-09-07 | 2026-09-07 | sim, correto |
| `/simulador` | 2026-09-07 | 2026-09-07 | 2026-09-07 | não |
| `/consultor` | 2026-09-07 | 2026-09-07 | 2026-09-07 | não |
| `/gastos` | janela padrão de 2026-09-07 | — | tolera | não |

Três defeitos distintos saem daí, e nenhum é o que o roadmap descreveu:

1. **Cinco `_reference` caem em `date.today()`**, não dois: `summary.py:82`, `commitments.py:76`,
   `plan.py:47`, `whatif.py:90`, `advisor.py:90`. Mais `spending.py:92`, que resolve a janela
   padrão por `default_period(date.today())`. Não existe leitor compartilhado: cada rota
   reimplementa o seu, e as seis erram do mesmo jeito. É classe, não caso.

2. **A tela inicial acusa um erro que ninguém cometeu.** `GET /` sem query string renderiza
   `id="recusa"` com o texto literal `data inválida: data (None) A tela responde pela data de
   hoje.` — a primeira coisa que o dono vê ao abrir o painel é um alerta vermelho sobre uma
   data que ele não digitou.

3. **Data fora do calendário derruba duas rotas com 500.** `GET /?data=0001-01-01` e
   `GET /comprometido?data=0001-01-01` levantam `ValueError: year 0 is out of range` em
   `app/queries/period.py:52`, via `app/commitments/live.py:22 live_floor` → `shift`. É
   exatamente o defeito que `plan.py:47-52` documenta no comentário (RF-15) e resolveu com
   `EARLIEST`/`LATEST` — `summary.py` e `commitments.py` nunca ganharam a faixa.

**Cobertura hoje: nenhuma.** Nenhum teste fixa `DASH_TODAY` e faz requisição a essas rotas
afirmando qual data saiu. Os auxiliares dos testes de tela passam `?data=` explícito sempre
(`tests/test_resumo_screen.py:24`), então o caminho sem parâmetro nunca foi exercido.

## INVEST

| Critério | Passa | Observação |
|---|---|---|
| Independente | sim | Não espera item nenhum; o `018` (tipagem estrita) é posterior e não o toca. |
| Negociável | sim | Fixo: a data que a tela usa. Conversável: extrair leitor único ou corrigir seis sítios no lugar. |
| Valioso | sim | O dono vê alerta falso ao abrir o painel, duas telas caem por URL digitada, e `vencido` mente. |
| Estimável | sim | Terreno medido: seis sítios, um leitor novo, cinco adoções, testes das três naturezas. Duas a três fases. |
| Pequeno | sim | Um módulo novo e seis arquivos tocados, sem migração e sem esquema. |
| Testável | sim | `DASH_TODAY` fixo mais requisição afirmando a data renderizada e o status. |

**Veredicto do INVEST:** segue como está.

## História

Como dono do painel, quero que **toda** tela responda pela data de referência do processo —
inclusive quando eu não peço data nenhuma, e inclusive quando a data que digitei é recusada —
para que o painel e o relatório regerável concordem, e para que "vencido" signifique a mesma
coisa nos dois.

## Regras e exemplos

### R1 — A data que uma tela usa vem de `reference_date()`, nunca de `date.today()`

- **E1.1** — Com `DASH_TODAY=2026-09-05` no processo e `date.today()` valendo `2026-09-07`,
  `GET /simulador` sem query string renderiza a referência **2026-09-05**. Hoje renderiza
  `2026-09-07`.
- **E1.2** — Nas mesmas condições, `GET /consultor`, `GET /comprometido`, `GET /objetivo` e
  `GET /` sem query string renderizam **2026-09-05**. Hoje as cinco renderizam `2026-09-07`.
- **E1.3** — Sem `DASH_TODAY` no ambiente, `GET /simulador` renderiza o dia corrente do
  relógio: `reference_date()` já cai em `date.today()` quando a variável não existe
  (`app/config.py:60`), e é ele quem decide, não a rota.

### R2 — Não pedir data não é pedir data errada

- **E2.1** — `GET /` sem query string não traz nenhum elemento `id="recusa"` no HTML. Hoje
  traz, com o texto `data inválida: data (None) A tela responde pela data de hoje.`
- **E2.2** — `GET /?data=` (parâmetro presente e vazio) é tratado como ausência de pedido:
  200, sem alerta, referência `2026-09-05`.
- **E2.3** — `GET /?data=banana` **continua** trazendo `id="recusa"`, porque aí houve pedido
  e ele foi recusado. O comportamento que `tests/test_resumo_screen.py:211-215` já afirma não
  muda.

### R3 — Data fora do calendário é recusada, e a rota responde 200 pela referência

- **E3.1** — `GET /?data=0001-01-01` devolve **200**, com alerta de recusa, referência
  `2026-09-05`. Hoje devolve 500 com `ValueError: year 0 is out of range`.
- **E3.2** — `GET /comprometido?data=0001-01-01` devolve **200** pela referência. Hoje,
  o mesmo 500.
- **E3.3** — `GET /?data=2100-12-31` é aceita: está dentro da faixa, e a tela responde por
  ela. A faixa recusa o que quebra a aritmética de mês, não o que é distante.

### R4 — Toda tela que recusa uma data diz que recusou

- **E4.1** — `GET /simulador?data=banana` mostra o aviso de recusa e responde por
  `2026-09-05`. Hoje silencia e responde `2026-09-07`.
- **E4.2** — `GET /consultor?data=banana` e `GET /comprometido?data=banana`, idem. `plan.py` e
  `summary.py` já dizem; as outras três se alinham ao caso idêntico ao lado.

### R5 — Existe um leitor só, e ele é o único caminho

- **E5.1** — `grep -rn "date.today()" app/routers/` não devolve nenhuma linha em função que
  resolve a data de uma tela. As ocorrências que sobrarem são de outra natureza e estão
  nomeadas uma a uma no plano.
- **E5.2** — `app/routers/summary.py:121` deixa de comparar `today == date.today()` para
  decidir o rótulo "hoje": com `DASH_TODAY=2026-09-05` e nenhuma data pedida, a tela hoje
  afirma que a referência **não** é hoje, e imprime a ressalva de posição sobre a própria
  data de referência.

### R6 — `vencido` se decide pela data de referência

- **E6.1** — Fato com `valid_until = 2026-09-06` e `DASH_TODAY=2026-09-05`: `GET /simulador`
  sem query string **não** marca o fato como vencido. Hoje marca, porque `_stale`
  (`app/settings/store.py:25-26`) recebe `2026-09-07` pela cadeia
  `whatif.py:40 → _reference → _answer → _context → facts(today) → stored(today) → _stale`.

## Perguntas em aberto

**Nenhuma.** Quatro apareceram durante o mapeamento e as quatro fecharam sem entrevista:

- **`/gastos` entra no item?** Entra. A própria linha do roadmap já decidiu: "varrer os demais
  `date.today()` de rota entra no mesmo item".
- **`whatif`, `advisor` e `commitments` passam a sinalizar a recusa?** Passam. `plan` e
  `summary` — o caso idêntico ao lado — já sinalizam, e o comentário de `summary.py:83-86`
  escreve a razão: uma tela que responde em silêncio por uma pergunta diferente da que foi
  feita é pior que uma que recusa.
- **`summary` e `commitments` ganham a faixa, ou se endurece `shift`?** Ganham a faixa, dentro
  do leitor único. O projeto já escolheu esse remédio uma vez, em `plan.py`, e o esqueceu nas
  outras duas rotas exatamente porque não havia lugar comum para pô-lo. Endurecer `shift` é
  tratar o sintoma numa biblioteca cujos outros chamadores recebem data já validada.
- **`DASH_TODAY=banana` deve derrubar o processo?** Fica **fora do escopo**, deliberadamente.
  `reference_date()` propaga o `ValueError` cru (`app/config.py:60`), e falhar alto num
  ambiente mal configurado é o comportamento certo — é erro do operador, não data pedida pelo
  usuário. Está registrado aqui para não voltar como pergunta.

## Trilha

**Trilha: rápida.**

| Gatilho | Verdadeiro | Evidência |
|---|---|---|
| Zero perguntas em aberto | sim | As quatro levantadas fecharam acima, com a razão de cada uma. |
| Uma stack só | sim | Só `api` (python): `app/routers`, `app/queries`, `app/templates` e `tests`. |
| Sem mudança de contrato | sim | Não há OpenAPI no repositório; as seis rotas devolvem HTML e nenhuma ganha ou perde parâmetro. |
| Sem dependência nova | sim | Nada entra em `pyproject.toml`; o conserto usa `app.config.reference_date`, que já existe. |

A trilha rápida corta documento, não verificação: critério tipado, reviewer de stack e
validador cego valem igual.
