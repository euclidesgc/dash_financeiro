## 1. O que foi implementado

**Item:** `007-objetivo-e-linha-do-tempo` · **Fase:** `1 de 1`

`GET /objetivo` dá ao produto o que faltava: **um alvo, um caminho e um
passado**.

**O alvo é derivado, não decretado.** Seis meses do piso de sobrevivência, e o
piso é o cruzamento `fixa × essencial` que o item `002` já calcula:
**R$ 6.979,93/mês**, logo **R$ 41.879,58** de reserva. Ele se move quando o piso
se move, que é o comportamento que se quer de um alvo — o `docs/plano.md` estima
≈R$ 49.400 por outro caminho, e a tela calcula o seu e diz de onde ele vem.

**Nenhum cenário é o outro vezes uma porcentagem.** Cada um soma uma alavanca que
o produto já mede e que nomeia um ato: as assinaturas marcadas, a lista de corte,
o caixa que os parcelamentos liberam **ao acabar**. O número de cabeçalho é o
estado estacionário que o cenário promete; a simulação é o caminho até ele,
escalonando cada alavanca no mês em que ela realmente chega.

**E a tela diz "nunca" quando é nunca.** Com resultado mensal negativo nenhum
cenário alcança o objetivo, e os meses ficam **nulos** — não um número enorme,
que se leria como uma data distante. O que a tela mostra no lugar é o único
número acionável que sobra: **faltam R$ 4.523,21 por mês** para que exista uma
data.

O financiamento imobiliário fica de fora: a 0,72% a.m. é a dívida mais barata da
escada, e amortizá-lo antes de ter reserva é trocar segurança por uma taxa que
não está doendo.

Branch: `007-objetivo/fase-1-linha-do-tempo` · commits `70bdd78`, `bfc1ecf`,
`1295a5c`, `f0e2c1a`.

**Capturas** em `06-capturas/`.

---

## 2. Critérios atendidos

Catorze critérios, **três validadores cegos**, duas reprovações e uma escalada
diagnosticada. O veredicto integral, com tudo o que cada rodada derrubou, está em
[`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

Vale ler: as duas reprovações acharam **quatro erros que antecipavam ou
inventavam a data** — um `500` por data ISO válida, um mês que ia todo para a
dívida e ainda alimentava a reserva, uma escada limpa reportada no mês 1 em vez
de 0, e o caixa liberado aplicado antes de existir. Num item cuja unidade é
**dia**, errar a data é errar o produto.

---

## 3. Como testar à mão

1. Prepare `/tmp/dash-o.sqlite` com `app.ingest` e `app.auth.seed`.
2. Abra `http://127.0.0.1:8000/objetivo?data=2026-09-05`.
3. **Esperado:** alvo `R$ 41.879,58`, resultado mensal `−R$ 4.523,21`, e os três
   cenários com **não chega**.
4. Leia o bloco vazio.
5. **Esperado:** "Faltam R$ 4.523,21 por mês para que exista uma data".
6. Leia o aviso abaixo dos cenários.
7. **Esperado:** "Ficam de fora 6 dívida(s), somando −R$ 27.934,80".
8. Abra `?data=2026-10-05` e volte a `?data=2026-09-05`.
9. **Esperado:** dois pontos na linha do tempo, com **reservas alvo
   diferentes** — ela se move com a janela, e a série mostra isso.

---

## 4. Divergências

Nenhuma. Duas reprovações, uma escalada com diagnóstico `criterio` registrado em
`D8`, e um defeito latente da terceira rodada corrigido com teste depois do
veredicto — nomeado no veredicto e aqui.

---

## 5. Raio de impacto

- `app/migrations/sql/007_plan.sql` — `plan_snapshots`, com `months_to_objective`
  **nulável** de propósito.
- `app/plan/objective.py` — piso, alvo, resultado mediano e as alavancas.
- `app/plan/timeline.py` — a simulação mês a mês, os três cenários, os marcos e o
  registro. **É aqui que a data nasce.**
- `app/routers/plan.py` — a rota, e a faixa de datas aceitas.
- `app/templates/objetivo.html` — a tela.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **`013-objetivo-cenario-vazio-e-ponto-espurio`**, com os dois apontamentos da
  terceira rodada: o cenário `base` promete dois atos e entrega o número do
  `nada muda` sem dizer que as duas listas estão vazias; e uma data recusada na
  query string grava um ponto permanente na série de progresso, indistinguível
  depois de uma leitura legítima.
