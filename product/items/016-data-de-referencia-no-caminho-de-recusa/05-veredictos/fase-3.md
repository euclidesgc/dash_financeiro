VEREDICTO: APROVADO

O despacho não trouxe plano, spec nem histórico — só objetivo, critérios e ponteiro. Não abri
`product/items/016-.../`. Não escrevi nada no repositório: `git status --porcelain` no fim é idêntico
ao do início (8 modificados, 2 não rastreados).

**Portões**
```
ruff:   OK   — bash scripts/lint.sh → "All checks passed!" / "138 files already formatted" (exit 0)
format: OK   — mesmo comando, `ruff format --check app financas ingestao tests`
mypy:   N/A  — não é portão deste projeto. `.venv/bin/python -m mypy --version` → "No module named
               mypy"; `ls -d src` → "cannot access 'src': No such file or directory". Não existe alvo
               nem ferramenta para medir; o despacho nomeia três portões e este não está entre eles.
pytest: OK   — env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q → "526 passed, 2 warnings
               in 43.56s", exit code real 0 (capturado sem pipe). Nenhum "no tests ran", nenhum 5.
gates:  OK   — bash scripts/gates/gates_runner.sh → "✓ gates: limpos (árvore completa, 469
               arquivo(s) considerados)." exit 0
```

**Critérios de aceite**

Todos os comportamentais foram medidos com harness próprio (scratchpad), base construída do zero pelo
validador: `DASH_ENV_FILE=/dev/null`, `DASH_DB_PATH` em arquivo temporário, `SESSION_SECRET`,
`DASH_TODAY` no ambiente do processo, `TestClient(follow_redirects=False)`, `POST /login` após
`seed_user`. Relógio real da máquina confirmado em execução: `2026-09-07`.

- [x] **1 — `/simulador` e `/consultor` sem query string** — `GET /simulador`: `status = 200`,
  `id="recusa"` presente = `False`, campo `<input type="hidden" name="data" value="2026-09-05">`
  presente = `True`. `GET /consultor`: idêntico (`200`, `False`, `True`).

- [x] **2 — as duas com `?data=banana`** — `GET /simulador?data=banana`: `200`, `id="recusa"` = `True`,
  `data inválida: data (banana)` = `True`, campo oculto = `True`. Trecho cru:
  `<p class="notice" id="recusa" role="alert">data inválida: data (banana)</p>` seguido, no
  formulário, de `<input type="hidden" name="data" value="2026-09-05">`. `GET /consultor?data=banana`:
  mesmo resultado, com o mesmo `<p class="notice" id="recusa" role="alert">data inválida: data
  (banana)</p>`.

- [x] **3 — `/objetivo` e `plan_snapshots` sobre cópia de trabalho** — precondição confirmada de
  verdade: `SELECT reference_date, scenario FROM plan_snapshots` antes → `[]`;
  `DELETE ... WHERE reference_date IN ('2026-08-01','2026-09-05')` → `rowcount = 0`; leitura depois →
  `[]`. Ou seja, nenhuma das duas datas existia no ponto de partida. Respostas: `?data=2026-08-01` →
  `200`, recusa `False`; `?data=0001-01-01` → `200`, recusa `True`; sem query → `200`, recusa `False`.
  Primeira leitura de `SELECT reference_date FROM plan_snapshots WHERE scenario = 'base'` →
  `['2026-08-01']` (contém `2026-08-01`, **não** contém `2026-09-05`). Segunda leitura →
  `['2026-08-01', '2026-09-05']` (contém `2026-09-05`).

- [x] **4 — `vencido` no recorte, não na página** — dois `POST /simulador/fato` (`quitacao-cdc` /
  `1.000,00` / `2026-09-06`, e `transporte-sem-carro` / `500,00` / `2026-09-04`), depois
  `GET /simulador` sem query. Recorte de `data-fato="quitacao-cdc"` até o primeiro `</tr>`
  (203 chars): `data-fato="quitacao-cdc" data-valor="100000"> <td>Saldo de quitação do CDC do
  carro</td> <td class="cifra col-num">R$ 1.000,00</td> <td>06/09/2026</td> </tr>` → `vencido`
  **ausente**. Recorte de `data-fato="transporte-sem-carro"` (258 chars):
  `... <td>04/09/2026 <span class="cell-key">vencido</span></td> </tr>` → `vencido` **presente**.
  Contagem de `vencido` no HTML inteiro = `1`, o que confirma que o recorte discrimina.

- [x] **5 — janela padrão de `/gastos` com `DASH_TODAY=2026-05-15`** — `reference_date()` retornou
  `2026-05-15` enquanto `date.today()` do processo retornou `2026-09-07`. `GET /gastos` (sem `inicio`,
  sem `fim`) → `200`; `de 01/11/2025 a 30/04/2026` presente = `True`; `de 01/03/2026 a 31/08/2026`
  presente = `False`. Varredura de todas as janelas no texto sem tags encontrou exatamente uma:
  `de 01/11/2025 a 30/04/2026`.

- [x] **6 — estrutural nos quatro routers** — em `app/routers/plan.py`, `whatif.py`, `advisor.py`,
  `spending.py`: `grep -n "date\.today()"` → nenhuma linha em nenhum dos quatro; `grep -n "_reference"`
  → nenhuma ocorrência sequer, muito menos definição; `screen_date` importado de
  `app.routers.reference` em `plan.py:13`, `whatif.py:20`, `advisor.py:20`, `spending.py:15`;
  `plan.py` não menciona `EARLIEST` nem `LATEST` (as constantes vivem em `app/routers/reference.py:7-8`);
  a lista completa de imports de `whatif.py` (linhas 1-26) e de `advisor.py` (linhas 1-22) não contém
  nenhum nome vindo de `app.routers.plan` — nem `from .plan`, nem `from app.routers import plan`.

- [x] **7 — `grep -REn --exclude-dir=__pycache__ "date\.today\(\)" app/routers`** — saída vazia,
  exit `1` (nenhuma correspondência).

- [x] **8 — integração das cinco rotas** — cópia de trabalho, precondição conferida: `plan_snapshots`
  antes → `[]`, `DELETE ... WHERE reference_date = '2026-09-05'` → `rowcount = 0`, depois → `[]`.
  Primeira volta, sem query string, na mesma execução:
  ```
  GET /              status=200 recusa=False  id='projecao' contém 05/09/2026 = True
  GET /comprometido  status=200 recusa=False  id='calendario' contém >05/09/2026< = True
  GET /objetivo      status=200 recusa=False  plan_snapshots(base) após a requisição = ['2026-09-05']
  GET /simulador     status=200 recusa=False  campo hidden 2026-09-05 = True
  GET /consultor     status=200 recusa=False  campo hidden 2026-09-05 = True
  ```
  Segunda volta, `?data=banana`: as cinco em `status=200` com `recusa=True`.

- [x] **9 — comando, os dois testes novos, e o dente da varredura** — o comando saiu com código `0`
  (capturado sem pipe: `EXIT_REAL=0`), saída `81 passed, 2 warnings in 14.96s`.
  `tests/test_route_guard.py` define `test_no_router_resolves_the_screen_date_by_itself` (linha 75) e
  `test_the_sweep_accuses_a_source_that_calls_the_clock` (linha 82); o `git diff` do arquivo é **só
  adição** — `test_every_registered_route_requires_session` e `test_the_login_form_is_the_open_door`
  seguem intactos, sem uma linha alterada.

  O dente foi provado por mutação, executando as funções com `_accused` substituída (nada gravado no
  repositório):
  ```
  1) repositório como está:  no_router → PASSOU   |  sweep_accuses → PASSOU
  2) varredura cega (_accused → []):
        no_router → PASSOU  (é exatamente o falso verde que o critério teme)
        sweep_accuses → FALHOU
  3) varredura com marcador errado ("datetime.today()"):
        sweep_accuses → FALHOU
  4) varredura invertida (acusa todos):
        no_router → FALHOU: "resolve a data pelo relógio: __init__.py, advisor.py, auth.py,
        commitments.py, debts.py, health.py, navigation.py, plan.py, reference.py, render.py,
        rules.py, settings.py, spending.py, summary.py, whatif.py"
  5) varredura real apontada para uma pasta com um router culpado:
        no_router → FALHOU: "resolve a data pelo relógio: culpado.py"
  ```
  Os dois sentidos ficam cobertos: a varredura cega é apanhada pelo teste de fonte falsa, e a
  varredura real acusa nomeando o arquivo.

**Instrumentos do implementer**

Critério 9 — por definição, é um comando sobre a suíte do avaliado, e a inspeção do dente também
partiu do código dela. Os critérios 1, 2, 3, 4, 5 e 8 foram medidos por harness independente do
validador, sem tocar em `tests/`; os critérios 6 e 7 foram medidos direto na fonte de `app/routers/`.

---

**Achado que não reprova** (não pedido, separado do que foi):

`tests/test_route_guard.py:76` varre com `ROUTERS_DIR.glob("*.py")`, que não é recursivo, enquanto o
critério 7 usa `grep -R`. Hoje os dois coincidem — `find app/routers -mindepth 1 -type d` devolve só
`__pycache__`, e os 15 `.py` estão todos no nível de cima. No dia em que alguém criar um subpacote sob
`app/routers/`, o `grep` continua enxergando e a varredura fica cega, verde e silenciosa. Trocar por
`rglob("*.py")` fecha a diferença sem custo. Item de roadmap, não reprovação: o critério pede
varredura de `app/routers/`, e ela cobre `app/routers/` como a pasta é hoje.
