# Veredicto — 001-base-e-login, fase 4

VEREDICTO: APROVADO

Portões
  lint/analyze: NÃO EXECUTÁVEL — `ruff` não está instalado no `.venv`. A DoD global é do CI e foi declarada fora deste julgamento; registro a ausência em vez de presumir que passaria.
  testes:       OK — `rtk proxy .venv/bin/python -m pytest -q` → `108 passed, 2 warnings in 6.07s`, `PYTEST_EXIT=0`
  gates:        OK — `rtk proxy bash scripts/gates/gates_runner.sh` → `✓ gates: limpos (árvore completa, 106 arquivo(s) considerados).`, `GATES_EXIT=0`

Instrumentação de navegador
  O MCP do Playwright **não** estava disponível nesta sessão, e `playwright` não está no `.venv`. Não inventei resultado: subi o Chromium real de `~/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome` em `--headless=new` com `--remote-debugging-port=9333` e falei CDP direto. `GET /json/version` → `"Browser": "Chrome/151.0.7922.34"`. Todos os critérios comportamentais de tela foram medidos nesse navegador, com `Emulation.setDeviceMetricsOverride`, `Emulation.setEmulatedMedia` e `Input.dispatchKeyEvent` reais.

Critérios de aceite

  [x] `estrutural` RF-35 — seções e tokens em `product/00-linguagem-visual.md`
      Seções de nível 2: `['O conceito…', 'Paleta', 'Tipografia', 'Espaçamento', 'Raio', 'Foco', 'Movimento', 'Pares de contraste', 'O que a régua não negocia', 'Escrita de interface']` — as sete exigidas presentes.
      Tokens com valor por seção: Paleta 20 (`--color-bg = #ECEFE9` … `--color-positive = #86C79A`, claro e escuro), Tipografia 8, Espaçamento 8 (`--space-1 = 0.25rem` … `--space-16 = 4rem`), Raio 2, Foco 3, Movimento 2.

  [x] `estrutural` RF-36 — `app/static/css/tokens.css` declara em `:root` toda property do documento, e o bloco escuro redefine as cores
      Comparação automática doc × CSS: `tokens citados no doc: 35 / declarados em :root: 34 / no doc e NÃO em :root: ['---'] (artefato de separador de tabela) / em :root e NÃO no doc: []`.
      `redefinidos no dark`: as dez cores; `cores em :root nao redefinidas no dark: []`. Bloco em `app/static/css/tokens.css:48`.

  [x] `comando` RF-36 — nenhuma cor literal fora de `tokens.css`
      `grep -rnE "#[0-9a-fA-F]{3,8}|rgb\(|hsl\(" app/templates app/static/css "--include=*.html" "--include=*.css" --exclude=tokens.css` → nenhuma linha, `EXIT=1`.
      Sanidade do escopo: `grep -rl` no mesmo escopo lista os quatro arquivos, e o mesmo grep por `color` imprime 29 ocorrências.

  [x] `comportamental` RF-37 — sem rolagem horizontal em 375/768/1440
      Chromium, altura 800: `375 -> scrollWidth=375 innerWidth=375 => true`; `768 -> 768/768 => true`; `1440 -> 1440/1440 => true`.

  [x] `estrutural` RF-37 — cinco capturas com mais de 1024 bytes
      `login-1440.png` 12892 B, `login-375.png` 9341 B, `login-768.png` 11476 B, `login-dark-1440.png` 12910 B, `login-erro-375.png` 12165 B. `file` confirma PNG válido nas dimensões correspondentes; abri `login-erro-375.png` e `login-dark-1440.png` — mostram a tela real, com a mensagem de erro e com o tema escuro.

  [x] `comportamental` RF-38 — mensagem única, sem eco de senha, campo de senha vazio
      Os dois envios (`teste`/`errada` e `nao-existe`/`qualquer`) devolveram `ocorrencias:1`, `textoAlerta:"Login ou senha inválidos."`, `contemSenha:false`, `valorSenha:""`.
      Corroborado no HTML cru (`curl -X POST`, `HTTP=401` nos dois): `grep -c "Login ou senha inválidos." → 1`; `grep -c errada → 0`; `grep -c qualquer → 0`.

  [x] `comportamental` RF-42 — foco visível
      Tab a Tab, com `Input.dispatchKeyEvent` real: `campo-senha {outlineStyle:"solid", outlineWidth:"2px", outlineOffset:"2px"}`; `BUTTON {idem}`. `campo-login` igualmente.

  [x] `comportamental` RF-43 — todos os pares de contraste, nos dois temas
      Script próprio, lendo os 13 pares da seção `## Pares de contraste` e os valores dos dois blocos de `tokens.css`. `:root`: menores razões `--color-field-border/--color-bg = 3.58` e `/--color-surface = 3.92` (borda, min 3.0); todo par de texto ≥ 6.03. `dark`: `3.61` e `4.02` (borda); todo par de texto ≥ 6.74. `FALHAS: nenhuma`.
      Instrumento aferido contra referências WCAG independentes: `#767676` sobre branco = `4.54`, `#595959` sobre branco = `7.0`, preto/branco = `21.0`.

  [x] `estrutural` RF-43 — `app/design/contrast.py` e os dois casos em `tests/test_contrast.py`
      `inspect.signature(contrast_ratio)` → `(hex_a: str, hex_b: str) -> float`. `tests/test_contrast.py:65` e `:69` trazem os dois casos exigidos.

  [x] `comportamental` RF-44 — `prefers-reduced-motion: reduce`
      `{"matchMedia": true, "total": 21, "ruins": []}`. Controle sem emulação: `{"botao":"0.12s","campo":"0.12s"}` — a media query de `tokens.css:68` é o que zera.

  [x] `comportamental` RF-45 — tema escuro em 1440 px
      `{"matches":true,"bodyBg":"rgb(21, 26, 24)","tokenBg":"#151a18"}`; diferente do `:root --color-bg: #ecefe9` = `rgb(236, 239, 233)`, confirmado com a emulação `light`.

Critérios de integração

  [x] `comando` — portão local: `pytest -q` → `108 passed`, exit 0.

  [x] `estrutural` RF-24 — `login.html:8` `<form method="post" action="/login">`, `:14` `name="login"`, `:21` `name="senha"`; `app/routers/auth.py:47-50` lê exatamente esses dois nomes.

  [x] `comportamental` RF-06, RF-24, RF-28 — ida e volta em banco novo
      `app.ingest` → `migrations applied: 2 / ingested transactions=1942 accounts=12`, exit 0. `app.auth.seed` com `PASSORD` → `seeded user: teste`, exit 0.
      `POST /login` → `302`, `location: /`, `set-cookie: dash_session=teste|0.…; HttpOnly; Max-Age=43200; Path=/; SameSite=Lax`. `GET /health` com o cookie → `200 {"status":"ok"}`. `app.query "select count(*) from transactions"` → `1942`.

  [x] `comportamental` RF-41 — `GET /` → `302 /login`; `GET /health` → `401`; `POST /logout` → `302 /login`; `GET /static/css/tokens.css` → `302 /login`. Exatamente a ordem pedida.

  [x] `estrutural` RF-41 — `openapi paths: ['/', '/health', '/login', '/logout']`; `rotas /static: []`; em `app/main.py`, `.mount → False`, `StaticFiles → False`.
      Prova adicional: com cookie válido, `GET /static/css/tokens.css` → `404` — o `302` é o middleware, não uma rota.

  [x] `comportamental` RF-41 — folha dentro do documento
      `curl -s /login`: linha 8 abre `<style>:root {`, linha 9 traz `--color-bg: #ecefe9;`, linha 57 traz `--color-bg: #151a18;` no bloco escuro embutido. As mesmas declarações estão em `app/static/css/tokens.css:2` e `:50`.

Instrumentos do implementer
  Um critério: o `comando` de portão local, cujo enunciado **é** rodar `pytest`.
  RF-43 comportamental usa `app.design.contrast.contrast_ratio` porque o próprio critério a nomeia, mas **não** usa `tests/test_contrast.py`: script independente lê a tabela do documento e os dois blocos do CSS, com a função aferida contra valores WCAG de referência antes de ser aceita. Todos os demais foram medidos por navegador real, HTTP cru, inspeção de arquivo ou introspecção do app.

Apontamentos
  nenhum

Observações de processo
  - O despacho chegou limpo: objetivo, critérios e ponteiro, sem plano, spec ou histórico. O diff toca `01-brief.md`, `03-plan.md` e `04-divergencias/D-001.md`; nenhum deles foi aberto.
  - Ambiente restaurado ao estado recebido: `login_attempts` de `/tmp/dash-fase4.sqlite` limpa antes e depois, Chromium de `:9333` e servidor auxiliar de `:8010` derrubados.
