VEREDICTO: APROVADO

## Portões

| Portão | Resultado | Saída |
|---|---|---|
| ruff check | OK | `All checks passed!` — `scripts/lint.sh` roda `ruff check app financas ingestao tests` |
| ruff format --check | OK | `141 files already formatted` |
| mypy --strict | não existe neste repositório | medido, não pulado: `.venv/bin/mypy` ausente e nenhuma seção `[tool.mypy]` em `pyproject.toml`. `scripts/lint.sh` (que li e executei) é só ruff |
| pytest | OK | `546 passed, 2 warnings in 45.41s`, `EXIT=0` — coletou testes, não é o caso de saída 5 |
| gates_runner | OK | `✓ gates: limpos (árvore completa, 502 arquivo(s) considerados).` — **502 > 0**, mediu de verdade |

## Critérios de aceite

| # | Tipo | Passou | Evidência executada |
|---|---|---|---|
| 1 | estrutural | sim | Verificação por import e AST: `MODELS = ('gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.5-flash-lite')` (tupla, primeiro item certo), `DEFAULT_MODEL='gemini-2.5-flash'`, `Setup` com campos `['api_key','model','origin']`, `current/view/save/forget` presentes, `UnknownModelError(ValueError)`. `gemini.py`: sem atributo `MODEL`, sem a cadeia `gemini-2.5`, sem `params=`, com `x-goog-api-key`; `ask(question, context, *, api_key, model)` — os dois kw-only e sem default. `routers/advisor.py` sem `load_config`, `gemini_api_key`, `configuracao`. `routers/settings.py:25-26` define `IA` e `IA_FORGET`, que importados valem `/configuracao/ia` e `/configuracao/ia/esquecer`, e mantém `store_value`, `name_payee`, `look_up_cnpj`, `_answer`, `_context`. Fragmento existe e não tem `data-config`; o include aparece 1 vez, só em `configuracao.html` (varri `app/templates/**/*.html` com contagem exata e com regex frouxa) |
| 2 | comando | sim | `EXIT=0`; saída traz `applied 015_advisor_config.sql` e `CREATE TABLE advisor_config (name TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)` |
| 3 | comportamental | sim | `Setup(api_key='chave-do-ambiente-MB9Z', model='gemini-2.5-flash', origin='ambiente')` → após `save`: `Setup(api_key='chave-da-tela-0123456789ABCDEF', model='gemini-2.5-pro', origin='tela')` → `view` com `'tail': 'CDEF'` → após chave de 8: `'tail': None` |
| 4 | comportamental | sim | `GET /consultor` = 200; `data-numero="1"` × 1, `/configuracao` × 3, `GEMINI_API_KEY` × **0** |
| 5 | comportamental | sim | 200; `id="ia"` exatamente 1 ocorrência; posição 30325 > `id="beneficiarios"` em 29150; as três `<option value="gemini-2.5-*"`; `action="/configuracao/ia"`; `Nenhuma chave guardada`; campo é `<input class="field-input" id="ia-chave" name="chave" type="password" autocomplete="off">` — sem `value` |
| 6 | comportamental | sim | POST grava = 200 com `Salvo.` e `id="ia"`; no mesmo processo, `POST /consultor` chama `.../models/gemini-2.5-pro:generateContent` com `{'x-goog-api-key': 'chave-da-tela-0123456789ABCDEF'}` — não a do ambiente, e `gemini-2.5-flash` ausente da URL |
| 7 | comportamental | sim | Segunda gravação com `chave=` vazio: 200, corpo com `Salvo.`, `Há uma chave guardada nesta tela` e `CDEF`; a chamada seguinte leva header terminado em `CDEF` e URL com `gemini-2.5-pro` — modelo mudou, chave não |
| 8 | comportamental | sim | `POST /configuracao/ia/esquecer` = 200, corpo com `Chave apagada.`, `Sem chave gravada aqui, o painel usa a do ambiente`, `MB9Z`, e sem `Há uma chave guardada nesta tela`; chamada seguinte com header `chave-do-ambiente-MB9Z` |
| 9 | comportamental | sim | Nas 4 respostas + `caplog.text` + `capsys.out` + `capsys.err`: `chave-da-tela...` e `chave-do-ambiente-MB9Z` ausentes nos 7 lugares. `POST /consultor` traz `id="indisponivel"` e `a chave foi recusada pelo provedor`. `GET /configuracao` contém `CDEF` e não contém `BCDEF` |
| 10 | comportamental | sim | 400; corpo com `id="ia"`, `id="beneficiarios"`, `id="recusa"` e `Modelo desconhecido. Escolha um da lista: gemini-2.5-flash, gemini-2.5-pro, gemini-2.5-flash-lite.`; `Sem chave gravada aqui, o painel usa a do ambiente`; conferi o banco depois: `SELECT name, value FROM advisor_config` → `[]`, nada escrito |
| 11 | comportamental | sim | URL registrada `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`; `params: None`; corpo JSON só `['contents','systemInstruction']`; header `{'x-goog-api-key': 'chave-da-tela-0123456789ABCDEF'}`. A chave não está na URL, não há `key=`, e `params` sequer é passado |
| 12 | comando | sim | `EXIT=0`, `64 passed`. Nomes coletados cobrem os assuntos exigidos: precedência tela>ambiente, queda para ambiente, quatro últimos caracteres, chave curta; e na tela: seção, gravação, campo vazio que não apaga, apagar, modelo fora da lista com 400 e tela de pé, chave que não vaza, cabeçalho da chamada |

Critérios 1–11 foram verificados por instrumento meu, escrito no scratchpad e nunca dentro do repositório, com dublê próprio de `httpx.post`, banco em `tmp_path` e usuário sem relação com o do dono.

## Caça ao vazamento (o que fui buscar por conta própria)

**Chave reconhecível gravada, painel inteiro exercitado.** Gravei `SEGREDO-VAZOU-QQQQ7777WWWW8888ZZZZ9999` na tela e `SEGREDO-AMBIENTE-VVVV1111YYYY2222` no ambiente, varri **37 rotas registradas** e depois refiz a varredura **ordenada, sem tocar na rota de apagar**, para a chave ficar guardada o percurso inteiro (18 rotas de leitura + `POST /consultor`). Em cada resposta conferi corpo, cabeçalhos, cookies e URL final; e ainda `caplog.text`, stdout e stderr; e a URL, os `params` e o corpo JSON de cada chamada de saída. Repeti em quatro estados do provedor — sucesso, **401 (chave recusada)**, falha de rede e resposta ilegível. **`VAZAMENTOS: []` nos quatro.** Nem `/openapi.json`, `/docs` e `/redoc` — que também respondem — carregam a cadeia.

**Caminho até o provedor.** Não bastou conferir o cabeçalho: registrei `url`, `params` e `json` da chamada. `params` é `None` (o argumento nem existe em `gemini.py`, confirmado pela ausência da cadeia `params=`), a URL não tem query string nenhuma e a chave aparece só em `headers['x-goog-api-key']`. Um dublê que olhasse só o cabeçalho não teria visto a diferença; olhei os dois lados.

**Campo vazio.** Não apaga: `save` só escreve `api_key` quando `api_key.strip()` é verdadeiro, e o modelo é gravado antes, em linha separada — por isso o campo em branco troca o modelo e preserva a chave (critério 7, provado pela chamada de saída, não pela tela).

**Guarda de sessão (norma 24).** Cliente anônimo contra todas as rotas registradas: `rotas sem guarda: {}`. As duas novas respondem `302` sem cookie — `{('POST','/configuracao/ia'): 302, ('POST','/configuracao/ia/esquecer'): 302}`.

**Painel sem chave nenhuma.** Sem `GEMINI_API_KEY` e sem nada gravado, nenhuma rota devolveu 5xx, e `POST /consultor` responde 200 com `id="indisponivel"`, a palavra `indisponível` e `data-numero="1"` na tela — os números determinísticos de pé, a leitura da IA declarada indisponível.

**Segredo fora do repositório.** `.gitignore` cobre `data/`, `*.sqlite` e `.env*` (com `!.env.example`); `.env.example` traz `GEMINI_API_KEY=` vazio; nenhuma cadeia com cara de chave no `git diff`.

## Achados que não reprovam

1. **Chave com CR/LF derruba a rota em 500, e a chave entra na mensagem da exceção.** `save` só faz `.strip()`, então um `\r\n` no meio do valor é gravado. Na chamada de saída, `h11` levanta `LocalProtocolError: Illegal header value b'chave-INJETADA-7777\r\nX-Injetado: sim'` — que **não** é `httpx.HTTPError` nem `ValueError`, e por isso escapa dos `except` de `app/advisor/gemini.py:74-81`. Medido: `POST /consultor` responde **500** em vez de degradar. O corpo devolvido é só `Internal Server Error` e nada vazou no cliente, mas o texto da exceção carrega a chave inteira, e `app/__main__.py` roda `uvicorn`, que registra o traceback de exceção não tratada. Alcance real é estreito: exige o dono colar deliberadamente uma quebra de linha no meio da chave (a do fim já é removida pelo `strip`), num painel local de usuário único. Conserto barato: recusar caracteres de controle em `save`, ou alargar o `except` de `ask`.
2. **Chave com acento degrada com a frase errada.** `chave-acentuada-çãé-8888WWWW` faz `httpx` levantar `UnicodeEncodeError`, que é subclasse de `ValueError` e cai no `except` de formato — a tela diz "o modelo respondeu num formato inesperado" quando o problema é a chave. Sem vazamento e sem quebra (200), só uma mensagem que aponta para o lado errado.
3. **A base do ramo está defasada em 6 commits de `develop`.** Por isso `git diff develop` mostra a exclusão de `product/items/{023,024,025}/03-plan.md`, do veredicto da fase 1 do item 022 e a reversão de `product/state.json` — nada disso é obra desta fase. O diff próprio dos dois commits são 13 arquivos, só código e teste. Conferi a sobreposição: `develop` mexeu em `spending/period/ahead/gastos`, a fase em `advisor/settings`, sem arquivo em comum. A migração `015` também não colide — `develop` para em `011`.
4. **Salto de numeração nas migrações: 011 → 015.** Presumivelmente 012–014 estão reservadas para os itens 023/024/025, cujos planos já foram aprovados em `develop`. Como o critério 2 exige `015` por escrito, é escolha e não descuido; fica o registro de que `tests/test_migrations.py` passa a fixar `max(version) == "015"`, e quem entregar a 012 depois vai ter de mexer nessa asserção.
5. **Mudanças em testes preexistentes são mecânicas.** `tests/test_advisor.py` só ganhou o argumento `model=` nas seis chamadas de `ask`, e trocou a asserção `"GEMINI_API_KEY" in ...` por `"/configuracao" in ...`, coerente com a mensagem nova. Nenhuma asserção foi removida ou afrouxada.

## Instrumentos do implementer

Só o **critério 12**, que por construção é a execução da suíte do avaliado. Os critérios 1 a 11 foram provados por harness independente meu, sem importar nada de `tests/test_advisor_config.py` nem de `tests/test_configuracao_ia_screen.py` — do diretório `tests/` reaproveitei apenas `app.auth.seed.seed_user` e `app.taxonomy.seed` para montar banco e sessão.

Não recebi plano, brief nem spec, e não abri `product/items/027-configuracao-do-gemini/`. O arquivo de critérios trazia só objetivo e critérios.
