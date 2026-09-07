## 1. O que foi implementado

**Item:** `004-resumo-e-projecao` · **Fase:** `2 de 2 — Tela de Resumo`

A raiz do painel deixa de ser um placeholder. `GET /` agora responde a pergunta
que o produto existe para responder: **onde você está, e para onde isto vai**.

- **Três posições, nunca uma.** Consolidada `−R$ 27.449,71`, caixa
  `−R$ 10.705,09`, cartão `−R$ 16.744,62`. A soma sozinha esconde que
  R$ 16.744,62 é dívida de cartão a ~51% ao ano e o resto é cheque especial.
- **O mês típico**, por mediana e não por média: renda `R$ 12.226,21`, gasto
  `−R$ 17.677,46`, e **quanto sobra: −R$ 5.451,25**. A tela não suaviza.
- **Os próximos 45 dias**, sobre a posição consolidada, com o **pior ponto**
  nomeado — `−R$ 40.722,95` em 13/10/2026 —, porque é ele que decide se o mês
  entra no cheque especial, não o valor do último dia.
- **A lista prova o cabeçalho.** Cada dia com movimento traz o que entra, o que
  sai e o saldo, e a soma fecha linha a linha até o número anunciado no topo.

A tela mínima do `001` (`app/routers/pages.py`, `app/templates/home.html`) foi
removida.

Branch: `004-resumo-e-projecao/fase-2-tela` · commits `3771d6d`, `a485f7e`,
`03c3f64`, `4682c53` e `1a6bd37`.

**Capturas** (em `06-capturas/`): `resumo-375.png`, `resumo-1440.png`,
`resumo-dark-1440.png`.

---

## 2. Critérios atendidos

Doze critérios, executados por **quatro validadores cegos em sequência** — o
veredicto integral, com o que cada rodada derrubou, está em
[`05-veredictos/fase-2.md`](../05-veredictos/fase-2.md).

Todos cumpridos na quarta rodada, com destaque para o que mais importa:
**`quebras aritméticas []`** nos 31 dias listados, e a cadeia fechando em
`-3444179` — que é exatamente o `−R$ 34.441,79` do cabeçalho. A lista prova o
número que o painel anuncia, que é a promessa central desta tela.

---

## 3. Como testar à mão

1. Prepare `/tmp/dash-r.sqlite` com `app.ingest` (`DASH_TODAY=2026-09-05`) e `app.auth.seed`.
2. Suba o app e abra `http://127.0.0.1:8000/?data=2026-09-05`.
3. **Esperado:** três posições com nome próprio, o mês típico e a linha de 45 dias.
4. Some à mão as parcelas de um dia da lista e compare com o saldo ao lado.
5. **Esperado:** igual ao centavo, e a última linha igual ao "Em 45 dias" do topo.
6. Abra `/?data=banana`.
7. **Esperado:** `200`, com aviso de que a data foi recusada e a tela responde por hoje.

---

## 4. Divergências

Nenhuma. Cinco defeitos foram achados pelos validadores e **corrigidos antes do
merge**, cada um com teste que falha sem a correção. Estão listados no veredicto.

---

## 5. Raio de impacto

**Confirmados:**

- `app/routers/summary.py` — a rota `/`. `_moving` decide quais dias a lista
  mostra e é onde a soma exibida deixa de fechar se alguém mexer sem cuidado.
- `app/templates/resumo.html` e os dois fragmentos — a tela e a linha do tempo.
- `app/accounts.py` — **novo**, e é a casa do vocabulário `BANK`/`CREDIT`. A
  inversão de sinal do cartão na ingestão e a soma por tipo na projeção precisam
  concordar sobre a mesma string.
- `app/main.py` — `pages` saiu, `summary` entrou.
- `app/static/css/app.css` — a classe `.figure`.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

Nenhuma nova. As cinco encontradas pelos validadores foram corrigidas nesta
fase, não adiadas.

- **Ainda não há portão de lint para Python.** Sétimo, oitavo, nono e décimo
  validadores a registrar. Segue como `010-lint-e-formatador-python`.
