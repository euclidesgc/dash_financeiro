# Veredicto — item `003-comprometido`, fase 3

**Resultado:** `APROVADO`

Branch: `003-comprometido/fase-3-calendario` · ponta `6ce6056` · base `de2728b`
Data da verificação: 2026-09-06 · Validador cego, agente novo.

**Higiene do despacho:** nenhum plano, brief, spec ou veredicto anterior veio no
envelope. Leitura declarada fora do estrito: `.harness/config.json`, **apenas**
o campo `command_quirks`. É configuração de instrumento, não traz plano nem
fases.

## Portões

| Portão | Resultado |
|---|---|
| lint/analyze | **N/A no projeto** — `pyproject.toml` não declara ruff/mypy/flake8/black; `ls .venv/bin \| grep -Ei "ruff\|mypy\|flake8\|black"` sai vazio. Declarado ausente, **não** aprovado por presunção. Quarto validador seguido a registrar a ausência. |
| testes | **OK** — `pytest -q` → `EXIT=0`, `308 passed, 2 warnings in 15.41s` |
| gates | **OK** — `bash scripts/gates/gates_runner.sh` → `EXIT=0`, `✓ gates: limpos (árvore completa, 213 arquivo(s) considerados).` |

Preparo do banco reproduzido como escrito: `app.ingest` → `ingested
transactions=1942 accounts=12` / `commitments recomputed: 151
reference=2026-09-06`; `app.auth.seed` → `seeded user: teste`. Servidor subido
com `setsid`, `/login` respondendo `200` antes de qualquer medição; ambos os
servidores mortos ao fim.

## Critérios de aceite

- [x] **`comportamental` — RF-21** — Chromium com cookie de um único `POST
      /login`, `200`. `contém 05/09/2026: true` · `contém 20/10/2026: true` ·
      `27` elementos `[data-dia]` · `primeiro/último: 2026-09-06 2026-10-20` ·
      todos dentro da janela, em ordem crescente, sem repetição · `dias com
      total != soma dos filhos: 0` · `dias sem filho [data-serie]: 0`.
- [x] **`comportamental` — RF-22** — o comando das séries paradas imprimiu **35**
      linhas. No DOM: o texto traz `35 sem cobrança recente`, e nenhum dos 42
      `[data-serie]` do bloco pertence ao conjunto parado (`0 []`).
- [x] **`comando` — RF-23** — `pytest -q tests/test_commitments_calendar.py` →
      `EXIT=0`, `11 passed`. O teste nomeado existe em
      `tests/test_commitments_calendar.py:141` e monta o cenário exigido. O
      validador **reproduziu o cenário fora da suíte do avaliado**, com banco
      próprio: `[('2026-06-10', -10000), ('2026-07-10', -10000), ('2026-08-10',
      -10000), ('2026-09-10', -9000)]` → `entradas no dia: 1 | total_cents:
      -9000 | predicted=False`.
- [x] **`comportamental` — RF-34** — a resposta de 86.633 bytes traz, dentro de
      `<section id="calendario">`, `<p class="lede">A data de cada vencimento é
      previsão a partir do histórico, não data contratual.</p>`.
- [x] **`comportamental` — RF-30** — `200`; `id="assinaturas"`,
      `id="parcelamentos"` e `id="calendario"` presentes; `−R$ 12.802,64` sob
      `Total comprometido` e `R$ 0,00` sob `Economia projetada`, uma ocorrência
      cada.
- [x] **`estrutural` — RF-39** — `comprometido-calendario-375.png` (73.135 B,
      375×800), `comprometido-calendario-1440.png` (107.194 B, 1440×800) e
      `comprometido-calendario-dark-1440.png` (108.894 B, 1440×800), no mesmo
      diretório. As três foram abertas: são o bloco do calendário, claro e
      escuro.

## Critérios de integração

- [x] **`comando` — portão local** — `EXIT=0`, `308 passed`.
- [x] **`comando` — RF-37** — 0 linhas em stdout. As 4 linhas de stderr são
      diagnósticos do grep sobre `app/commitments/__pycache__/*.pyc`, arquivos
      **não rastreados** (`git ls-files app/commitments | grep -c "pycache"` →
      `0`), três dos quais anteriores a esta fase. Reexecutado com
      `--exclude-dir=__pycache__`: `stdout 0 | stderr 0`. Cumprido sobre o
      código-fonte rastreado; ver apontamento 3.
- [x] **`comportamental` — RF-21, RF-24** — banco `/tmp/dash-003-e2e.sqlite` do
      zero, servidor próprio, um único `POST /login`. Leitura 1: `−R$ 12.802,64`
      e `R$ 0,00`; três dispensas com `http=200` cada; leitura 2: `−R$
      11.703,01` e `R$ 1.099,63`. Nas duas, `#calendario` traz `05/09/2026` e
      `20/10/2026` — 27 dias antes, 24 depois. Sem reingestão e sem reinício:
      `Started server process` aparece uma vez só, e o PID seguia vivo ao fim.
- [x] **`comportamental` — RF-39, RF-41** — `reducedMotion=true` confirmado em
      página nas seis medições. Carregando já na largura: 375, 768 e 1440 com
      `scrollWidth == innerWidth`. Redimensionando com a página aberta: as três
      idem. Em todas, 312 elementos em `#calendario *` e **zero** com
      `animationDuration` ou `transitionDuration` diferente de `0s`.

## Divergências declaradas — julgamento

**(a) `app/commitments/calendar.py` fora do escopo declarado — aceitável.**
Os critérios *nomeiam o módulo*: RF-23 manda chamar
`app.commitments.calendar.calendar(conn, today=...)`. Critério que manda chamar
a função obriga o arquivo a existir. O módulo é importado só por
`app/routers/commitments.py:10` e pelo teste da fase, e o intervalo
`de2728b..HEAD` não tocou nada além de `app/`, `tests/`, as três capturas e
`product/state.json` — não houve carona.

**(b) Substituição da previsão por mês, não por dia — aceitável, e a
justificativa se sustenta.**
O critério escrito descreve uma ocorrência que cai **exatamente no dia
previsto**; nesse cenário as duas leituras dão o mesmo resultado, e a reprodução
independente confirma o exigido. O critério está satisfeito.

Nos dados reais: `recurring | jim com | -13644 | due_day 6 | last_seen
2026-09-08` contra a transação `2026-09-08 | JIM.COM* 53489221 06/06 | -13643`.
Pela regra literal do mesmo dia, setembro exibiria a previsão de −R$ 136,44 em
06/09 **e** o lançamento real de −R$ 136,43 em 08/09 — o mesmo dinheiro duas
vezes. Com a regra por mês, o calendário mostra só `2026-09-08 | -13643 |
predicted=False`.

Custo do afrouxamento, medido: das 26 séries vivas, **apenas 1** lançamento
casou dentro da janela, e ele está a 2 dias do `due_day`. Nenhuma previsão
legítima foi suprimida.

## Instrumentos do implementer

Nenhum critério ficou dependente da suíte do avaliado. RF-23 e o portão de
testes invocam `pytest` porque os próprios critérios o nomeiam, mas o cenário de
RF-23 foi reproduzido fora da suíte, com banco montado pelo validador sem
`tests/conftest.py`. Todo o resto foi medido com instrumento próprio: `curl`,
Chromium via Playwright, chamada direta a `app.commitments.calendar`, `grep` e
`stat`.

## Apontamentos

Nenhum reprova. Ficam registrados porque quem lê o veredicto não tem a sessão do
validador.

1. **`app/commitments/calendar.py:84-110` — previsão fantasma de parcelamento
   encerrado.** O calendário prevê `2026-10-06 | jim com | -13644 |
   predicted=True`, mas a compra fechou na parcela 06/06 em `2026-09-08`: a
   linha `installment | jim com | installments_left=0 | ends_month=2026-09` não
   deve mais nada. Ela sobrevive em outubro porque o motor mantém **também** uma
   linha `recurring | jim com | -13644` — a média das mesmas cinco cobranças —, e
   `_live_series` a considera viva. A causa está no motor de séries, anterior a
   esta fase, e o número congelado `−R$ 12.802,64` já a inclui. Mas esta é a
   primeira tela em que o dinheiro aparece com **data futura**, e é aí que ele é
   contado de novo. Vira item de fila.
2. **`app/commitments/calendar.py:34` e `:96` — risco latente da chave por mês.**
   `booked` usa `(identidade, "AAAA-MM")`: qualquer lançamento casado à série
   apaga a previsão do mês inteiro, inclusive caindo longe do `due_day` — uma
   cobrança avulsa no dia 5 esconderia o vencimento do dia 25. Medido hoje: 1
   lançamento casado, a 2 dias do previsto, sem dano. Uma tolerância em dias
   fecha o buraco sem reabrir o problema do `jim com`.
3. **Redação de RF-37 — endereçada a quem escreve critério.** "Nenhuma linha em
   nenhum dos dois fluxos" com `grep -R` puro é medida instável:
   `__pycache__/*.pyc` casa por coincidência de bytes e o critério passa a
   reprovar conforme o estado do cache, não do código. Fixar
   `--exclude-dir=__pycache__` — ou trocar por `git grep`, que só vê o
   rastreado — faz o critério medir o que quer medir.
