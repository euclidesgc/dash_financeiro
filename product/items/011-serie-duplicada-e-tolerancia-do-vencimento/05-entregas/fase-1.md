## 1. O que foi implementado

**Item:** `011-serie-duplicada-e-tolerancia-do-vencimento` · **Fase:** `1 de 1 — Integridade das séries`

O item `003` entregou a tela de Comprometido com o número de cabeçalho em
**−R$ 12.802,64**. Ele estava errado em quatro lugares ao mesmo tempo. Agora é
**−R$ 8.026,79** — de um gasto mensal médio de R$ 17.295, a diferença entre ler
74% do mês já vendido antes de ele começar e ler 46%.

Os quatro defeitos, todos em `app/commitments/`, todos com a mesma consequência:

1. **Parcelamento que acabava ressuscitava como assinatura.** A precedência do
   parcelamento sobre a recorrência só valia enquanto sobrava parcela a vencer.
   No mês em que a última parcela caía, a série deixava de "dever", a precedência
   soltava, e a linha recorrente — construída a partir daquelas mesmas cobranças
   — voltava a cobrar a dívida encerrada. Eram quatro chaves,
   **R$ 368,61/mês**.
2. **Uma compra virava duas séries por causa de um centavo.** A chave incluía o
   valor exato da parcela, e a primeira parcela quase sempre difere das demais
   por arredondamento — `jim com` tinha parcelas de R$ 136,47 e R$ 136,43,
   **0,03%** de diferença. A metade velha ficava "devendo" cinco parcelas de uma
   compra já quitada. Eram **96 séries para 66 compras**; agora são 74.
3. **O total somava assinatura que parou de ser cobrada.** O invariante que o
   `003` escreveu para parcelamento — *compromisso que não existe mais inflando o
   total é pior que não ter a tela* — não estava aplicado a assinatura. Eram 25
   séries, **R$ 2.739,97/mês**.
4. **A janela de vida marcava como morto o que está no futuro.** Ela era um
   conjunto de dois rótulos de mês, e fatura de cartão chega com parcela lançada
   meses adiante. Virou um **piso de data**: o passado remoto sai, o futuro
   entra, com uma comparação só. São **15** séries de parcelamento com cobrança
   datada adiante.

E o calendário deixou de casar lançamento com previsão pelo mês, passando a casar
por **distância entre datas completas** — que atravessa a virada do mês, e por
isso lê uma série que vence no dia 29 e é cobrada no dia 1º como dois dias de
distância, não vinte e oito.

Branch: `011-serie-duplicada/fase-1-integridade` · commit `4faaeb9`.

---

## 2. Critérios atendidos

Os quinze critérios foram executados por um **validador cego** — agente novo, sem
plano, sem brief, sem veredictos. O veredicto integral está em
[`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

O que ele fez de mais forte, e que nenhum critério pedia: **extraiu a árvore do
commit base e rodou o código anterior sobre o mesmo dataset**. Ele devolve
`96 / 55`, `151` e `4` — contra os `74 / 41`, `115` e `0` exigidos. O critério
reprova a implementação anterior, e é isso que separa um critério que mede de um
que descreve.

- [x] `[comando]` RF-02, RF-07, RF-25 — `installment 74`, `recurring 41`,
      `115` linhas, `66` pares distintos, `0` linhas fantasmas.
- [x] `[comportamental]` RF-03, RF-24, RF-25 — `−R$ 8.026,79` e `R$ 0,00` na
      tela, `12.802,64` com zero ocorrências, `R$ 233,76` em
      `id="caixa-liberado"`. **Reconciliado contra o banco:** `-779303` mais
      `-23376` dá `-802679`; as três linhas de caixa liberado somam `-23376`.
- [x] `[comando]` RF-01, RF-04 — `6 passed`. Série cobrada dentro da janela sem
      parcela a vencer não deixa linha recorrente; cobrada fora da janela, deixa.
- [x] `[comando]` RF-05, RF-06, RF-08, RF-09 — `12 passed`. Quatro centavos de
      diferença não partem a compra; 45% de diferença partem.
- [x] `[comando]` RF-10 a RF-14 — `13 passed`. Lançamento a 20 dias do previsto
      não apaga a previsão; a série do dia 29 cobrada no dia 1º aparece uma vez.
- [x] `[comando]` RF-22 a RF-25 — vivas `16`, parcelamentos vivos `5`, paradas
      `25` somando `-273997`, futuras `installment 15`.
- [x] `[comportamental]` RF-15 — DOM real: 28 dias, 59 entradas, `jim com` uma
      vez só, em `2026-09-08`, `-13643`, `já lançado na conta`.
- [x] `[comportamental]` RF-18 — as três dispensas continuam devolvendo
      exatamente `R$ 1.099,63`, sem reingestão e sem reinício.
- [x] `[estrutural]` RF-05, RF-11, RF-16, RF-17, RF-22 — as quatro constantes em
      escopo de módulo, com os valores declarados.
- [x] `[comportamental]` RF-16, RF-17 — o piso alcança um mês e atravessa a
      virada do ano; a janela do calendário continua em 45 dias.
- [x] `[comando]` portão local — `316 passed`; gates limpos, 222 arquivos.
- [x] `[comando]` RF-19 — **stdout 0 bytes, stderr 0 bytes**, medidos com `wc -c`.
- [x] `[comando]` RF-20 — `115` → recompute → `115` → recompute → `115`.
- [x] `[estrutural]` RF-21, RF-26, RF-27 — os dois canônicos do `003` limpos e
      citando o `011`; o plano do `003` intacto com nota no topo; `docs/plano.md`
      byte a byte igual.

---

## 3. Como testar à mão

1. `rm -f /tmp/dash-cal.sqlite`
2. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-cal.sqlite DASH_TODAY=2026-09-05 .venv/bin/python -m app.ingest`
3. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-cal.sqlite LOGIN=teste PASSORD=senha-teste-9k2 .venv/bin/python -m app.auth.seed`
4. Suba com as mesmas variáveis mais `SESSION_SECRET=segredo-de-teste-7h4`, entre e abra `http://127.0.0.1:8000/comprometido?data=2026-09-05`.
5. **Esperado:** `−R$ 8.026,79` como total comprometido.
6. Procure `jim com` no calendário.
7. **Esperado:** uma única linha, em `08/09/2026`, `já lançado na conta`,
   −R$ 136,43 — e nada em 06/10/2026, porque a compra acabou.
8. Role até **Caixa liberado**.
9. **Esperado:** três marcos — R$ 68,72 em 12/2026, R$ 37,77 em 12/2027 e
   R$ 127,27 em 06/2028 —, somando R$ 233,76.

---

## 4. Divergências

Nenhuma. Duas coisas foram **declaradas e julgadas**, ambas aceitas:

- **Os números dos critérios foram reescritos contra a medição, depois de a
  implementação existir.** A previsão do brief dizia −R$ 9.553,00; a medição deu
  −R$ 8.026,79, porque a precedência passou a usar o mesmo piso de data da
  liveness e isso derrubou mais 10 linhas recorrentes que eram duplicata de
  parcelamento com cobrança datada adiante. Corrigir antes da validação é o
  oposto de esconder — e o validador provou que os critérios corrigidos ainda
  reprovam o código anterior.
- **O `03-plan.md` do `003` não foi reconciliado.** Os critérios de um plano
  executado são o registro do que a fase foi medida contra, e os veredictos citam
  a saída daqueles comandos. Reescrevê-los tornaria os veredictos inverificáveis.

---

## 5. Raio de impacto

**Confirmados** (lidos, a dependência existe):

- `app/commitments/live.py` — `live_floor` substituiu `live_months`, e `totals`
  passou a somar só o vivo. **É este arquivo que define o que "comprometido"
  significa**, e o item `004` projeta saldo em cima do que ele devolve.
- `app/commitments/series.py` — `SAME_PURCHASE_DEVIATION` e a separação por
  agrupamento dentro de `(beneficiário, total)`.
- `app/commitments/engine.py` — a precedência olha a janela, nunca o que se deve.
- `app/commitments/calendar.py` — `DUE_TOLERANCE_DAYS` e o casamento por
  distância entre datas; `charged()` alimenta o lado dos lançamentos.
- `app/commitments/schedule.py` — `months_before` foi removida: depois do piso de
  data ela ficou sem chamador em produção.
- `product/items/003-comprometido/00-discovery.md` e `01-brief.md` — reconciliados
  no presente, com âncora de uma linha para este item.

**Candidatos** (não conferidos):

- `app/templates/fragments/comprometido_*.html` — não mudaram; a tela lê o que o
  motor devolve.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **Âncora de dígito vale menos que âncora de identidade.** O validador
  registrou que `−R$ 8.026,79` prova estabilidade, não correção financeira. Para
  o `004`: escrever pelo menos um critério que fixe a **identidade** — o total é
  a soma das vivas não dispensadas mais os parcelamentos em aberto — e não só o
  dígito. Não vira item de roadmap: vira régua de quem escreve critério, e está
  no prompt da próxima sessão.
- **O despacho do validador vazou envelope.** A seção "declarações do
  implementador" levava um número de histórico de planejamento. Anotado em
  `.harness/proposals/2026-09-06-004.md`, que já trata do vazamento pelo branch.
- **Ainda não há portão de lint para Python.** Quinto validador seguido a
  registrar. Segue como `010-lint-e-formatador-python`, na dívida técnica.
