## 1. O que foi implementado

**Item:** `004-resumo-e-projecao` · **Fase:** `1 de 2 — Motor de projeção`

O painel sabia dizer para onde o dinheiro foi. Esta fase é o que ele precisa
para dizer **para onde está indo**: as três posições, os três números do mês e a
série diária dos próximos 45 dias, tudo como função determinística e testada.

A decisão que define a fase, e que quase não foi tomada: **projetar renda
inteira contra gasto pela metade faz a linha subir**. O calendário de 45 dias
traz R$ 17.176,05 de compromisso datado; a renda esperada no mesmo período traz
R$ 24.452,42, porque a janela alcança dois salários. Só com essas duas parcelas
a projeção melhora R$ 7.276,37 e o painel anuncia que o déficit se fecha
sozinho.

O compromisso é só a **parte datável** do gasto. O gasto mensal mediano é
R$ 17.677,46 e o comprometido é R$ 8.026,79: a diferença, **R$ 9.650,67/mês**, é
gasto variável, e é ela que decide o sinal da linha. Cada dia soma três parcelas
— compromisso datado, renda no dia mediano das entradas, e o variável diluído
pelos dias do mês.

Com as três, a posição consolidada vai de **−R$ 27.449,71** a **−R$ 34.441,79**
em 45 dias, passando pelo pior ponto — **−R$ 40.722,95** — em **13/10/2026**.
São **−R$ 6.992,08**, ou cerca de R$ 4.661/mês: a mesma ordem do déficit de
R$ 4.940,72 que `docs/plano.md` mede por caminho independente.

Três posições, nunca uma: **caixa −R$ 10.705,09**, **cartão −R$ 16.744,62**,
**consolidada −R$ 27.449,71**. A soma sozinha esconderia que R$ 16.744,62 é
dívida de cartão a ~51% ao ano.

Branch: `004-resumo-e-projecao/fase-1-motor` · commit `f858133`.

---

## 2. Critérios atendidos

Sete critérios, executados por um **validador cego**. O veredicto integral está
em [`05-veredictos/fase-1.md`](../05-veredictos/fase-1.md).

Ele fez algo que nenhum critério pedia e que vale registrar: pediram-lhe para
julgar um critério reescrito rodando-o contra o commit base, e ele **recusou o
caminho** — `app/projection` não existia lá, então o critério reprovaria por
ausência de alvo, não por discriminação. Em vez disso montou um **teste de
mutação** numa cópia fora do repositório, recortando a janela à mão, e mostrou
que as duas cláusulas reprovam a implementação errada.

- [x] `[comando]` RF-01 a RF-04 — as três posições, e `cash + card ==
      consolidated`.
- [x] `[comando]` RF-05 a RF-08 — `1222621`, `-1767746`, `-545125` e os seis
      meses completos.
- [x] `[comando]` RF-10, RF-12 a RF-15 — 46 dias, começo, fim, pior ponto,
      delta e parcela variável. O pior ponto é **anterior ao último dia**, o que
      prova que o mínimo não é trivial.
- [x] `[comando]` RF-16 — `8 passed`. As duas asserções nomeadas foram lidas no
      fonte, não aceitas pelo nome.
- [x] `[estrutural]` RF-10 — a janela vem de `app.commitments.calendar`; o
      literal `45` não aparece em `app/projection`.
- [x] `[comando]` portão local — `324 passed`; gates limpos, 233 arquivos.
- [x] `[comando]` RF-24 — nenhum dos dez números medidos aparece no código, nos
      dois fluxos de saída.

---

## 3. Como testar à mão

1. `rm -f /tmp/dash-p.sqlite`
2. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-p.sqlite DASH_TODAY=2026-09-05 .venv/bin/python -m app.ingest`
3. Rode, com `DASH_ENV_FILE=/dev/null` e `DASH_DB_PATH=/tmp/dash-p.sqlite`:
   `from app.projection.forecast import forecast` sobre uma conexão ao banco,
   com `today=date(2026, 9, 5)`.
4. **Esperado:** 46 dias, o primeiro em `-2744971` e o último em `-3444179`.
5. Olhe `worst`.
6. **Esperado:** `2026-10-13`, `-4072295` — o fundo do poço é antes do fim da
   janela, porque o salário do dia 14 vem depois dele.

---

## 4. Divergências

Nenhuma. Uma coisa foi **declarada e julgada**: o critério estrutural de RF-10
foi reescrito antes da validação, porque a versão anterior cobrava a constante
`WINDOW_DAYS` dentro de `app/projection` e o motor importa a função `window()`.
O validador julgou por mutação e aceitou — e registrou o limite: a cláusula
proíbe o literal `45`, não a recontagem da janela por outro caminho.

---

## 5. Raio de impacto

**Confirmados** (lidos, a dependência existe):

- `app/projection/position.py` — `positions(conn)`, as três posições a partir de
  `accounts`, agrupadas por `type`.
- `app/projection/monthly.py` — `monthly(conn, today=)` e `median()`. A mediana
  é escolha de modelo, não de gosto: 03/2026 traz R$ 42.210,26 de crédito
  atípico, e a média projetaria uma renda que não existe.
- `app/projection/forecast.py` — a série de 46 dias. **Importa `window` do
  `003`**: mudar a janela lá muda a projeção aqui, que é o que se quer.
- `app/commitments/calendar.py` e `app/commitments/live.py` — o motor lê os dois.
  A correção do item `011` é o que torna esta projeção confiável; sobre o motor
  anterior ela projetaria R$ 4.775,85/mês de dívida que não existe.

**Candidatos** (não conferidos):

- `app/templates/home.html` — a tela provisória do `001`, que a fase 2 substitui.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

- **O vocabulário de tipo de conta ganhou uma segunda fonte.**
  `app/projection/__init__.py` define `BANK` e `CREDIT`, e
  `app/ingest/loader.py:242` — a linha que inverte o sinal do cartão, sustentando
  o invariante 22 — continua comparando com o literal cru. As duas concordam por
  coincidência textual, não por construção. **Vai para a etapa 2.1 da fase 2**,
  que é a próxima vez que este código é aberto; não vira item de roadmap porque
  cabe na fase seguinte e é uma linha.
- **Ainda não há portão de lint para Python.** Sexto validador seguido a
  registrar. Segue como `010-lint-e-formatador-python`.
