# Veredicto — 002-gastos-tres-eixos, fase 1 (primeira rodada)

VEREDICTO: REPROVADO

> Este é o julgamento da primeira rodada, guardado por honestidade de registro:
> o estado do harness guarda só o último veredicto de cada fase, e uma fase que
> passou na segunda tentativa não deve parecer que passou na primeira. O
> veredicto que vale é o de `fase-1.md`, emitido por um validador novo depois da
> correção.

Portões
  lint/analyze: NÃO EXECUTÁVEL — `ruff` não instalado no `.venv`. Não presumo que passaria.
  testes:       OK — `pytest -q` → "157 passed, 2 warnings in 6.63s", exit 0
  gates:        OK — `✓ gates: limpos (árvore completa, 126 arquivo(s) considerados)", exit 0

Critérios de aceite: treze dos catorze cumpridos com evidência executada contra
a fonte real (RF-01 duas vezes, RF-02/03, RF-04/05, RF-06, RF-07, RF-08, RF-09,
RF-10, RF-11 duas vezes, RF-12 e RF-14).

  [ ] `comportamental` RF-13 — reclassificação ao vivo e cruzamento
      A primeira metade cumpre: `update_rule(conn, 20, essentiality='supérfluo')`
      devolveu `reclassificados = 128`, como o critério exige.
      A segunda metade **não é cumprida**: a função exigida não existe.
      Saída real, no mesmo processo, logo após o `128`:
        Traceback (most recent call last):
          File ".../rf13.py", line 12, in <module>
            import app.queries.crossings as cx
        ModuleNotFoundError: No module named 'app.queries.crossings'
        EXIT=1
      `find app/queries -name "*.py"` → apenas `__init__.py` e `spending.py`.
      Falta o módulo `app/queries/crossings.py` com `crossing(conn, *, slug,
      start, end)`.

Apontamentos
  A tabela `crossings` é criada em `003_taxonomy.sql:35-42` e semeada com as duas
  linhas esperadas, mas nenhum código lê essa tabela: o eixo do cruzamento fica
  semeado e inerte. O dado já está correto — a consulta equivalente escrita à mão
  devolve `Eating out -436013 60`, exatamente o que o critério exige. Falta expor
  isso como `app.queries.crossings.crossing`.

  `app/taxonomy/classify.py:56-60` — a regra de `match_kind='description'` é
  casada contra `payee` (descrição normalizada), não contra `description`. RF-11
  passou porque a normalização preserva `ifood`; registro porque o critério
  compara com `lower(description) like '%ifood%'` e a equivalência é
  circunstancial, não estrutural.
