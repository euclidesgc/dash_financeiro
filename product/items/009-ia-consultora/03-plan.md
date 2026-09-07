# Plano — 009-ia-consultora

**Trilha:** rápida · **Brief:** `01-brief.md` · Uma fase.

## Fase 1 — O consultor que pergunta e não calcula

**Critérios de aceite:**

O banco é preparado por `rm -f /tmp/dash-009.sqlite && rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-009.sqlite DASH_TODAY=2026-09-05
.venv/bin/python -m app.ingest && rtk proxy env DASH_ENV_FILE=/dev/null
DASH_DB_PATH=/tmp/dash-009.sqlite LOGIN=teste PASSORD=senha-teste-9k2
.venv/bin/python -m app.auth.seed`, e o servidor por `rtk proxy env
DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/dash-009.sqlite LOGIN=teste
PASSORD=senha-teste-9k2 SESSION_SECRET=segredo-de-teste-7h4
DASH_KEY_PATH=/tmp/dash-009.key .venv/bin/python -m app`. **Nenhuma variável
`GEMINI_API_KEY` é definida em nenhum dos comandos.**

- [ ] `comportamental` — RF-01, RF-02, RF-10
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -b "dash_session=<cookie>"
      "http://127.0.0.1:8000/consultor?data=2026-09-05"` é executado
      *Então* a resposta é `200`; o bloco `id="pergunta"` traz **exatamente um**
      elemento com `data-pergunta`, e o seu valor é `taxa-cartao`; o texto do
      bloco traz `Qual é` e o nome de uma tela onde informar; e o bloco
      `id="numeros"` traz cinco elementos com `data-numero`
- [ ] `comportamental` — RF-05
      *Dado* o servidor rodando e um cookie válido
      *Quando* `rtk proxy curl -s -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/consultor/adiar --data-urlencode "nome=taxa-cartao"
      --data-urlencode "data=2026-09-05"` é executado
      *Então* a resposta é `200` e o `data-pergunta` do bloco `id="pergunta"`
      **deixa de ser** `taxa-cartao`
- [ ] `comportamental` — RF-12, RF-13
      *Dado* o servidor rodando **sem** `GEMINI_API_KEY` e um cookie válido
      *Quando* `rtk proxy curl -s -X POST -b "dash_session=<cookie>"
      http://127.0.0.1:8000/consultor --data-urlencode "pergunta=Por que o pior
      ponto é em outubro?" --data-urlencode "data=2026-09-05"` é executado
      *Então* a resposta é `200`, **não** `500`; traz o bloco
      `id="indisponivel"` com as strings `GEMINI_API_KEY` e `não dependem dela`;
      e o bloco `id="numeros"` continua trazendo os cinco `data-numero`
- [ ] `comportamental` — RF-14
      *Dado* o servidor rodando e um cookie válido
      *Quando* `POST /consultor` é feito com `pergunta=` vazia e depois com uma
      pergunta de 600 caracteres
      *Então* as duas respostas são `400` e trazem o bloco `id="recusa"`
- [ ] `comando` — RF-03 a RF-08, RF-11, RF-13
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_advisor.py` sai com código 0, e o arquivo contém: um teste que
      afirma que fato informado não é perguntado; um que afirma que fato vencido
      volta; um que afirma que a pergunta adiada some; um que afirma que a
      adiada **volta** quando o fato vence; um que afirma que a instrução de
      sistema contém a proibição de calcular; um que afirma que erro de rede
      vira indisponibilidade e não exceção; e um que afirma que o instantâneo
      **não chama o modelo** — substituindo `httpx.post` por algo que falha se
      for chamado
- [ ] `comando` — RF-08, RF-09
      `rtk proxy grep -c "NUNCA CALCULA" app/advisor/gemini.py` imprime `1`, e
      `rtk proxy grep -REn --exclude-dir=__pycache__ "httpx" app/advisor` imprime
      linhas **apenas** de `app/advisor/gemini.py`
- [ ] `comportamental` — RF-15
      *Dado* o Chromium com `prefers-reduced-motion: reduce` emulado, sessão
      válida e `http://127.0.0.1:8000/consultor?data=2026-09-05` carregada
      *Quando* a janela é ajustada para 375, 768 e 1440 px, altura 800, uma vez
      carregando já naquela largura e uma vez redimensionando
      *Então* nas seis medições `document.documentElement.scrollWidth <=
      window.innerWidth` avalia como `true`, e todo elemento de
      `document.querySelectorAll("#pergunta *")` tem `animationDuration` e
      `transitionDuration` iguais a `0s`
- [ ] `estrutural` — RF-15
      Existem `product/items/009-ia-consultora/06-capturas/consultor-375.png`,
      `consultor-1440.png` e `consultor-dark-1440.png`, todos no **mesmo**
      diretório e cada um com mais de 1024 bytes

**Critérios de integração:**

- [ ] `comando` — portão local
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` na
      raiz sai com código 0
- [ ] `comando` — portão de lint
      `rtk proxy bash scripts/lint.sh` sai com código 0
- [ ] `comando` — RF-15
      `rtk proxy grep -REn "#[0-9a-fA-F]{3,8}\b|rgb\(|hsl\(" app/templates
      app/static/css/app.css` não imprime nenhuma linha
- [ ] `comportamental` — RF-01 guarda
      *Dado* nenhuma sessão
      *Quando* `rtk proxy curl -s -o /dev/null -w "%{http_code}"
      http://127.0.0.1:8000/consultor` é executado
      *Então* a resposta é `302`

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] 1.1 Migração `009_advisor.sql` com `advisor_questions`.
- [ ] 1.2 `app/advisor/gaps.py`: a fila declarada e o adiamento.
- [ ] 1.3 `app/advisor/context.py`: o instantâneo determinístico.
- [ ] 1.4 `app/advisor/gemini.py`: a instrução de sistema e a degradação.
- [ ] 1.5 `app/routers/advisor.py` e `app/templates/consultor.html`.
- [ ] 1.6 `tests/test_advisor.py`.
- [ ] 1.7 As três capturas.

## Validações de campo pendentes

- A qualidade da resposta do Gemini só se julga lendo, e exige chave válida. Já
  registrada no roadmap desde antes deste item.
