# Veredicto — 002-gastos-tres-eixos, fase 3

VEREDICTO: APROVADO

> Terceira rodada, por um validador novo, depois das duas correções que o dono
> autorizou ao decidir a escalada: o `RF-33` reescrito e o canvas que segurava a
> largura do container. Os julgamentos anteriores estão em
> `fase-3-reprovada-1.md` e `fase-3-reprovada-2.md`.

Portões
  lint/analyze: não executado — o despacho declara a DoD global como do CI e fora
                deste julgamento. Não presumo que passaria.
  testes:       não executado, pelo mesmo motivo. A suíte é do avaliado e não foi
                usada como prova.
  gates:        OK — `✓ gates: limpos (árvore completa, 160 arquivo(s) considerados).`

Critérios de aceite

  [x] `comportamental` RF-31 — `/gastos` responde 200 com os cinco `<option>` na
      ordem, `value="2026-03-01"` e `value="2026-08-31"` nos campos de data,
      `−R$ 103.772,33` uma única vez e `732 lançamentos de`. Data do sistema
      confirmada pelo cabeçalho `date: Sun, 06 Sep 2026`.

  [x] `comportamental` RF-32 — Chromium real (Chrome for Testing 151.0.7922.34).
      `ANTES {"scrollY":400,"marca":"x","rows":10,"eixo":"grupo"}` → troca de
      eixo → `DEPOIS {"scrollY":400,"marca":"x","rows":52,"eixo":"categoria"}`.
      Os quatro checks verdadeiros. O `#cruzamentos` sobrevive porque o `change`
      do select troca só `#tabela`, sem tocar em `#painel`.

  [x] `comportamental` RF-33 — eixo `beneficiario`, fim de `2026-08-31` para
      `2026-07-31`: eixo continua `beneficiario`; última linha da evolução passa
      de `2026-08` para `2026-07`; total da agregação `−R$ 103.772,33` →
      `−R$ 84.555,22`; `fixa × essencial` `−R$ 41.879,60` → `−R$ 34.797,18`;
      soma das candidatas `−R$ 29.279,70` → `−R$ 23.928,48`. Os cinco checks
      verdadeiros.

  [x] `comportamental` RF-34, RF-35 — `Sem regra`, `R$ 0,00`, `em 0 lançamentos.`
      no bloco de resíduo, dois `<a href="/regras">`, e os dois cruzamentos com
      rótulo e cifra casando `−?R\$ [\d.]+,\d{2}`.

  [x] `comportamental` RF-36 — o clique em `School` abre 20 linhas com as colunas
      `["Data","Descrição","Conta","Valor"]`, todas as células preenchidas, sem
      perder `body.dataset.marca` nem o eixo, e com os cruzamentos idênticos
      antes e depois.

  [x] `comportamental` RF-37 — período de 2020: zero `<tr>` e nenhuma `<table>`
      em `#tabela`, com `Nenhum gasto neste período.` e o caminho de volta aos
      seis meses fechados.

  [x] `comportamental` RF-48 — precondição verificada no SQLite:
      `count(*) from category_rules where essentiality='supérfluo'` → `0`
      (`essencial` 20, `importante` 60). O bloco traz `Quem marca é você, na tela
      de Regras.` e as cinco candidatas, na ordem, com as cifras exigidas.

  [x] `comportamental` RF-38 — com `javaScriptEnabled: false`, a tabela `#serie`
      tem 13 linhas, de `2025-08 −R$ 2.826,05 12` a `2026-08 −R$ 19.217,11 113`.
      Ela vem do servidor, não do gráfico.

  [x] `comando` RF-44 — o grep do critério não imprime nenhuma linha. Controle
      contra falso positivo: os mesmos flags buscando `cifra` devolvem 11 linhas
      sobre 9 arquivos em escopo.

  [x] `comportamental` RF-44 — 88 elementos `.cifra`; zero sem `tabular-nums`,
      zero fora de `^−?R\$ [\d.]+,\d{2}$`, zero com hífen no lugar do sinal.
      Codepoint medido: `U+2212`.

  [x] `comportamental` RF-45 — o critério diz "a janela é ajustada", e o
      validador mediu **redimensionando** e também **carregando** na largura. Os
      dois modos passam nas três: 375 `{375,375,true}`, 768 `{768,768,true}`,
      1440 `{1440,1440,true}`. Em 375 o elemento mais largo é a tabela, com
      427 px, contida pelo `.table-scroll`, que rola por dentro.

  [x] `estrutural` RF-45 — as seis capturas existem, todas acima de 1024 bytes.

  [x] `comportamental` RF-46 — `Tab` real: seletor de eixo, campo de data e
      primeiro controle de linha, todos com `outline=solid 2px offset=2px`.

  [x] `comportamental` RF-47 — sob `reducedMotion: reduce`, zero dos 702
      elementos tem duração de animação ou transição.

Instrumentos do implementer
  nenhum. Os catorze critérios foram medidos por `curl`, leitura direta do
  SQLite, Chromium real, `grep` e `stat`. A suíte do avaliado não foi executada
  nem consultada como prova.

Apontamentos

  `app/templates/gastos.html:6-11` — htmx e Chart.js vêm de `cdnjs.cloudflare.com`.
  Três critérios aprovados (RF-32, RF-33, RF-36) só passam porque o htmx
  carregou; a CDN estava alcançável no momento da validação (`http=200`,
  `0.13 s`). Sem rede, a troca de eixo, a aplicação de período e o drill-down
  caem para navegação inteira pelos `href`/`submit` que os templates mantêm —
  **degradam, não quebram** —, mas nenhum critério exercita esse caminho.
  `product/00-linguagem-visual.md` dá como razão da regra de fonte que "a tela
  precisa abrir sem rede"; fazer a interatividade depender de terceiro não
  controlado merece ratificação explícita, não herança silenciosa.

  `product/00-linguagem-visual.md` — o parágrafo "**E cor semântica é exceção,
  não regra.**", que autoriza a coluna de valores a usar `--color-ink`, foi
  acrescentado pelo mesmo commit que implementa a tela que essa regra passa a
  medir. A régua canônica se moveu junto com o objeto medido. A norma 8 do
  projeto põe reconciliação de documento no mesmo PR da mudança, então é
  procedimentalmente admissível; ainda assim um humano deveria ratificar a
  mudança da régua por mérito próprio, e não como efeito colateral da tela.

  `app/templates/gastos.html:34-38` — dentro de `input[type=date]` o Chromium
  expõe paradas internas de `Tab` cujo estilo computado do host é
  `outline=none`. Os três elementos que RF-46 nomeia passam; registro porque a
  linguagem visual cobra algo mais largo — "percorrer a tela inteira só com
  `Tab`" — e essas paradas não mostram onde o foco está.

Nota sobre a cegueira: o despacho veio limpo. Ao listar os arquivos dos commits
apareceram nomes de `01-brief.md` e `03-plan.md`; estão fora do escopo recebido e
não foram abertos. O único documento lido além do código e dos critérios foi
`product/00-linguagem-visual.md`, pela exceção declarada.
