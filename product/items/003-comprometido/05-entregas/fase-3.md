## 1. O que foi implementado

**Item:** `003-comprometido` · **Fase:** `3 — Calendário de vencimentos`

A tela de Comprometido já dizia **quanto** está vendido antes do mês começar.
Faltava **quando**. Esta fase acrescenta o calendário dos próximos 45 dias: um
bloco por dia com vencimento, o que sai naquele dia, a soma do dia, e — em cada
linha — se aquilo é previsão ou lançamento que já está na conta.

A janela é de 45 dias porque é a mesma que a projeção do item `004` vai
consumir, e ela nasce aqui em vez de ser recortada na tela.

Três decisões de leitura, e nenhuma delas é cosmética:

- **A data é previsão, e a tela diz isso em texto**, não em asterisco: *"A data
  de cada vencimento é previsão a partir do histórico, não data contratual."* A
  mediana erra o dia — `debito prestacao hab` caiu nos dias 6, 16, 17, 18, 19, 28
  e 31 ao longo de nove meses. Número que parece exato e não é destrói a
  confiança no resto da tela.
- **O que já foi lançado aparece como lançado.** `JIM.COM* 53489221 06/06` sai
  em `08/09/2026` com a etiqueta `já lançado na conta` e o valor real de
  −R$ 136,43, em vez da previsão de −R$ 136,44 no dia 6.
- **O calendário declara quantas séries ficaram de fora.** Das assinaturas
  detectadas, **35** não têm cobrança recente e por isso não têm próximo
  vencimento a prever. Sem essa linha, um calendário curto se lê como um mês
  tranquilo.

Na base congelada de 05/09/2026, a janela vai de **05/09/2026 a 20/10/2026** e
traz **27 dias** com **42 vencimentos**.

Branch: `003-comprometido/fase-3-calendario` · commits `ce4aa69`, `fdefd4b` e
`6ce6056`.

**Capturas** (em `06-capturas/`): `comprometido-calendario-375.png`,
`comprometido-calendario-1440.png`, `comprometido-calendario-dark-1440.png`.

---

## 2. Critérios atendidos

Os oito critérios foram executados por um **validador cego** — agente novo, sem
plano, sem brief, sem os veredictos anteriores desta fase, com o diff restrito a
`app` e `tests`. Ele mediu interface com o Chromium do Playwright, não por
inspeção de HTML. O veredicto integral está em
[`05-veredictos/fase-3.md`](../05-veredictos/fase-3.md).

- [x] `[comportamental]` RF-21 — os 27 dias estão dentro da janela, em ordem
      crescente, sem repetição, e **todo** `data-total` é igual à soma dos
      `data-centavos` dos seus filhos. **Evidência:** `dias com total != soma
      dos filhos: 0` e `dias sem filho [data-serie]: 0`.
- [x] `[comportamental]` RF-22 — a consulta das séries paradas devolveu **35**
      chaves; a tela imprime `35 sem cobrança recente` e **nenhuma** dessas
      chaves aparece entre os 42 `data-serie` do bloco.
- [x] `[comando]` RF-23 — `pytest -q tests/test_commitments_calendar.py` →
      `11 passed`, exit 0. O validador **reproduziu o cenário fora da suíte do
      avaliado**, montando o próprio banco: quatro cobranças, a de setembro
      valendo −9000, e o dia `2026-09-10` com uma entrada só, `amount_cents =
      -9000`, `predicted = False`.
- [x] `[comportamental]` RF-34 — a frase que declara a previsão está dentro do
      bloco `id="calendario"`, não em rodapé de página.
- [x] `[comportamental]` RF-30 — `200`, os três blocos presentes,
      `−R$ 12.802,64` como total comprometido e `R$ 0,00` como economia
      projetada.
- [x] `[estrutural]` RF-39 — as três capturas existem, com 73.135, 107.194 e
      108.894 bytes. O validador as abriu: são o bloco do calendário, claro e
      escuro.
- [x] `[comando]` portão local — `pytest -q` na raiz → `308 passed`, exit 0.
      `gates_runner.sh` → `✓ gates: limpos (árvore completa, 213 arquivos)`.
- [x] `[comando]` RF-37 — nenhum número congelado literal no código do item.
      Zero linhas em stdout; as quatro de stderr são `.pyc` não rastreados (ver
      seção 7).
- [x] `[comportamental]` RF-21, RF-24 — ida e volta completa em banco novo: a
      primeira leitura traz `−R$ 12.802,64` / `R$ 0,00`, as três dispensas
      respondem `200`, a segunda traz `−R$ 11.703,01` / `R$ 1.099,63`, e o
      calendário cai de 27 para 24 dias — **sem reingestão e sem reinício de
      processo**, provado por `Started server process` aparecendo uma vez só.
- [x] `[comportamental]` RF-39, RF-41 — sem rolagem horizontal do corpo em 375,
      768 e 1440, nas duas formas (carregando já na largura e redimensionando
      com a página aberta), e nenhum dos 312 elementos do calendário tem duração
      de animação ou transição sob `prefers-reduced-motion: reduce`.

---

## 3. Como testar à mão

1. `rm -f /tmp/dash-cal.sqlite`
2. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-cal.sqlite .venv/bin/python -m app.ingest`
3. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-cal.sqlite LOGIN=teste PASSORD=senha-teste-9k2 .venv/bin/python -m app.auth.seed`
4. Suba com as mesmas variáveis mais `SESSION_SECRET=segredo-de-teste-7h4`, entre com `teste` / `senha-teste-9k2` e abra `http://127.0.0.1:8000/comprometido?data=2026-09-05`.
5. Role até **Calendário de vencimentos**.
6. **Esperado:** a escala graduada como eixo do tempo, "Os próximos 45 dias, de
   05/09/2026 a 20/10/2026", a frase que declara a previsão e a contagem das 35
   séries sem cobrança recente.
7. Procure `08/09/2026`.
8. **Esperado:** `JIM.COM* 53489221 06/06`, `já lançado na conta`, −R$ 136,43 —
   e **nada** no dia 06/09 para essa mesma série.
9. Some à mão os valores de um dia qualquer.
10. **Esperado:** igual, ao centavo, ao total impresso ao lado da data.
11. Estreite a janela até 375 px.
12. **Esperado:** os dias empilham em coluna única, sem rolagem horizontal.

---

## 4. Divergências

Nenhuma divergência foi aberta. Duas foram **declaradas pelo implementador e
julgadas pelo validador**, ambas aceitas:

- **`app/commitments/calendar.py` estava fora da lista de escopo que o
  implementador recebeu.** O critério RF-23 manda chamar
  `app.commitments.calendar.calendar(conn, today=...)`: critério que manda
  chamar a função obriga o arquivo a existir. O erro foi meu, ao recortar o
  escopo, não dele. O validador conferiu que não houve carona: o intervalo não
  tocou nada além de `app/`, `tests/`, as capturas e `product/state.json`.

- **A previsão é substituída pelo lançamento do mesmo mês, não do mesmo dia.**
  A leitura literal do critério — mesmo dia — mostraria `jim com` duas vezes em
  setembro: a previsão de −R$ 136,44 no dia 6, pela mediana, e o lançamento real
  de −R$ 136,43 no dia 8. O critério, como escrito, descreve um caso em que a
  ocorrência cai exatamente no dia previsto, e nele as duas leituras coincidem —
  por isso está satisfeito. O afrouxamento tem custo latente e ele virou item de
  roadmap; ver a seção 7.

---

## 5. Raio de impacto

> **Conjunto de candidatos, não verdade.** A precisão medida do raio de impacto
> é **0,578**. Os confirmados abaixo foram lidos; os candidatos, não.

**Confirmados** (lidos, a dependência existe):

- `app/commitments/calendar.py` — `WINDOW_DAYS = 45` e `calendar(conn, *,
  today)`. É **daqui** que sai a janela de 45 dias, e é este contrato que o item
  `004-resumo-e-projecao` consome para projetar saldo dia a dia. Mudar a janela
  aqui muda a projeção lá.
- `app/routers/commitments.py:10` — importa `calendar` e o injeta no contexto de
  `/comprometido`. É o único chamador em produção.
- `app/templates/fragments/comprometido_calendario.html` — os atributos
  `data-dia`, `data-total`, `data-serie` e `data-centavos` não são enfeite: soma
  exibida só é verificável se as parcelas estiverem legíveis ao lado. Todo
  critério comportamental desta fase lê por eles.
- `app/static/css/app.css` — as classes do calendário, com a lista empilhando em
  coluna única abaixo de 768 px. Nenhum valor de cor ou espaço nasce fora de
  `tokens.css`.
- `app/commitments/live.py` e `app/commitments/engine.py` — o calendário não
  decide o que está vivo; ele lê a janela de vida que a fase 1 fixou. Os dois
  defeitos da seção 7 nascem aí, não no calendário.

**Candidatos** (não conferidos):

- `tests/test_comprometido_screen.py` — a fase 2 já o havia alargado para ler
  **todos** os `<tbody>` de uma seção; o calendário não usa tabela e não
  depende disso.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

O validador registrou três apontamentos. Nenhum reprova; dois viraram item de
fila e um virou proposta ao harness.

- **`011-serie-duplicada-e-tolerancia-do-vencimento`**, inserido **antes do
  `004`** porque a projeção de 45 dias soma exatamente estes compromissos
  datados. Ele carrega os dois defeitos medidos:
  1. *Série recorrente e parcelada ao mesmo tempo sobrevive ao fim das
     parcelas.* `jim com` fechou na parcela 06/06 em 08/09/2026 e não deve mais
     nada, mas o motor mantém **também** uma linha `recurring` com a média das
     mesmas cinco cobranças, e `_live_series` a considera viva — o calendário
     prevê −R$ 136,44 em 06/10/2026 para uma dívida que acabou. A causa é do
     motor de séries, anterior a esta fase, e o número congelado `−R$ 12.802,64`
     já a inclui. **Esta é a primeira tela em que esse dinheiro aparece com data
     futura**, e é aí que ele é contado de novo.
  2. *A previsão é apagada pelo mês inteiro, não pelo vencimento.* Uma cobrança
     avulsa no dia 5 esconderia o vencimento do dia 25 da mesma série. Medido
     hoje: um único lançamento casou na janela, a dois dias do dia previsto —
     dano zero. A correção é tolerância em dias, não a volta à comparação
     exata, que reabriria o problema do `jim com`.
- **`.harness/proposals/2026-09-06-005.md`** — `criteria-lint` deveria recusar
  critério `comando` com `grep -R` sem `--exclude-dir`. É a terceira armadilha
  de shell desta corrida a só aparecer na hora da medição, e a régua escrita não
  pegou nenhuma das três.
- **Ainda não há portão de lint para Python.** Quarto validador seguido a
  registrar a ausência; segue como `010-lint-e-formatador-python`, na dívida
  técnica, e não como dependência de item de produto nenhum.
