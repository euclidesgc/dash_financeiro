## 1. O que foi implementado

**Item:** `002-gastos-tres-eixos` · **Fase:** `2 — Agregação pelos cinco eixos`

O banco já sabia classificar; agora sabe responder. Esta fase entrega as
consultas: agregação por **grupo, categoria, beneficiário, natureza e
essencialidade** com período livre, os dois cruzamentos, a série de treze meses
sem buraco e o drill-down de qualquer célula até a transação. Nenhuma tela.

O filtro de gasto — negativo, sem transferência, sem estorno, sem débito
estornado — passou a ser **uma constante única** em `app/queries/spending.py`,
reusada pelos outros módulos de consulta. Estava escrito em três lugares, e um
invariante copiado é um invariante que um dia diverge.

Branch: `002-gastos-tres-eixos/fase-2-agregacao` · commit `eb90a99`.

---

## 2. Critérios atendidos

Os treze critérios foram executados por um validador cego contra os 1.942
lançamentos reais, com os comandos que eles próprios declaram. O veredicto
integral está em [`05-veredictos/fase-2.md`](../05-veredictos/fase-2.md).

- [x] `[comando]` RF-15, RF-16 — o eixo grupo devolve `−R$ 103.772,33` em 732
      lançamentos. **Evidência:** `True -10377233 732`.
- [x] `[comando]` RF-17 — as 52 categorias, e as dez primeiras na ordem exata,
      de `School −R$ 12.992,18` a `Shopping −R$ 4.178,70`.
- [x] `[comando]` RF-10, RF-18 — os 317 beneficiários, com `debito prestacao
      hab` no topo.
- [x] `[comando]` RF-19 — PIX e boleto a terceiros contam como gasto.
      **Evidência:** `-468515 58 -523959 1`.
- [x] `[comando]` RF-20, RF-21 — os cinco eixos reparticionam o mesmo total e
      nenhuma linha é positiva. **Evidência:** `5 {-10377233} 0`.
- [x] `[comportamental]` RF-23 — período invertido e data impossível levantam
      `InvalidPeriodError` com mensagem que nomeia o valor.
- [x] `[comportamental]` RF-24 — eixo desconhecido levanta `UnknownAxisError`
      listando os eixos aceitos.
- [x] `[comando]` RF-25 — o cruzamento `corte` responde com o rótulo
      `variável × supérfluo`. **Ver a seção 7: ele responde vazio, e isso é o
      achado mais importante desta fase.**
- [x] `[comando]` RF-26 — o cruzamento `piso` devolve `−R$ 41.879,60` no período
      e média mensal de `−R$ 6.979,93`, conferida à mão.
- [x] `[comando]` RF-27 — a série tem 13 pontos, de `2025-08` a `2026-08`, e
      `2026-08` vale `−R$ 19.217,11`.
- [x] `[comando]` RF-28 — mês sem gasto vale zero e não some da série.
      **Evidência:** o validador corroborou por fora, pedindo uma janela em que
      a base não tem nenhuma transação: 13 pontos, todos zero.
- [x] `[comportamental]` RF-29, RF-30 — o drill-down de `School` abre 20
      transações que somam exatamente a linha agregada.
- [x] `[comando]` RF-22 — nenhum número congelado aparece em código de `app/`.

**Portões:** `pytest -q` → `204 passed`, exit 0.

---

## 3. Como testar à mão

1. `rm -f /tmp/dash-ag.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-ag.sqlite .venv/bin/python -m app.ingest`
2. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-ag.sqlite .venv/bin/python -c "from app.db import connect; from app.queries.axes import aggregate; [print(e, sum(l['amount_cents'] for l in aggregate(connect(), axis=e, start='2026-03-01', end='2026-08-31'))) for e in ('grupo','categoria','beneficiario','natureza','essencialidade')]"`
3. **Esperado:** os cinco eixos imprimindo o mesmo `-10377233`.

---

## 4. Divergências

nenhuma

Uma correção de erro material foi feita nos documentos, e está registrada como
`D9`: a lista do `RF-17` omitia `Transfer - Bank Slip` e `Transfer - PIX`,
embora o `RF-19` do mesmo brief mandasse contá-las como gasto — o documento se
contradizia sozinho, e a correção era única. Erro material com uma só correção
possível é reconciliação direta; divergência é para quando existem caminhos com
impactos diferentes.

---

## 5. Raio de impacto

> **Conjunto de candidatos, não verdade.** Precisão medida: **0,578**.

**Confirmados** (lidos):

- `app/queries/axes.py` + `app/queries/axes.json` — `aggregate(conn, *, axis,
  start, end)`. Os nomes dos eixos e o mapa para a coluna moram no arquivo de
  dados, porque `essencialidade` contém `essencial`, termo do vocabulário, e
  nenhum termo pode aparecer como literal em código.
- `app/queries/period.py` — `InvalidPeriodError` e o parse de data, reexportados
  por `axes.py` e reusados por `series.py`.
- `app/queries/series.py` — `monthly_series`, que gera os meses e faz `LEFT
  JOIN`: é o que garante que mês sem gasto valha zero em vez de sumir.
- `app/queries/spending.py` — a constante única do filtro de gasto. Toda
  consulta nova do produto parte dela.
- `tests/test_frozen_numbers.py` — o varredor que impede número congelado de
  virar constante em `app/`, com o caso que planta o número num arquivo
  temporário e prova que o varredor morde.

**Candidatos** (não conferidos):

- `app/taxonomy/classify.py` — ainda tem a própria cópia do filtro de gasto,
  porque estava fora do escopo desta fase. É a única repetição que sobrou.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **A lista de corte nasce vazia, e a tela precisa dizer isso.** O validador
  mediu: nenhuma das 1.942 transações tem essencialidade `supérfluo`, porque
  nenhuma das 80 regras semeadas a atribui — consequência direta da decisão `D2`
  (seed conservador, que não decide pelo dono o que a família dele pode cortar).
  O cruzamento `corte` devolve zero linhas para qualquer período, e o critério
  que o cobre passa nesse vazio: sobre lista vazia, "ordenado" é vacuamente
  verdadeiro e "soma igual ao total" vira `0 == 0`.
  **Não virou item de roadmap**: virou requisito `RF-48` deste mesmo item, com
  critério na fase 3. A tela declara que nada foi marcado como supérfluo,
  aponta a tela de Regras como próximo ato e lista as cinco maiores categorias
  de `variável × importante` como candidatas — `Services` −R$ 8.774,12,
  `Transfers` −R$ 6.220,71, `Transfer - Bank Slip` −R$ 5.239,59, `Transfer -
  PIX` −R$ 4.685,15 e `Eating out` −R$ 4.360,13. Decisão registrada como `D10`.
- **`app/taxonomy/classify.py` mantém a própria cópia do filtro de gasto.** A
  extração ficou fora do escopo desta fase. Fica registrado aqui; a fase 4 toca
  esse arquivo e é a hora barata de fechar.
