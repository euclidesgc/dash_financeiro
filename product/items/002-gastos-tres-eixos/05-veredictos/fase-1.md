# Veredicto — 002-gastos-tres-eixos, fase 1

VEREDICTO: APROVADO

> Segunda rodada, por um validador novo, depois de `app/queries/crossings.py`
> existir. O julgamento da primeira rodada está em `fase-1-reprovada.md`.

Portões
  lint/analyze: NÃO EXECUTÁVEL — o projeto não registra linter/typechecker
                (`pyproject.toml` sem seção ruff/mypy/flake8; `.venv/bin/ruff`
                → "No such file or directory"). Não presumo que passaria.
  testes:       OK — `env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q`
                → `167 passed, 2 warnings in 7.01s`
  gates:        OK — `bash scripts/gates/gates_runner.sh`
                → `✓ gates: limpos (árvore completa, 128 arquivo(s) considerados).`

Critérios de aceite
  [x] RF-01 `comando` — tabelas, colunas e índice — após `python -m app.migrate`
      (`applied 001_schema.sql / 002_session_epoch.sql / 003_taxonomy.sql —
      migrations applied: 3`), a consulta do critério imprimiu `6 5 1`.
  [x] RF-01 `comando` — migrações antigas intocadas — o grep imprimiu exatamente
      `001_schema.sql:0` e `002_session_epoch.sql:0`.
  [x] RF-02, RF-03 `comando` — termos e ordem — com o banco carregado por
      `python -m app.ingest` (`ingested transactions=1942 accounts=12` ·
      `taxonomy seeded: groups=10 natures=3 essentialities=3 crossings=2 rules=80` ·
      `classified 1942: changed=1942 without_rule=7`), a consulta imprimiu
      `grupos=Moradia,Educação,Transporte,Alimentação,Comer fora e lazer,Saúde,Serviços e assinaturas,Dívidas e juros,Transferências,Outros naturezas=fixa,variável,eventual essencialidades=essencial,importante,supérfluo`
      — idêntico, caractere a caractere, ao esperado.
  [x] RF-04, RF-05 `comando` — cobertura de regras — `77 1 0 1 1 0 1`. A única
      categoria sem regra de categoria é `Não classificado`.
  [x] RF-06 `comportamental` — seed idempotente — antes `10 3 3 2 80`; duas
      execuções, ambas exit 0; depois `10 3 3 2 80`.
  [x] RF-07 `comportamental` — termo inválido rejeitado — as três chamadas
      levantaram `grupo inválido: 9999`, `natureza inválida: fixo` e
      `essencialidade inválida: dispensável`; nenhuma regra gravada.
  [x] RF-08 `comando` — nenhum termo do seed em código de `app/` — `0 []`, exit 0.
  [x] RF-09 `comando` — sem nulo de classificação nem beneficiário vazio — `0 0 1942`.
  [x] RF-10 `comando` — beneficiário conferido contra a fonte — `0 0 1942`:
      zero divergências entre `normalize_description`, o `payee` gravado e o
      campo `chave` do JSON de origem, sobre 1942 lançamentos.
  [x] RF-11 `comportamental` — classificação idempotente — assinatura
      `1942 85507 13046 33394` antes e depois de duas execuções; `diff` vazio.
  [x] RF-11 `comportamental` — expressão vence categoria — a regra `ifood`
      reclassificou `26`, e os lançamentos cuja descrição contém `ifood` também
      são `26`.
  [x] RF-12 `comportamental` — resíduo visível — removida a regra de
      `Eating out`, a classificação devolveu `changed=128 without_rule=135`, a
      consulta de fallback imprimiu `128` e `residue(…, '2026-03-01',
      '2026-08-31')` imprimiu `60 -436013`.
  [x] RF-13 `comportamental` — corte reclassifica no mesmo processo —
      `update_rule(conn, 20, essentiality='supérfluo')` devolveu `128`, e a
      chamada seguinte a `crossing(conn, slug='corte', …)` devolveu
      `label = variável × supérfluo | total = -436013 | media = -72669` com a
      linha `{'key': 'Eating out', 'amount_cents': -436013, 'entries': 60}`.
  [x] RF-14 `comando` — atomicidade — `pytest tests/test_rules_atomicity.py` →
      `2 passed`, e o teste foi lido linha a linha: banco temporário,
      substituição efetiva de `classify_all`, escrita parcial antes da exceção e
      comparação de snapshot completo. O caminho de rollback é exercitado de
      verdade.

Instrumentos do implementer
  RF-14 é o único critério cuja evidência é a suíte do avaliado, por construção
  do próprio critério, que nomeia o arquivo. Mitigado pela leitura do teste. Os
  outros treze foram medidos por execução direta contra os 1942 lançamentos
  reais.

Apontamentos
  `app/taxonomy/classify.py:74` (com `app/ingest/normalize.py:14-23` e
  `app/taxonomy/rules.py:127-131`) — regras de expressão são compiladas sem
  `re.IGNORECASE` e casadas contra `payee`, que vem em minúsculas, sem acento e
  **sem dígito**. A validação de `create_rule` só checa que a expressão compila,
  então uma regra gravada como `Uber`, `99app` ou `saúde` é aceita e casa zero
  lançamentos, em silêncio. Nada nesta fase expõe o problema — a tela de edição
  de regras expõe. O sintoma será "a regra que eu criei não fez nada", sem erro
  e sem log.

  `app/queries/crossings.py:13` — a lista de corte agrupa por
  `transactions.category`, a string crua da Pluggy, então as chaves saem em
  inglês (`Eating out`). Não viola critério, mas a interface é pt-BR: a tradução
  precisa existir em algum lugar, e é melhor decidir onde antes de a tela
  consumir isso.
