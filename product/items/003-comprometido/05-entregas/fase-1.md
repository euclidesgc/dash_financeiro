## 1. O que foi implementado

**Item:** `003-comprometido` · **Fase:** `1 — Motor de compromissos`

A migração `004` traz `commitments` e a marca de dispensa. O motor detecta
recorrência e parcelamento **a partir das transações no banco** — não do JSON
congelado —, aplica a **janela de vida** de um mês, prevê o dia pela mediana dos
dias observados, calcula data de término e caixa liberado, e recomputa de forma
idempotente em transação única.

O que a janela de vida compra, medido: a conta ingênua diz que 32 parcelamentos
ainda têm parcelas a vencer; com a janela sobram **6**, somando **R$ 374,82/mês**.
`IPVA parcela 1 de 3`, visto pela última vez em 26/01/2026, deixa de ser
compromisso. As 26 séries mortas que ele arrastava consigo inflavam o total do
mês sem que um único real fosse sair da conta.

Branch: `003-comprometido/fase-1-motor` · commits `d5156b1` e `9d0f3bf`.
Reprovou na primeira rodada — por dois critérios errados, não pelo código.

---

## 2. Critérios atendidos

Os catorze critérios, executados por validador cego. Veredicto integral em
[`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md); o da primeira rodada em
[`fase-1-reprovada-1.md`](../05-veredictos/fase-1-reprovada-1.md).

Os números que a fase entrega, todos medidos contra a base de 05/09/2026:
**55 recorrentes** somando **R$ 12.427,82/mês**; **96 séries parceladas**
detectadas, das quais **6 vivas** somando **R$ 374,82/mês**; `DEBITO PRESTACAO
HAB` com média de R$ 2.467,20 em 9 meses, 4 consecutivos; as recorrentes de
categoria de serviço somando R$ 2.245,69/mês, **nenhuma** delas tratada como
cancelável pelo código; `MERCADOLIVRE` de R$ 127,27 com 22 restantes e término em
06/2028; `Assai 232 Macae` terminando em 10/2026.

Atomicidade provada duas vezes: pela suíte e pelo próprio validador, que
substituiu a detecção por uma função que levanta erro e conferiu, **em conexão
nova reaberta**, que as 151 linhas continuam idênticas — o rollback é real em
disco, e não é vácuo, porque a recomputação apaga a tabela antes da etapa que
quebra.

---

## 3. Como testar à mão

1. `rm -f /tmp/dash-c.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-c.sqlite DASH_TODAY=2026-09-05 .venv/bin/python -m app.ingest`
2. **Esperado:** `commitments recomputed: 151 reference=2026-09-05`.
3. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-c.sqlite .venv/bin/python -m app.query "select kind, count(*), sum(amount_cents) from commitments group by kind"`
4. **Esperado:** `installment 96` e `recurring 55 -1242782`.

---

## 4. Divergências

nenhuma

Duas correções de critério antes da validação, como erro material: o critério de
`RF-03` dependia de `calendar`, que é entrega da fase 3, e o de `RF-06/07` exigia
155 séries onde 55 recorrentes + 96 parceladas dão 151.

E uma correção de número no brief: `RF-12` dizia 100 séries parceladas, e a
realidade dá **96** — quatro das 100 que o `parcelamentos.json` conta não têm
nenhum lançamento de gasto (três são parcelamento de fatura, marcado
`is_transfer`, e uma é compra estornada), e o filtro da invariante 25 as exclui.

---

## 5. Raio de impacto

**Confirmados** (lidos):

- `app/commitments/engine.py` — `recompute(conn, today=)` é o ponto único de
  materialização. Apaga e regrava `commitments` numa transação, reaplicando as
  marcas de dispensa.
- `app/commitments/live.py` — a janela de vida. É a diferença entre 32 e 6, e é
  leitura, não gravação: mudar a data de referência muda o conjunto sem tocar no
  banco.
- `app/commitments/schedule.py` — `median_day` e `on_month`. A fase 3 monta o
  calendário sobre elas.
- `app/config.py` — `reference_date()` lê `DASH_TODAY`. Sem ela, o CLI seguia o
  relógio da máquina e o mesmo comando produzia outro resultado em outro dia.
- `app/migrations/sql/004_commitments.sql` — o contrato que as fases 2 e 3 leem.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **O envelope do validador vaza pelo branch.** O ponteiro do diff inclui
  `product/items/<id>/`, então o branch carrega o brief, o plano e — pior — o
  veredicto anterior da mesma fase. A cegueira valeu por disciplina do validador,
  não por construção. Vai para `.harness/proposals/`, porque é defeito do harness,
  não deste produto.
