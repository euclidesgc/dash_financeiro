## 1. O que foi implementado

**Item:** `001-base-e-login` · **Fase:** `2 — Ingestão dos 1.942 lançamentos`

Antes desta fase existia o schema vazio. Agora os 1.942 lançamentos e as 12
contas que já estavam em disco entram no SQLite em **centavos inteiros**, com o
sinal normalizado — negativo é dinheiro saindo, e o saldo de cartão entra como
dívida —, com transferência entre contas próprias e estorno marcados, sem
duplicar quando a ingestão roda de novo, e com cada execução registrada em
`sync_runs`. Fonte e banco são comparados no fim: se divergirem, a gravação é
desfeita e o processo sai com código diferente de zero.

Branch: `001-base-e-login/fase-2-ingestao` · commit `fb1288b`.

---

## 2. Critérios atendidos

Os doze critérios foram executados por um validador cego, que não recebeu plano
nem brief e refez cada medida contra a fonte real. O veredicto integral está em
[`05-veredictos/fase-2.md`](../05-veredictos/fase-2.md).

- [x] `[comando]` RF-06, RF-10 — carga limpa devolve 1.942 transações, 12 contas
      e soma de saldos `-2744971`.
      **Evidência:** `ingested transactions=1942 accounts=12`, exit 0; query →
      `1942 12 -2744971`.
- [x] `[comando]` RF-07 — nenhum valor fracionário gravado.
      **Evidência:** contagem de `typeof(...) <> 'integer'` → `0`.
- [x] `[comando]` RF-08 — o valor de cada linha bate com a fonte, lançamento a
      lançamento.
      **Evidência:** comparação com `data/processed/transacoes.json` → `0`
      divergências.
- [x] `[comportamental]` RF-09 — Dado o lançamento `c5120b3b-…e80cd9`, que a
      Pluggy entrega como `amount: -3310.23` com `type: CREDIT` num cartão,
      quando ele é ingerido, então `amount_cents` é `331023`.
      **Evidência:** premissa reconferida no `data/raw/`; query → `331023`.
- [x] `[comando]` RF-11 — nenhum `pluggy_id` duplicado.
      **Evidência:** `group by … having count(*) > 1` → `0`.
- [x] `[comportamental]` RF-12 — Dado banco inexistente, quando a ingestão roda
      duas vezes, então as contagens não mudam e `sync_runs` tem duas linhas.
      **Evidência:** query → `1942 12 2`, os dois exits 0.
- [x] `[comportamental]` RF-13 — Dado o servidor rodando, quando ele recebe
      `SIGTERM` e sobe de novo, então a contagem de transações continua `1942`.
      **Evidência:** dois ciclos com `timeout -s TERM`; query → `1942`.
- [x] `[comando]` RF-14 — 152 linhas com `is_transfer = 1` e motivo não vazio.
      **Evidência:** query → `152`.
- [x] `[comportamental]` RF-15 — Dado o estorno `8b073fe4-…`, quando a carga
      termina, então há 9 linhas com `is_refund = 1` e o débito anulado aponta
      para o par.
      **Evidência:** query → `9 8b073fe4-d7e9-47e9-a24e-f8b6fcbeac43 -246256`.
- [x] `[comando]` RF-16 — o total de gasto exclui transferência, estorno e
      débito estornado, e bate com o mesmo cálculo feito sobre a fonte.
      **Evidência:** → `-21860413 -21860413`, exit 0.
- [x] `[comportamental]` RF-17 — Dado um arquivo com um lançamento sem `id` e
      outro com valor de milésimo, quando a ingestão roda, então ela sai com
      código 1, nomeia cada rejeição pelo índice e não grava nada.
      **Evidência:** exit 1; stderr com `rejected index=1
      reason=missing_pluggy_id` e `rejected index=2 reason=fractional_cents`;
      `count(*)` → `0`.
- [x] `[comportamental]` RF-18 — Dado um arquivo em que dois lançamentos
      repetem o mesmo `id`, quando a ingestão roda, então a gravação é desfeita,
      `sync_runs` registra a falha e o processo sai com código 1.
      **Evidência:** exit 1; query → `0 failed transactions accepted=3
      written=2 accounts accepted=1 written=1`.

**Portões:** `pytest -q` → `27 passed`, exit 0; `gates_runner.sh` →
`✓ gates: limpos (65 arquivos)`. Lint Python continua **não medido** — não
existe linter declarado no projeto.

---

## 3. Como testar à mão

1. Na raiz, com o `.venv/` populado.
2. `rm -f /tmp/dash-manual.sqlite && rtk proxy env DASH_DB_PATH=/tmp/dash-manual.sqlite .venv/bin/python -m app.ingest`
3. **Esperado:** `ingested transactions=1942 accounts=12`, código de saída 0.
4. Repita o mesmo comando.
5. **Esperado:** a mesma linha; a contagem não muda e `sync_runs` passa a ter
   duas linhas.
6. `rtk proxy env DASH_DB_PATH=/tmp/dash-manual.sqlite .venv/bin/python -m app.query "select count(*) from transactions, (select count(*) from accounts), (select sum(balance_cents) from accounts)"`
7. **Esperado:** `1942 12 -2744971` — a posição líquida de −R$ 27.449,71
   congelada em 05/09/2026, agora somada pelo banco.

---

## 4. Divergências

nenhuma

---

## 5. Raio de impacto

> **Conjunto de candidatos, não verdade.** A precisão medida do raio de impacto
> é **0,578** — cerca de 42% dos candidatos são falso-positivo. Os confirmados
> abaixo foram lidos; os candidatos, não.

**Confirmados** (lidos, a dependência existe):

- `app/ingest/money.py:10` — `to_cents` usa `Decimal(str(value))`, e é a única
  porta de conversão de reais para centavos. Toda soma do produto depende de
  ela não arredondar por conta própria.
- `app/ingest/loader.py:64` — `ingest` é transação única com desfazimento; o
  item `006-sync-pluggy` vai chamá-la com a fonte vinda da API em vez do
  arquivo, e o contrato de `IngestResult` é o que ele consome.
- `app/queries/spending.py:12` — `total_spending_cents` é a primeira consulta de
  agregação do produto e já aplica a invariante 25 (transferência e estorno
  fora do gasto). O item `002-gastos-tres-eixos` parte dela.
- `app/migrations/sql/001_schema.sql` — consumido, não alterado.

**Candidatos** (não conferidos):

- `ingestao/pluggy_consolidate.py` — continua sendo quem produz
  `data/processed/transacoes.json`. Esta fase o lê e não o toca.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **`006-sync-pluggy`** — `sync_runs.transactions_count` hoje guarda quantas
  linhas **existem** depois da carga, não quantas entraram naquela execução
  (`app/ingest/loader.py:298`). Medido pelo validador: a segunda ingestão do
  mesmo arquivo grava `1942` sem inserir nada. Nenhum critério deste item cobre
  a semântica, e quem for medir volume sincronizado vai ler o número errado. A
  linha foi acrescentada à descrição do item `006` no `product/roadmap.md`, que
  é onde a coluna ganha consumidor.
