## 1. O que foi implementado

**Item:** `012-sync-pos-carga-atomica` · **Fase:** `1 de 1`

O item `006` matou a sincronização que falha **em silêncio**. Sobrou o caminho em
que ela falha **mentindo**, que é pior.

A reclassificação, o recálculo de compromissos e a reconstrução da escada rodavam
**depois** de a linha `ok` já estar gravada e **fora** de qualquer tratamento. Uma
exceção ali derrubava a rota com `500` e deixava um `sync_runs` afirmando sucesso
com as tabelas derivadas paradas: o dono lia a tela seguinte marcada como
sincronizada, com os números do estado anterior.

Agora a execução é **rebaixada**, não desfeita. Desfazer jogaria fora lançamentos
que entraram corretamente, e a carga é idempotente — a próxima sincronização os
reencontra. Rebaixar diz a verdade sobre a execução que aconteceu.

Branch: `012-sync-pos-carga/fase-1` · commits `e73a1af` e `1cfadf0`.

---

## 2. Critérios atendidos

Cinco critérios, **um validador cego**. Veredicto em
[`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

Ele fez duas coisas que nenhum critério pedia. Primeiro, **quebrou os três passos
reais** um a um, em vez de aceitar o teste que substitui `_after` inteiro, e leu o
banco direto nos três casos. Segundo, pegou um **passe falso do portão de gates**
— `0 arquivo(s) considerados` numa árvore sem `.git` — e reexecutou depois de
corrigir, em vez de aceitar o `EXIT=0`.

E registrou uma falha operacional minha: **troquei de branch durante a validação
dele**, quebrando o ponteiro do despacho. Ele contornou exportando o ref e
conferindo a identidade por hash. A regra ficou registrada em `D4`.

---

## 3. Como testar à mão

1. Prepare `/tmp/dash-x.sqlite` com `app.ingest`.
2. Quebre um dos três passos da pós-carga (`classify_all`, `recompute`, `rebuild`).
3. Rode `python -m app.sync`.
4. **Esperado:** a última linha de `sync_runs` em `failed`, com
   `pós-carga falhou: <Exceção>`.
5. Aperte **Sincronizar agora** na tela com a pós-carga quebrada.
6. **Esperado:** `200`, não `500`, com *"os lançamentos entraram, mas a
   classificação e os compromissos não foram recalculados até o fim"*.

---

## 4. Divergências

Nenhuma. Dois apontamentos corrigidos com teste depois do veredicto, nomeados nele.

---

## 5. Raio de impacto

- `app/sync/__init__.py` — o `try` em volta de `_after` e `_demote`, que agora
  **nomeia a própria linha**.
- `app/ingest/loader.py` — `IngestResult.run_id`: o id da linha que a execução
  gravou. Quem precisar corrigi-la depois tem de nomeá-la.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

Nenhuma.
