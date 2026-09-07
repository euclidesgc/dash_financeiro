# Veredicto — item `004-resumo-e-projecao`, fase 2

**Resultado:** `APROVADO`

Branch: `004-resumo-e-projecao/fase-2-tela` · base `ec9effb`
Data: 2026-09-07 · **Quatro** validadores cegos, agentes novos, em sequência.

Esta fase foi validada quatro vezes porque as três primeiras rodadas acharam
defeitos reais e a implementação foi corrigida entre elas. Está registrado como
`D17` que a régua correta é **uma validação por fase**: achado marcado pelo
próprio validador como "não reprova" vira correção com teste ou linha de
roadmap, não uma rodada nova.

## Portões (quarta rodada, ponta `4682c53`)

| Portão | Resultado |
|---|---|
| lint/analyze | **não existe no projeto** — `pyproject.toml` traz só `pytest` e `httpx`; nenhum job de lint no CI. Declarado, não presumido. |
| testes | **OK** — `337 passed, 2 warnings`, `EXIT=0`, capturado em arquivo. |
| gates | **OK** — `✓ gates: limpos (árvore completa, 242 arquivo(s)).` |

## Critérios — todos cumpridos

- [x] **RF-01 a RF-04, RF-20** — `200`; `Posição consolidada −R$ 27.449,71`,
      `Caixa −R$ 10.705,09`, `Cartão −R$ 16.744,62`, medidos sobre o texto sem
      tags, cada cifra colada ao seu rótulo. Fecham entre si.
- [x] **RF-05, RF-07, RF-08, RF-09** — `R$ 12.226,21`, `−R$ 17.677,46`,
      `−R$ 5.451,25` e a frase que nomeia a janela.
- [x] **RF-11, RF-14, RF-15, RF-18** — partida, chegada e pior ponto com as suas
      datas, e a frase que declara sobre qual posição a linha corre. Delta
      coerente: `−34.441,79 − (−27.449,71) = −6.992,08`.
- [x] **RF-19** — Chromium: 31 elementos, todos na janela, crescentes, sem
      repetição, `quebras aritméticas []`. **A cadeia fecha em `-3444179`, que é
      o número do cabeçalho** — a lista prova o que o painel anuncia.
- [x] **RF-21** — um `href` de cada.
- [x] **RF-23** — base só com migração e seed: `200`, `Nenhum lançamento na
      base.` e o href do próximo ato dentro do próprio bloco vazio.
- [x] **RF-22** — seis medições (375/768/1440, carregando e redimensionando):
      `scrollWidth == innerWidth` em todas, e os 417 nós de `#projecao *` com
      `animationDuration` e `transitionDuration` em `0s`.
- [x] **RF-22 estrutural** — as três capturas, todas acima de 1024 bytes,
      abertas e conferidas contra o que a tela serve.
- [x] **RF-22 comando** — nenhuma cor literal.
- [x] **portão local** — `337 passed`.
- [x] **RF-24** — nenhum dos dez números medidos no código.
- [x] **RF-20 integração** — sem sessão, `302` com `location: /login`.

## O que a caça extra derrubou, rodada a rodada

Cada rodada atacou a promessa da tela com bases sintéticas, e cada uma achou
defeito que nenhum critério cobria:

1. **`_moving` descartava a cauda.** Quando os últimos dias da janela não têm
   renda nem compromisso, a lista parava num saldo anterior ao do cabeçalho —
   e a lista existe para provar aquele número. Não disparava na base real por
   coincidência: 20/10/2026 tem compromisso. Corrigido em `a485f7e`.
2. **O literal `None` na prosa em pt-BR.** `income_day` é nulo quando não há
   entrada observada até a data pedida, e a frase imprimia "a renda esperada no
   dia None". Alcançável por data digitada à mão. Corrigido em `03c3f64`.
3. **A tela se contradizendo no mesmo painel.** Janela sem renda e sem
   compromisso: o cabeçalho anunciava queda de R$ 26.136,05 e o corpo dizia
   "Nenhum movimento previsto". Corrigido em `03c3f64`.
4. **O gasto sem data trocando de sinal.** Sem mês completo, o gasto esperado é
   zero e o comprometido não, e a subtração creditava a diferença como dinheiro
   **entrando**, sob um rótulo que promete gasto, com a aritmética da linha
   fechando. Painel errado com coerência interna é o modo caro de errar.
   Corrigido em `4682c53`, com piso zero.
5. **A frase da mediana prometendo seis meses inexistentes.** Mesma raiz do
   anterior. Corrigido em `4682c53`.

## O que aguentou o ataque (quarta rodada)

Registrado para não virar dívida de investigação: cauda silenciosa, janela
inteiramente silenciosa, base sem entrada observada, primeira ingestão com
movimentação só no mês corrente, e as datas `2020-01-01`, `1900-01-01`,
`2099-12-31`, `banana`, `2026-13-45`, vazia, `2026-02-30`, `%3Cscript%3E` e
`2026-09-05T00:00` — todas `200`, nenhum 500, nenhuma troca de sinal, nenhuma
contradição, e a última linha da lista batendo com o cabeçalho nas oito bases.

## Apontamentos da quarta rodada — corrigidos em `1a6bd37`

Todos marcados pelo validador como "não reprova". Corrigidos com teste em vez de
virarem dívida, porque os quatro são a tela dizendo algo que não é:

1. **O rótulo `Hoje` sobre uma data que não é hoje.** Os saldos são sempre os
   atuais — não se guarda histórico de saldo —, então `?data=2020-01-01` servia
   "Hoje −R$ 27.449,71" sobre 01/01/2020. Virou **Ponto de partida**, e a tela
   diz que a posição é a atual sempre que a data pedida não é a de hoje.
2. **Data ilegível engolida em silêncio.** `/?data=banana` respondia `200` com o
   painel de hoje, sem avisar. O fallback continua; o aviso passou a existir.
3. **A última linha da janela sem nada embaixo.** Ela existe para a lista
   alcançar o saldo do cabeçalho; agora diz isso.
4. **A prosa prometendo três parcelas onde duas são zero.**

## Instrumentos do implementer

Um critério depende da suíte do avaliado, por definição própria: o portão local,
que **é** `pytest -q`. Os outros onze foram medidos com instrumento
independente — `curl` contra o servidor real, Chromium dirigido pelo validador,
`grep`, `stat` e bases sintéticas construídas por ele.
