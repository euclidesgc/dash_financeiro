# Veredicto — 002-gastos-tres-eixos, fase 3 (segunda rodada)

VEREDICTO: REPROVADO

> Segunda rodada, por um validador novo, depois de corrigidos o salto de rolagem
> e os nomes das capturas. O veredicto da primeira rodada está em
> `fase-3-reprovada-1.md`.

Portões
  lint:   NÃO EXECUTÁVEL — o projeto não declara linter nem typechecker.
  testes: OK — `222 passed, 2 warnings in 10.34s`
  gates:  OK — `✓ gates: limpos (árvore completa, 154 arquivo(s) considerados).`

Navegador: Chromium real de `~/.cache/ms-playwright/chromium-1234`, dirigido por
Playwright do cache do npx. Uma única sessão aberta e reusada.

Critérios cumpridos: RF-31, RF-32 (o salto foi corrigido — `scrollY = 400` antes
e depois da troca de eixo, com 52 linhas), RF-34/RF-35, RF-36, RF-37, RF-48,
RF-38, RF-44 (comando e comportamental), RF-45 (estrutural — as seis capturas
existem, todas PNG de verdade acima de 1024 bytes), RF-46 e RF-47.

Critérios não cumpridos:

  [ ] `comportamental` RF-45 — rolagem horizontal em 375 px e 768 px **quando a
      janela é redimensionada**, que é o que o critério manda fazer.
        `redimensionada 375px: scrollWidth=1064 innerWidth=375 ok=false`
        `redimensionada 768px: scrollWidth=1104 innerWidth=768 ok=false`
        `redimensionada 1440px: scrollWidth=1440 innerWidth=1440 ok=true`
      Falha em toda largura inicial maior que o alvo; só passa quando a página é
      carregada já na largura final (`carga fresca 375px: 375<=375 true`).

  [ ] `comportamental` RF-33 — três das quatro cláusulas cumpridas. Trocar o fim
      de `2026-08-31` para `2026-07-31`: o eixo continua `beneficiario`, a última
      linha da evolução passa a `2026-07 −R$ 15.625,74 127`, e o total da
      agregação passa de `−R$ 103.772,33` para `−R$ 84.555,22`. Mas dos dois
      cruzamentos só `fixa × essencial` muda (`−R$ 41.879,60` → `−R$ 34.797,18`);
      `variável × supérfluo` continua `R$ 0,00`. Como RF-48 exige um banco em que
      nenhuma regra carrega `supérfluo` — confirmado: `[('essencial', 20),
      ('importante', 60)]` —, esse total é zero em qualquer período, **por
      construção**. Nenhuma implementação faz os dois totais mudarem sob esse
      fixture. O único número do bloco que muda é a soma das candidatas
      (`−R$ 29.279,70` → `−R$ 23.928,48`).

Apontamentos
  `app/static/css/app.css` (`.chart` / `.chart-canvas`) com
  `app/templates/fragments/gastos_painel.html` — **causa raiz da falha de
  RF-45, isolada e confirmada**: o canvas do gráfico nunca encolhe quando a
  janela estreita. Seis segundos depois de ir de 1440 para 375 px, o canvas
  continua com 1022 px e o corpo herda 1064 px de rolagem. Sem JavaScript — logo
  sem gráfico — o mesmo redimensionamento fecha limpo (`375 vs 375 ok=true`), o
  que isola a causa no gráfico. `.chart` só declara `height`; `.panels` e
  `.panel` são itens de grid com `min-width: auto`, então a largura intrínseca
  do canvas vira piso: o Chart.js só reduz o canvas quando o container reduz, e
  o container não reduz porque o canvas o segura. Confirmado injetando estilo no
  navegador, sem tocar no repositório: `.panels, .panel, .chart { min-width: 0 }`
  e `.chart-canvas { max-width: 100% }` → `375 vs 375 | canvas=325`.

  RF-33, cláusula dos cruzamentos — conflita com o fixture que RF-48 exige.
  Reescrever a cláusula (exigindo mudança no total do cruzamento **atribuído** e
  na soma das candidatas do cruzamento vazio) ou mudar o fixture. Endereçado a
  quem escreveu os critérios, não a quem implementou.

  Fora de critério: htmx e Chart.js vêm de `cdnjs.cloudflare.com`. Nesta máquina
  a rede responde, e por isso RF-32, RF-33 e RF-36 puderam ser medidos; em rede
  fechada a troca de eixo por `hx-trigger` e o gráfico não existem — a tabela
  continua de pé, o que RF-38 já verifica.
