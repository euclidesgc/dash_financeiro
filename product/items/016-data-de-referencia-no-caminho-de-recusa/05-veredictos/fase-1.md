VEREDICTO: APROVADO

Portões
```
ruff:   OK — bash scripts/lint.sh → "All checks passed!" (escopo app financas ingestao tests), EXIT=0
format: OK — mesma execução → "136 files already formatted", EXIT=0
mypy:   NÃO SE APLICA a esta stack — não há diretório `src` (`ls -d src` → "No such file or directory")
        e não há binário mypy no venv (`.venv/bin/mypy` inexistente). Norma 35 do projeto declara
        `mypy --strict` como item de roadmap. Não inventei o portão nem o dei por passado.
pytest: OK — env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q → "510 passed, 2 warnings in
        39.81s", PYTEST_EXIT=0. Julgado pela saída: 510 testes coletados, não é o caso de coleta vazia
        (que sairia 5).
gates:  OK — bash scripts/gates/gates_runner.sh → "✓ gates: limpos (árvore completa, 462 arquivo(s)
        considerados)", GATES_EXIT=0
```

Nota de portão (não reprova, mas registro): `ruff check .` e `ruff format --check .` sobre a árvore inteira acusam 14 erros e 2 arquivos desformatados. Todos fora do escopo do portão canônico e fora do diff: `.claude/skills/**/templates/*.py` (templates do pack, com imports de `src.*` que este projeto não tem), `product/items/015-.../06-evidencias/*.py` e `.harness/proposals/2026-09-06-003.md`. Nenhum arquivo tocado por esta branch aparece na lista.

Critérios de aceite
```
[x] 1 estrutural — app/routers/reference.py existe e exporta o combinado.
    Executado: python -c importando o módulo →
      file: /home/euclidesgc/development/dash_financeiro/app/routers/reference.py
      has screen_date: True
      Reference fields: ['date', 'asked', 'notice']
      EARLIEST: datetime.date(2000, 1, 1) True
      LATEST:   datetime.date(2100, 12, 31) True
      contains 'date.today()': False   (via inspect.getsource)
    Controle cruzado: grep -n "today" app/routers/reference.py → nenhuma linha, exit 1.

[x] 2 comportamental — screen_date(None) com DASH_TODAY=2026-09-05.
    env DASH_TODAY=2026-09-05 → date=datetime.date(2026, 9, 5) asked=False notice=None
    O relógio do processo é 2026-09-07 (date.today() impresso na mesma execução), então o valor 05/09
    só pode ter vindo do ambiente, não de coincidência com o relógio.

[x] 3 comportamental — screen_date("") e screen_date("   ").
    empty  -> date=datetime.date(2026, 9, 5) asked=False notice=None
    spaces -> date=datetime.date(2026, 9, 5) asked=False notice=None

[x] 4 comportamental — os dois limites aceitos, não presumidos.
    "2100-12-31" -> date=datetime.date(2100, 12, 31) asked=True notice=None
    "2000-01-01" -> date=datetime.date(2000, 1, 1)   asked=True notice=None

[x] 5 comportamental — screen_date("banana").
    -> date=datetime.date(2026, 9, 5) asked=False notice='data inválida: data (banana)'

[x] 6 comportamental — "0001-01-01" e "2101-01-01" sem exceção, com o controle positivo conferido.
    A ausência foi medida com try/except BaseException explícito em volta de cada chamada (SystemExit
    se levantasse); nenhuma levantou. E o controle positivo bateu por igualdade de tupla:
      "0001-01-01" -> (date(2026,9,5), False, 'data inválida: data (0001-01-01)')
      "2101-01-01" -> (date(2026,9,5), False, 'data inválida: data (2101-01-01)')
    Ou seja, não é o caso de "não levanta porque o alvo não existe": o alvo existe, responde, e
    responde o valor pedido.
    Saída final do bloco de asserções: "ALL CRITERIA 2-6 ASSERTIONS PASSED", ASSERT_EXIT=0.

[x] 7 comando — o comando literal do critério.
    env -u DASH_TODAY DASH_ENV_FILE=/dev/null .venv/bin/python -c "from datetime import date; from
    app.routers.reference import screen_date; assert screen_date(None).date == date.today()"
    → sem saída, C7_EXIT=0
    Controle negativo (o comando tem dente): a mesma asserção com DASH_TODAY=2026-09-05 fixado, que é
    o comportamento de um leitor que ignora o relógio, sai
      Traceback (most recent call last): File "<string>", line 1, in <module>
      AssertionError
      NEG_A_EXIT=1
    Portanto o zero do critério 7 é informação, não um comando que sai zero de qualquer jeito.
    DASH_ENV_FILE=/dev/null neutraliza o `.env` do repositório; conferi ainda que o `.env` não define
    DASH_TODAY (grep -c "DASH_TODAY" .env → 0).

[x] 8 comando — a suíte do arquivo e a cobertura de casos exigida.
    env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q tests/test_screen_reference.py
    → "9 passed in 0.02s", C8_EXIT=0 (9 testes coletados, não é coleta vazia)
    Os casos exigidos estão nomeados na coleta e conferidos no arquivo:
      data aceita ......... test_both_range_limits_are_accepted_not_assumed (linhas 43-48)
      ausência (None) ..... test_no_query_string_answers_with_the_reference_date_unasked (29-32)
      ausência ("" e "  ") . test_a_blank_parameter_is_absence_not_refusal (35-40)
      data ilegível ....... test_an_unreadable_date_is_refused_with_the_shared_phrase (51-55)
      fora da faixa, dois lados . test_a_readable_date_outside_the_range_is_refused_without_raising
                                  (58-65: "0001-01-01" abaixo, "2101-01-01" acima)
```

Instrumentos do implementer

Nenhum critério dependeu da suíte do avaliado para ser julgado. Os critérios 2 a 6 foram medidos chamando `app.routers.reference.screen_date` diretamente, em processo próprio, com `DASH_TODAY` fixado por mim; o 7 é o comando literal do critério mais o controle negativo; o 8 é o único que roda a suíte do avaliado, e ali a suíte é o objeto sob medição, não a prova.

Achados que você não pediu

1. **`app/queries/period.py` também mudou nesta branch** e não é coberto por critério nenhum. A mudança é a renomeação de `_INVALID_DATE` para `INVALID_DATE` (constante privada virou pública, para o leitor novo reusar a frase), com as duas ocorrências internas atualizadas. Sem mudança de comportamento, e a suíte inteira (510) segue verde. Arquivo: `/home/euclidesgc/development/dash_financeiro/app/queries/period.py`.

2. **A parte do objetivo que diz "nenhuma rota ainda o consome" confere**, embora não seja critério tipado: o único importador de `app.routers.reference` em todo o código é `/home/euclidesgc/development/dash_financeiro/tests/test_screen_reference.py:6`. Nenhum `APIRouter` é montado a partir do módulo.

3. **`app/routers/reference.py` não contém router.** A norma 29 do projeto diz que `app/routers/` guarda o router de cada domínio, um por domínio; este arquivo é um leitor puro morando lá. Não reprova — não há critério sobre isso e o gate7 (fronteira de camada) passou —, mas é uma decisão de lugar que vale confirmar antes de a pasta acumular mais não-routers.

4. **O despacho não me enviou plano, spec nem histórico**, e me instruiu explicitamente a não abrir `product/items/`. Não abri; a pasta `product/items/016-data-de-referencia-no-caminho-de-recusa/` aparece em `git status` como não rastreada e foi ignorada, como o despacho pede.
