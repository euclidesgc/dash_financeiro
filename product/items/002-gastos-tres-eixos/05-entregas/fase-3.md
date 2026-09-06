## 1. O que foi implementado

**Item:** `002-gastos-tres-eixos` · **Fase:** `3 — Tela de Gastos`

> **Esta fase não foi integrada em `develop`.** Ela reprovou em dois validadores
> cegos seguidos e a corrida parou por escalada, como manda a regra. O trabalho
> está commitado na branch `002-gastos-tres-eixos/fase-3-tela-gastos`, nos
> commits `87589fa` e `8a5c269`, e o diagnóstico está em
> [`decisoes-autonomas.md`](../decisoes-autonomas.md), seção "Escalada".

A tela existe e funciona: rota `/gastos` com seletor de eixo e de período,
tabela agregada nos cinco eixos, evolução de treze meses com gráfico e tabela,
drill-down até a transação, os dois cruzamentos e o balde de resíduo. O período
padrão são os seis meses fechados mais recentes, e a tela abre mostrando
`−R$ 103.772,33` em 732 lançamentos — o mesmo número do relatório de origem.

O bloco que mais importa é o da lista de corte. Ela nasce **vazia**, porque
nenhuma regra semeada marca `supérfluo` — a classificação inicial não decide o
que a família do dono pode cortar. Em vez de um painel em branco, o bloco diz
isso, aponta a tela de Regras e lista as cinco maiores categorias de
`variável × importante` como candidatas, somando `−R$ 29.279,70`.

**Capturas** em `06-capturas/`: `gastos-categoria-375.png`,
`gastos-categoria-768.png`, `gastos-categoria-1440.png`,
`gastos-detalhe-1440.png`, `gastos-vazio-375.png`, `gastos-dark-1440.png`.

---

## 2. Critérios atendidos

Doze dos catorze foram cumpridos na segunda rodada, todos medidos em Chromium
real. Os veredictos integrais estão em
[`fase-3-reprovada-1.md`](../05-veredictos/fase-3-reprovada-1.md) e
[`fase-3-reprovada-2.md`](../05-veredictos/fase-3-reprovada-2.md).

- [x] `[comportamental]` RF-31 — os cinco eixos no seletor, o período padrão e o
      total `−R$ 103.772,33` em 732 lançamentos.
- [x] `[comportamental]` RF-32 — trocar o eixo mantém a rolagem onde estava.
      **Evidência:** `scrollY = 400` antes e depois, com 52 linhas. Corrigido
      entre as rodadas: antes a página saltava 2433 px.
- [ ] `[comportamental]` RF-33 — três das quatro cláusulas cumpridas. A quarta é
      insatisfazível sob o fixture que o próprio `RF-48` exige. **É o critério
      que precisa mudar, não o código** — ver a seção 7.
- [x] `[comportamental]` RF-34, RF-35 — o balde de resíduo e os dois cruzamentos,
      com rótulo e cifra no formato exigido.
- [x] `[comportamental]` RF-36 — o drill-down abre as 20 transações de `School`,
      com data, descrição, conta e valor, sem perder o estado da página.
- [x] `[comportamental]` RF-37 — período sem gasto mostra estado vazio acionável,
      com o caminho de volta aos seis meses fechados.
- [x] `[comportamental]` RF-48 — a lista de corte vazia declara a premissa e
      oferece as cinco candidatas com as cifras exatas.
- [x] `[comportamental]` RF-38 — com JavaScript desligado, os 13 pontos da série
      continuam legíveis como tabela e o gráfico fica escondido.
- [x] `[comando]` e `[comportamental]` RF-44 — nenhuma cor fora de `tokens.css`;
      88 cifras, todas com algarismo tabular, todas no formato `−R$ 0.000,00`
      com o sinal U+2212.
- [ ] `[comportamental]` RF-45 — rolagem horizontal em 375 e 768 px **quando a
      janela é redimensionada**. Carregar a página já estreita passa. **É defeito
      real** — ver a seção 7.
- [x] `[estrutural]` RF-45 — as seis capturas existem, todas PNG acima de 1024
      bytes.
- [x] `[comportamental]` RF-46 — foco visível de 2 px em cada parada do `Tab`.
- [x] `[comportamental]` RF-47 — sob `prefers-reduced-motion`, nenhum dos 702
      elementos tem duração de animação ou transição.

**Portões:** `pytest -q` → `222 passed`; `gates_runner.sh` → `✓ gates: limpos`.

---

## 3. Como testar à mão

1. `rm -f /tmp/dash-g.sqlite && rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-g.sqlite .venv/bin/python -m app.ingest`
2. `rtk proxy env DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-g.sqlite LOGIN=teste PASSORD=senha-teste-9k2 .venv/bin/python -m app.auth.seed`
3. Suba o app com as mesmas variáveis mais `DASH_KEY_PATH=/tmp/dash-g.key`, faça
   login e abra `http://127.0.0.1:8000/gastos`.
4. **Esperado:** o total `−R$ 103.772,33`, dez grupos, a evolução de treze meses
   e a lista de corte explicando por que está vazia.
5. Troque o eixo para `categoria`.
6. **Esperado:** 52 linhas, `Escola` no topo com `−R$ 12.992,18`, e a página
   **não** salta.
7. Clique em `Escola`.
8. **Esperado:** as 20 transações que somam a linha.

---

## 4. Divergências

nenhuma

---

## 5. Raio de impacto

> **Conjunto de candidatos, não verdade.** Precisão medida: **0,578**.

**Confirmados** (lidos):

- `app/routers/spending.py` — a rota `/gastos` e os três fragmentos (`tabela`,
  `painel`, `detalhe`). O padrão de fragmento que a tela do item `004` vai
  reusar nasce aqui.
- `app/templates/gastos.html` e `app/templates/fragments/**` — inclusive
  `celula.html`, que resolve rótulo pt-BR e chave crua num lugar só.
- `app/static/css/app.css` — ganhou as classes de tabela de dados, cifra,
  cruzamento e estado vazio, e o `overflow-anchor: none` que impede o salto de
  rolagem em qualquer swap futuro.
- `app/taxonomy/seed.json` — ganhou `category_labels`, o rótulo pt-BR das 77
  categorias. A chave continua sendo o nome cru da Pluggy.
- `app/routers/render.py` — os filtros `brl` e `dia`, que toda tela seguinte usa.

**Candidatos** (não conferidos):

- `app/templates/home.html` — ganhou o link para `/gastos`; o item `004` a
  substitui inteira.

---

## 6. Validações de campo pendentes

nenhuma

---

## 7. Pendências que viraram roadmap

As duas são o motivo da escalada, e nenhuma virou item de roadmap: as duas são
trabalho desta mesma fase, e quem decide segui-las é o dono.

- **`RF-45` — o canvas do gráfico segura a largura do container.** Causa raiz
  isolada pelo validador e confirmada por injeção de estilo no navegador:
  `.chart` só declara `height`, e `.panels`/`.panel` são itens de grid com
  `min-width: auto`, então a largura intrínseca do canvas vira piso e o
  container nunca encolhe. `.panels, .panel, .chart { min-width: 0 }` mais
  `.chart-canvas { max-width: 100% }` fecha em `375 vs 375 | canvas=325`.
  Correção de três linhas de CSS, mais o teste que a trava.
- **`RF-33` — a cláusula dos cruzamentos é insatisfazível.** Ela exige que os
  totais dos **dois** cruzamentos mudem ao trocar o período, e `RF-48` exige um
  banco em que um deles é `R$ 0,00` em todo período. Reescrever para exigir
  mudança no total do cruzamento **atribuído** e na soma das candidatas do
  cruzamento vazio — que é o que de fato muda, e foi medido mudando de
  `−R$ 29.279,70` para `−R$ 23.928,48`.
