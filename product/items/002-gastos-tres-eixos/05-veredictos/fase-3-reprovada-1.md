# Veredicto — 002-gastos-tres-eixos, fase 3 (primeira rodada)

VEREDICTO: REPROVADO

Instrumentação: sem MCP de navegador, o validador subiu um Chromium real
(`~/.cache/ms-playwright/chromium-1234`) por Playwright e mediu tudo nele.

Portões
  testes: OK — `219 passed, 2 warnings in 9.83s`
  gates:  OK — `✓ gates: limpos (árvore completa, 154 arquivo(s) considerados).`
  lint:   N/A — o projeto não declara linter nem typechecker.

Critérios cumpridos: RF-31, RF-33, RF-34/RF-35, RF-36, RF-37, RF-48, RF-38,
RF-44 (comando e comportamental), RF-45 (comportamental), RF-46 e RF-47 — doze
ao todo, medidos em navegador real, `curl` e leitura de arquivo.

Critérios não cumpridos:

  [ ] `comportamental` RF-32 — trocar o eixo faz a página saltar.
      Chromium 1440x800, `window.scrollTo(0, 400)`, troca de `grupo` (10 linhas)
      para `categoria` (52 linhas). Medido em duas execuções independentes:
        scrollY antes: 400 | scrollHeight antes: 2819
        depois:        scrollY=2833 | scrollHeight=5252 | linhas=52
      As 52 linhas, a marca do painel e o campo de fim sobrevivem; o que quebra
      é a rolagem. O delta de 2433 px é exatamente o crescimento do documento: o
      swap insere 42 linhas acima da âncora e o Chromium re-ancora, porque
      `overflowAnchor` está em `auto` e nada no projeto o desliga.

  [ ] `estrutural` RF-45 — três das seis capturas não existem com o nome exigido.
      Ausentes: `gastos-categoria-375.png`, `gastos-categoria-768.png`,
      `gastos-categoria-1440.png`. O diretório trazia `gastos-375.png`,
      `gastos-768.png` e `gastos-1440.png` — nome diferente do pedido, e o nome
      diz de qual eixo é a captura.

Apontamentos
  RF-33 versus RF-34/RF-35 e RF-48 — conflito de redação, para quem escreveu o
  bloco. RF-33 exige que "os totais exibidos nos dois cruzamentos mudam de
  valor"; RF-34/RF-35 exige `R$ 0,00` no cruzamento `variável × supérfluo`, e
  RF-48 exige que ele esteja vazio por não haver regra `supérfluo`. Zero não
  muda de valor em período nenhum.

  `GET /regras` responde 404: os dois blocos que oferecem o próximo ato apontam
  para lá, e a tela é da fase seguinte. Apontamento de ordem, não defeito.

  Sem rede, o `<select>` de eixo fica mudo — só tem `hx-get`, enquanto o botão
  de período funciona pelo form GET.
