VEREDICTO: APROVADO

Portões
  ruff:   OK — `bash scripts/lint.sh` → "All checks passed!" / "136 files already formatted", exit 0
  format: OK — mesmo comando; `ruff format --check app financas ingestao tests` → "136 files already formatted"
  mypy:   N/A DECLARADO — `ls .venv/bin | grep mypy` não retorna nada e `grep mypy pyproject.toml` não
          retorna nada: mypy não está instalado nem configurado neste repositório. A norma 35 do
          CLAUDE.md declara `mypy --strict` fora do portão desta stack (item de roadmap), e o
          despacho nomeou três portões — lint.sh, suíte inteira, gates_runner.sh. Registro a
          ausência em vez de fingir medida; não é portão que falhei em medir, é portão que não existe.
  pytest: OK — `env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q` → "517 passed, 2 warnings
          in 42.71s", exit 0. Coleta não-vazia (517 > 0), logo não é o falso verde do código 5.
  gates:  OK — `bash scripts/gates/gates_runner.sh` → "✓ gates: limpos (árvore completa, 468
          arquivo(s) considerados).", exit 0

Critérios de aceite
  [x] 1 — `GET /` sem query e `GET /?data=banana`, mesma execução, medição própria (harness em
      scratchpad, DASH_TODAY=2026-09-05 no `os.environ` do processo, base carregada, `POST /login -> 302`):
        GET /               status_code=200  len(html)=29856  'id="recusa"' → False
                            seção projecao (5351 chars) contém '05/09/2026' → True
                            trecho cru: `<p class="figure cifra">−R$ 1.000,00</p> <p class="lede">05/09/2026</p>`
        GET /?data=banana   status_code=200  len(html)=29976  'id="recusa"' → True
                            `<p class="notice" id="recusa" role="alert">data inválida: data (banana)
                             A tela responde pela data de hoje.</p>`
      Controle positivo satisfeito: a ausência de `id="recusa"` em `GET /` não é página em branco
      nem erro mudo — 200, 29856 chars, seção projecao presente e datada; e a frase
      'A tela responde pela data de hoje.' aparece só no segundo pedido (False em `/`, True em `/?data=banana`).
  [x] 2 — GET /?data= → status_code=200, len(html)=29856, 'id="recusa"' → False, seção projecao
      contém '05/09/2026' → True. Idêntica em tamanho à resposta sem query: parâmetro vazio é ausência.
  [x] 3 — GET /?data=2100-12-31 → status_code=200, 'id="recusa"' → False, seção projecao contém
      '31/12/2100' → True. Trecho cru: `<p class="lede">31/12/2100</p>` e
      `<h3 class="calendar-date">31/12/2100</h3>`. O limite superior da faixa não é recusado.
  [x] 4 — GET /?data=0001-01-01 → status_code=200 (não 500), len(html)=29980, 'id="recusa"' → True,
      seção projecao contém '05/09/2026' → True. Trecho cru:
      `<p class="notice" id="recusa" role="alert">data inválida: data (0001-01-01) A tela responde pela data de hoje.</p>`
  [x] 5 — GET /comprometido?data=0001-01-01 → status_code=200 (não 500), len(html)=33354,
      'id="recusa"' → True, seção calendario (3659 chars) contém '>05/09/2026<' → True.
  [x] 6 — mesma execução:
        GET /comprometido               status=200 len=33265 'id="recusa"' → False
                                        calendario: '>05/09/2026<' True, '>20/10/2026<' True
        GET /comprometido?data=banana   status=200 len=33350 'id="recusa"' → True
                                        calendario: '>05/09/2026<' True, '>20/10/2026<' True
      Trecho cru: `Os próximos 45 dias, de <span class="calendar-date">05/09/2026</span> a
      <span class="calendar-date">20/10/2026</span>`. Controle positivo satisfeito na mesma execução.
  [x] 7 — HOJE calculado na hora dentro do próprio harness: `date.today().isoformat()` = 2026-09-07,
      com DASH_TODAY=2026-09-05 no processo (impresso pelo harness: "HOJE ... = 2026-09-07",
      "DASH_TODAY do processo = 2026-09-05").
        GET /                    status=200  'A posição é sempre a atual' presente: False
        GET /?data=2026-09-07    status=200  'A posição é sempre a atual' presente: True
      Trecho cru do segundo: `A posição é sempre a atual — o histórico dos saldos não é guardado —`.
      A discriminação vale: o relógio (2026-09-07) difere de DASH_TODAY (2026-09-05), então a
      frase só aparece porque a data foi pedida por nome, não porque coincide com `date.today()`.
  [x] 8 — verificado por AST, não por leitura:
        app/routers/summary.py:     importa de app.routers.reference → ['Reference', 'screen_date'];
                                    chamadas date.today() → []; defs _reference → []
        app/routers/commitments.py: importa de app.routers.reference → ['screen_date'];
                                    chamadas date.today() → []; defs _reference → []
      Linhas: summary.py:14 `from app.routers.reference import Reference, screen_date`;
      commitments.py:15 `from app.routers.reference import screen_date`.
      Varredura ampla de `today` nos dois arquivos: toda ocorrência é parâmetro ou keyword
      (`today=reference.date`, `def _context(..., today: date)`), nenhuma é `date.today()`.
  [x] 9 — `env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_resumo_screen.py
      tests/test_comprometido_screen.py` → "37 passed, 2 warnings in 7.26s", EXIT=0 (coleta
      não-vazia). Chamadas sem o parâmetro `data`, com DASH_TODAY no ambiente:
        tests/test_resumo_screen.py:38  `monkeypatch.setenv("DASH_TODAY", ASKED)` (ASKED="2026-09-05")
        tests/test_resumo_screen.py:228 `unasked = client.get("/")`
        tests/test_resumo_screen.py:262 `unasked = client.get("/")`
        tests/test_comprometido_screen.py:107 `monkeypatch.setenv("DASH_TODAY", ASKED)`
        tests/test_comprometido_screen.py:316 `unasked = client.get(SCREEN)`

Instrumentos do implementer
  Somente o critério 9, que é por construção um comando sobre a suíte do avaliado. Os critérios 1 a 7
  foram medidos por harness independente que o validador escreveu, com base própria, sessão própria e
  requisições próprias — nenhum deles depende de asserção escrita pelo implementador. O critério 8 foi
  medido por AST sobre os arquivos-fonte, sem passar por teste.

Duas observações fora do que foi pedido, separadas do veredicto:

1. **`mypy --strict` não existe neste ambiente.** Não é falha desta fase — é o item de roadmap
   declarado na norma 35 do `CLAUDE.md`. Registro porque a ordem padrão de portões da minha função o
   inclui, e um portão declarado-ausente precisa aparecer no relatório em vez de sumir.

2. **O despacho não veio com plano, spec, brief nem histórico**, e não abri
   `product/items/016-data-de-referencia-no-caminho-de-recusa/`. A cegueira foi mantida: o veredicto
   acima mede critério cumprido, não intenção seguida.

3. **Achado não pedido, que não reprova:** em `app/routers/commitments.py:62`, dentro do caminho de
   `POST` (dispensar/retomar série), o resultado de `screen_date(asked)` é consumido só pelo campo
   `.date` — o `.notice` da recusa é descartado ali. Ou seja: um `POST /comprometido/dispensar` com
   `data=banana` recai na data de referência corretamente, mas **não** mostra o alerta `id="recusa"`
   que a rota `GET` mostra. Nenhum critério desta fase cobre o `POST`, então isto não é reprovação; é
   assimetria entre os dois caminhos do mesmo arquivo, candidata a correção com teste em vez de
   rodada nova.
