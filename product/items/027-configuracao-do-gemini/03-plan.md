# Plano — 027-configuracao-do-gemini

**Item:** `027-configuracao-do-gemini` · **Trilha:** rápida · **Fonte aprovada:**
`01-brief.md` (RF-01 a RF-08) · **Terreno:** `00-discovery.md` · **Uma fase**,
uma branch integrada em `develop`.

> A decisão de segurança do item está fechada em `00-discovery.md` e **não se
> reabre aqui**: a chave mora no SQLite local, sem cifragem em repouso, com o
> ambiente valendo quando não há nada gravado; o que foi gravado na tela vence o
> ambiente; a chave nunca volta inteira para a tela; o modelo se escolhe de uma
> lista declarada no código. Este plano executa e verifica essa decisão.

## Objetivo

Ao fim da fase existe **um** leitor da configuração da IA — a chave em vigor e o
modelo em vigor —, e as duas chamadas que hoje leem `GEMINI_API_KEY` e a
constante de modelo passam a consumi-lo. `/configuracao` ganha a seção que grava
os dois, com a mesma interação de todas as outras gravações desta tela: acerto
responde `200` com a tela de pé e a confirmação, erro responde `400` com a tela
de pé e a frase em português. `/consultor` deixa de nomear um problema que ele
mesmo não deixa resolver. A chave inteira não aparece em resposta HTTP, em log
nem em mensagem de erro — inclusive quando o provedor a recusa —, chega ao
provedor no **cabeçalho** e não na query string, e campo vazio não apaga o que
está guardado: apagar é um ato próprio, com nome e botão.

**É uma fase só, e o corte é o de contrato:** o leitor único, a gravação e a tela
compartilham a mesma forma de dado, e não há segundo consumidor para o qual uma
premissa errada se espalhe. Cortar em duas entregaria uma primeira fase em que
`/consultor` aponta para uma seção de `/configuracao` que ainda não existe — a
tela mentindo, que é exatamente a classe de defeito que este item fecha.

## O terreno, medido

| Sítio | Hoje | O que falta |
|---|---|---|
| `app/config.py:29,68` | `gemini_api_key` lido de `GEMINI_API_KEY` | nada: continua sendo a camada de ambiente, e passa a ter **um** leitor acima dela |
| `app/advisor/gemini.py:6,67,87` | `MODEL = "gemini-2.5-flash"`, constante de módulo | o modelo vira parâmetro nomeado obrigatório de `ask` |
| `app/advisor/gemini.py:58` | a recusa sem chave cita `falta a chave GEMINI_API_KEY no ambiente` | citar a tela onde se informa |
| `app/advisor/gemini.py:68` | `params={"key": api_key}` — a chave na query string | `headers={"x-goog-api-key": api_key}` |
| `app/routers/advisor.py:64,121` | dois `load_config().gemini_api_key` | um leitor por resposta; **nenhuma rota nova** aqui |
| `app/templates/consultor.html:60-63` | `Sem GEMINI_API_KEY no ambiente a leitura da IA não roda.` | apontar `/configuracao` |
| `app/templates/configuracao.html:86-136` | três seções: `fatos`, `metas`, `beneficiarios` | a quarta, `ia`, por **uma** linha de `{% include %}` depois do `</section>` da linha 136 |
| `app/routers/settings.py:49-113` | três POSTs da tela — `store_value`, `name_payee`, `look_up_cnpj` — que gravam e re-renderizam pelo mesmo `_answer` | mais dois, `store_ia` e `forget_ia`, na mesma forma |
| `app/routers/settings.py:156-168` | `_answer` monta a tela sem nada de IA | três linhas no fim de `_answer` |
| `app/migrations/sql/` | vai até `011_payee_names.sql` | `015_advisor_config.sql` — `012`, `013` e `014` estão reservadas a itens simultâneos |

Cinco fatos decidem o desenho e não se re-discutem:

1. `tests/test_route_guard.py:37-48` varre **toda** rota registrada e exige
   `302` ou `401` sem sessão. As duas rotas novas entram na varredura sozinhas:
   a norma 24 é cobrada sem critério novo e sem teste novo.
2. `tests/conftest.py:76-87` troca `httpx.post` por uma recusa. Todo teste de
   provedor usa dublê instalado por `monkeypatch.setattr` dentro do próprio
   teste, como `tests/test_advisor.py:129` já faz, e nenhum sai para a rede.
3. `tests/test_configuracao_screen.py:20,64` casa **todo** `data-config="..."` da
   página com o catálogo inteiro. O fragmento novo **não pode usar
   `data-config`**, ou uma asserção de catálogo quebra por um atributo que não é
   de catálogo.
4. `app/migrations/runner.py:36-38` ordena por nome de arquivo e versiona pelo
   prefixo antes do primeiro `_`. `015` aplica depois de `011` e depois de
   `012`–`014`, existam elas ou não.
5. `app/routers/settings.py:49-64` é a forma desta tela desde o item `015`: a
   função que grava chama `_answer`, que é a mesma que monta o contexto, então a
   recusa sai com `400` **e a tela inteira de pé**, com a frase em português no
   bloco `notices` do cabeçalho (`app/templates/configuracao.html:59-64`). As
   duas rotas da IA moram neste arquivo justamente para herdar essa forma.

## Decisões resolvidas por padrão, não por pergunta

| Dúvida | O que decidiu | Decisão |
|---|---|---|
| Onde mora o leitor? | Norma 29: domínio é pasta, e `app/advisor/` já é a pasta do domínio | `app/advisor/config.py`, com `current`, `view`, `save`, `forget` |
| Onde moram as rotas de gravação? | Quem sabe montar `configuracao.html` é `app/routers/settings.py`, e a recusa precisa sair com a tela de pé | em `app/routers/settings.py`, ao lado de `name_payee` e `look_up_cnpj`. Descartado: pô-las em `app/routers/advisor.py`, que a norma 29 sugeriria — de lá a recusa só chegaria à tela por redirecionamento, e uma interação diferente do resto do painel apareceria justamente no pior momento, quando o dono errou. **Nenhum router novo**, e por isso `app/main.py` **não é tocado** |
| Como a tela responde depois de gravar? | A forma do item `015`, e nada mais | `200` com a tela renderizada e `Salvo.` no bloco `notices`; recusa é `400` com a tela renderizada e a frase em português no mesmo bloco — o mesmo `_answer` que `store_value` usa |
| Como este item toca `settings.py` sem conflitar com as worktrees vizinhas? | Dois itens simultâneos vão acrescentar chave de contexto neste arquivo | só se **acrescenta**: três constantes no bloco do topo, três linhas no fim de `_answer` e duas funções depois de `look_up_cnpj`. Nenhuma função existente é reescrita, e `_context` — onde os vizinhos vão mexer — **não é tocado** |
| Como a chave chega ao provedor? | Query string entra em log de servidor, em proxy e em histórico por construção, que é o que RF-07 existe para impedir; a API do Gemini aceita as duas formas | **cabeçalho `x-goog-api-key`**. Decidido na revisão deste plano pelo dono, e não pelo brief: o custo é uma linha, e a alternativa era registrar como pendência um vazamento conhecido |
| Forma da tabela | Apagar a chave não pode encostar no modelo, e o inverso também não | chave-valor: `advisor_config(name, value, updated_at)`, uma linha por coisa |
| Quantas coisas o leitor devolve? | A chamada quer `api_key` e `model`; a tela quer origem, quatro últimos e a lista | duas saídas: `current(conn) -> Setup(api_key, model, origin)` para a chamada, `view(conn)` para a tela — e `view` **não** carrega a chave |
| Quantos caracteres a tela mostra? | RF-05 diz "no máximo os quatro últimos" | exatamente **quatro**, e **nenhum** quando a chave tem oito caracteres ou menos: quatro de oito é metade do segredo |
| Quais modelos a lista declara? | O brief exige lista declarada e não a enumera | `gemini-2.5-flash` (padrão, o de hoje), `gemini-2.5-pro`, `gemini-2.5-flash-lite`. **Lacuna registrada no retorno**: os nomes são escolha minha, não do brief |
| A recusa de modelo ecoa o valor enviado? | O valor vem de pedido forjado e viajaria até a tela | não: a frase lista os modelos declarados, montada a partir de `MODELS` dentro de `UnknownModelError`; o router só imprime `str(refusal)`, como já faz com `InvalidValueError` |
| `app/config.py` muda? | RF-01 pede leitor único do **efetivo**; `GEMINI_API_KEY` continua sendo variável de ambiente como as outras | **não é tocado** |
| Ordem de validação em `save` | RF-06 diz "recusado no ato da gravação" | o modelo é conferido **antes** de qualquer escrita: modelo fora da lista não grava nem o modelo nem a chave |
| A chave é limpa ao gravar? | Chave colada carrega `\n` no fim, e o provedor recusa uma chave correta | `strip()` na gravação, uma vez |
| Algum portão novo? | Norma 6, e nada aqui é regra de estilo | nenhum arquivo entra em `scripts/gates/`; `scripts/lint.sh` e `pyproject.toml` não mudam — `httpx` e `pytest` já estão declarados |

## A seção, na linguagem visual do painel

A seção segue `product/00-linguagem-visual.md` — **instrumento de leitura, não
app de banco** — e não introduz token, cor, classe nem folha de estilo: reusa
`panel panel-wide`, `section-title`, `lede`, `eyebrow` para o rótulo em
versalete, `field`/`field-label`/`field-input` para os dois campos, e `<code>`
para os quatro caracteres do fim da chave. A confirmação e a recusa **não são
impressas pelo fragmento**: saem no bloco `notices` do cabeçalho da tela
(`app/templates/configuracao.html:59-64`), que é onde toda gravação desta tela
já responde — a mesma aresta entre `notice-done` e `notice`, no mesmo lugar. O
`<select class="field-input">` é o mesmo de `app/templates/regras.html:35` e
`app/templates/gastos.html:24`, então nada é acrescentado a `app/static/css/` —
que, aliás, está fora do escopo deste item.

A seção **não leva escala graduada**: a régua do documento diz que a marcação
aparece onde há distância a percorrer, e aqui não há — é uma configuração, não
uma projeção. O ato de gravar mantém o nome do começo ao fim: quem clica em
"Salvar" lê "Salvo."; quem clica em "Apagar a chave guardada" lê "Chave
apagada." O estado é a própria confirmação: a frase abaixo do título diz se há
chave, de onde ela vem e em que quatro caracteres termina.

---

## Fase 1 — A configuração da IA na tela, com a chave guardada e nunca exibida (api)

**Objetivo da fase:** existe um leitor único da chave e do modelo da IA, a tela
`/configuracao` grava os dois com a mesma resposta das outras gravações dela, e a
chave inteira não sai em nenhuma resposta, log ou URL.

**Critérios de aceite:**

- [ ] `estrutural` — RF-01, RF-03, RF-07
      Existe `app/advisor/config.py`, e ele exporta `MODELS` (tupla cujo
      primeiro item é a string `gemini-2.5-flash`), `DEFAULT_MODEL`, a classe
      `Setup` com os campos `api_key`, `model` e `origin`, as funções `current`,
      `view`, `save` e `forget`, e a exceção `UnknownModelError`.
      `app/advisor/gemini.py` **não** define `MODEL` e **não** contém a cadeia
      `gemini-2.5`; a assinatura de `ask` tem os parâmetros nomeados obrigatórios
      `api_key` e `model`; o arquivo contém a cadeia `x-goog-api-key` e **não**
      contém a cadeia `params=`. `app/routers/advisor.py` **não** contém as
      cadeias `load_config`, `gemini_api_key` nem `configuracao`.
      `app/routers/settings.py` define as funções `store_ia` e `forget_ia` e as
      constantes `IA` (valor `/configuracao/ia`) e `IA_FORGET` (valor
      `/configuracao/ia/esquecer`), e **continua** definindo `store_value`,
      `name_payee`, `look_up_cnpj`, `_answer` e `_context`. Existe
      `app/templates/fragments/configuracao_ia.html`, que **não** contém a cadeia
      `data-config`; `app/templates/configuracao.html` contém exatamente uma
      ocorrência de `{% include "fragments/configuracao_ia.html" %}` — nenhum
      outro arquivo de `app/templates/` a contém.
- [ ] `comando` — RF-02
      `rtk proxy rm -f /tmp/027-migracao.sqlite && rtk proxy env
      DASH_ENV_FILE=/dev/null DASH_DB_PATH=/tmp/027-migracao.sqlite
      .venv/bin/python -c 'from app.migrate import run_migrations; from app.db
      import connect; run_migrations(); print(connect().execute("SELECT sql FROM
      sqlite_master WHERE name = ?", ("advisor_config",)).fetchone()[0])'`
      sai com código `0`; a saída contém a linha `applied
      015_advisor_config.sql` e um `CREATE TABLE advisor_config` que declara as
      colunas `name`, `value` e `updated_at`. Sem a tabela, `fetchone()[0]`
      levanta `TypeError` e o comando sai com `1`; um arquivo de migração com
      outro número não imprime a linha `applied`.
- [ ] `comportamental` — RF-01, RF-02, RF-05
      *Dado* um banco em diretório temporário com as migrações aplicadas, e o
      ambiente do processo com `GEMINI_API_KEY=chave-do-ambiente-MB9Z` e
      `DASH_ENV_FILE=/dev/null`
      *Quando* `app.advisor.config.current(conn)` é chamada com nada gravado;
      depois `app.advisor.config.save(conn, api_key="chave-da-tela-0123456789ABCDEF",
      model="gemini-2.5-pro")` e `current(conn)` de novo; depois
      `app.advisor.config.view(conn)`; e por fim
      `save(conn, api_key="12345678", model="gemini-2.5-pro")` seguido de
      `view(conn)`
      *Então* a primeira chamada devolve `.api_key` igual a
      `chave-do-ambiente-MB9Z`, `.model` igual a `gemini-2.5-flash` e `.origin`
      igual a `ambiente`; a segunda devolve `.api_key` igual a
      `chave-da-tela-0123456789ABCDEF`, `.model` igual a `gemini-2.5-pro` e
      `.origin` igual a `tela`; o primeiro `view` traz `tail` igual a `CDEF`; e
      o segundo `view` traz `tail` igual a `None` — chave de oito caracteres ou
      menos não mostra caractere nenhum
- [ ] `comportamental` — RF-02, RF-03
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_TODAY=2026-09-05`, **sem**
      `GEMINI_API_KEY` no ambiente do processo, banco em diretório temporário,
      nada gravado na tabela `advisor_config` e sessão autenticada
      *Quando* `GET /consultor` é buscada
      *Então* a resposta é `200`; o HTML contém `data-numero="1"` — os números
      determinísticos continuam de pé, e é o invariante 23 —; contém a cadeia
      `/configuracao`; e **não** contém a cadeia `GEMINI_API_KEY`. Hoje a tela
      traz `GEMINI_API_KEY` e não traz `/configuracao`
- [ ] `comportamental` — RF-03, RF-06
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_TODAY=2026-09-05`, banco em diretório
      temporário, nada gravado na tabela `advisor_config` e sessão autenticada
      *Quando* `GET /configuracao` é buscada
      *Então* a resposta é `200`; o HTML contém `id="ia"` exatamente uma vez; a
      posição de `id="ia"` no documento é **posterior** à de
      `id="beneficiarios"`; o HTML contém `<option value="gemini-2.5-flash"`,
      `<option value="gemini-2.5-pro"` e `<option value="gemini-2.5-flash-lite"`;
      contém `action="/configuracao/ia"`; contém a frase
      `Nenhuma chave guardada`; e contém um `<input` com `name="chave"` que
      **não** traz atributo `value`
- [ ] `comportamental` — RF-03, RF-06, RF-08
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_TODAY=2026-09-05`,
      `GEMINI_API_KEY=chave-do-ambiente-MB9Z` no ambiente do processo, banco em
      diretório temporário, sessão autenticada, e `httpx.post` substituído por um
      dublê que registra `url` e `headers` da chamada e devolve uma resposta cujo
      `json()` traz `{"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}`
      *Quando* `POST /configuracao/ia` é enviada com
      `chave=chave-da-tela-0123456789ABCDEF` e `modelo=gemini-2.5-pro`, e em
      seguida, **no mesmo processo e sem recriar a aplicação**, `POST /consultor`
      é enviada com `pergunta=e daí?`
      *Então* a primeira resposta tem código `200`, e o corpo dela contém
      `Salvo.` e `id="ia"` — a tela inteira volta de pé, sem redirecionamento; e
      a chamada registrada pelo dublê tem `gemini-2.5-pro` na URL e
      `headers["x-goog-api-key"]` igual a `chave-da-tela-0123456789ABCDEF` — não
      `chave-do-ambiente-MB9Z`, e não `gemini-2.5-flash`
- [ ] `comportamental` — RF-04
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_TODAY=2026-09-05`, banco em diretório
      temporário, sessão autenticada, `httpx.post` substituído por um dublê que
      registra `url` e `headers` da chamada e devolve uma resposta cujo `json()`
      traz `{"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}`, e
      `POST /configuracao/ia` já enviada uma vez com
      `chave=chave-da-tela-0123456789ABCDEF` e `modelo=gemini-2.5-flash`
      *Quando* `POST /configuracao/ia` é enviada de novo com `chave=` **vazio** e
      `modelo=gemini-2.5-pro`, e em seguida `POST /consultor` com
      `pergunta=e daí?`
      *Então* a segunda gravação responde `200`, e o corpo dela contém `Salvo.`,
      a frase `Há uma chave guardada nesta tela` e a cadeia `CDEF`; e a chamada
      registrada pelo dublê tem `headers["x-goog-api-key"]` igual a
      `chave-da-tela-0123456789ABCDEF` e `gemini-2.5-pro` na URL — o modelo mudou
      e a chave não, que é a diferença entre campo vazio e ato de apagar
- [ ] `comportamental` — RF-02, RF-04
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_TODAY=2026-09-05`,
      `GEMINI_API_KEY=chave-do-ambiente-MB9Z` no ambiente do processo, banco em
      diretório temporário, sessão autenticada, `httpx.post` substituído por um
      dublê que registra `url` e `headers` da chamada e devolve uma resposta cujo
      `json()` traz `{"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}`,
      e `POST /configuracao/ia` já enviada com
      `chave=chave-da-tela-0123456789ABCDEF` e `modelo=gemini-2.5-flash`
      *Quando* `POST /configuracao/ia/esquecer` é enviada sem corpo, e em seguida
      `POST /consultor` com `pergunta=e daí?`
      *Então* a resposta da primeira tem código `200` e o corpo dela contém
      `Chave apagada.`, a frase
      `Sem chave gravada aqui, o painel usa a do ambiente` e a cadeia `MB9Z`, e
      **não** contém `Há uma chave guardada nesta tela`; e a chamada registrada
      pelo dublê tem `headers["x-goog-api-key"]` igual a
      `chave-do-ambiente-MB9Z` — apagar na tela devolve a vez ao ambiente
- [ ] `comportamental` — RF-05, RF-07
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_TODAY=2026-09-05`,
      `GEMINI_API_KEY=chave-do-ambiente-MB9Z` no ambiente do processo, banco em
      diretório temporário, sessão autenticada, `caplog.set_level(logging.DEBUG)`
      ativo, `httpx.post` substituído por um dublê cujo `raise_for_status()`
      levanta `httpx.HTTPStatusError` com `response.status_code` igual a `401`, e
      `POST /configuracao/ia` já enviada com
      `chave=chave-da-tela-0123456789ABCDEF` e `modelo=gemini-2.5-flash`
      *Quando* são buscadas, na mesma execução, `GET /configuracao`,
      `GET /consultor`, `POST /configuracao/ia` com
      `chave=chave-da-tela-0123456789ABCDEF` e `modelo=nao-existe`, e
      `POST /consultor` com `pergunta=e daí?`
      *Então* a cadeia `chave-da-tela-0123456789ABCDEF` **não** aparece no corpo
      de nenhuma das quatro respostas, nem em `caplog.text`, nem em
      `capsys.readouterr().out`, nem em `capsys.readouterr().err`; a cadeia
      `chave-do-ambiente-MB9Z` também não aparece em nenhum desses seis lugares;
      a resposta de `POST /consultor` contém `id="indisponivel"` e a frase
      `a chave foi recusada pelo provedor`; e o corpo de `GET /configuracao`
      contém `CDEF` e **não** contém `BCDEF` — quatro caracteres, não cinco
- [ ] `comportamental` — RF-06
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_TODAY=2026-09-05`,
      `GEMINI_API_KEY=chave-do-ambiente-MB9Z` no ambiente do processo, banco em
      diretório temporário, **nada gravado** na tabela `advisor_config` e sessão
      autenticada
      *Quando* `POST /configuracao/ia` é enviada com
      `chave=chave-da-tela-0123456789ABCDEF` e `modelo=gemini-9-turbo`
      *Então* a resposta tem código `400`; o corpo traz a tela inteira de pé —
      contém `id="ia"` e `id="beneficiarios"` —; contém `id="recusa"` e a frase
      `Modelo desconhecido. Escolha um da lista:` seguida dos três nomes
      `gemini-2.5-flash`, `gemini-2.5-pro` e `gemini-2.5-flash-lite`; e contém
      `Sem chave gravada aqui, o painel usa a do ambiente` — a recusa do modelo
      também não gravou a chave, porque a lista é conferida antes de qualquer
      escrita
- [ ] `comportamental` — RF-07
      *Dado* o painel servido a partir deste repositório com
      `DASH_ENV_FILE=/dev/null`, `DASH_TODAY=2026-09-05`, banco em diretório
      temporário, sessão autenticada, `httpx.post` substituído por um dublê que
      registra `url`, `params`, `headers` e `json` da chamada e devolve uma
      resposta cujo `json()` traz
      `{"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}`, e
      `POST /configuracao/ia` já enviada com
      `chave=chave-da-tela-0123456789ABCDEF` e `modelo=gemini-2.5-flash`
      *Quando* `POST /consultor` é enviada com `pergunta=e daí?`
      *Então* a chamada registrada pelo dublê tem
      `headers["x-goog-api-key"]` igual a `chave-da-tela-0123456789ABCDEF`; e a
      cadeia `chave-da-tela-0123456789ABCDEF` **não** aparece em `str(url)`, o
      `params` registrado é `None` ou não contém essa cadeia, e `str(url)` não
      contém a cadeia `key=` — a chave viaja no cabeçalho, e a URL que iria para
      um log de proxy não a carrega
- [ ] `comando` — RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08
      `rtk proxy env DASH_ENV_FILE=/dev/null .venv/bin/python -m pytest -q
      tests/test_advisor_config.py tests/test_configuracao_ia_screen.py
      tests/test_advisor.py tests/test_consultor_screen.py
      tests/test_configuracao_screen.py tests/test_config.py
      tests/test_route_guard.py` sai com código `0`, e:
      `tests/test_advisor_config.py` exercita a precedência do gravado sobre o
      ambiente, a queda para o ambiente sem nada gravado, os quatro últimos
      caracteres e a chave curta que não mostra nenhum;
      `tests/test_configuracao_ia_screen.py` exercita a seção na tela, a
      gravação, o campo vazio que não apaga, o ato de apagar, o modelo fora da
      lista recusado com `400` e a tela de pé, a chave que não vaza e o cabeçalho
      da chamada de saída. Os cinco arquivos restantes já existem e seguem verdes

> A DoD global é do CI e não se repete aqui.

### Etapas

- [ ] **1.1 — Criar `app/migrations/sql/015_advisor_config.sql`: a tabela da
      configuração da IA.**
      Método:
      ```sql
      CREATE TABLE advisor_config (
          name TEXT PRIMARY KEY,
          value TEXT NOT NULL,
          updated_at TEXT NOT NULL
      );
      ```
      Quem a aplica é `app/migrate.py::run_migrations`, chamada por
      `app/main.py::create_app` no boot e por `tests/conftest.py:96-101` em cada
      banco temporário; nenhum executor novo entra no projeto.
      *Considerando:* nada antes — é a primeira etapa.
      *Justificativa:* RF-02 e norma 34. O número é **exatamente** `015`:
      `012`, `013` e `014` estão reservadas a itens que rodam em worktrees
      simultâneas, e duas migrações com o mesmo prefixo fazem
      `app/migrations/runner.py:38` pular a segunda em silêncio — o esquema do
      dono ficaria sem a tabela e o defeito apareceria como `no such table` em
      produção, não em teste. Chave-valor, e não uma linha com duas colunas,
      porque apagar a chave é `DELETE` de uma linha e não pode encostar no
      modelo (RF-04).

- [ ] **1.2 — Criar `app/advisor/config.py`: o leitor único, a gravação e o que
      a tela pode ver.**
      Método:
      ```python
      MODELS = ("gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite")
      DEFAULT_MODEL = MODELS[0]
      API_KEY, MODEL = "api_key", "model"
      FROM_SCREEN, FROM_ENV, ABSENT = "tela", "ambiente", "ausente"
      TAIL, MIN_TO_SHOW = 4, 8
      UNKNOWN_MODEL = "Modelo desconhecido. Escolha um da lista: {models}."

      class UnknownModelError(ValueError): ...

      @dataclass(frozen=True)
      class Setup:
          api_key: str | None
          model: str
          origin: str

      def current(conn: sqlite3.Connection) -> Setup
      def view(conn: sqlite3.Connection) -> dict
      def save(conn: sqlite3.Connection, *, api_key: str, model: str) -> None
      def forget(conn: sqlite3.Connection) -> None
      ```
      `current` lê as duas linhas da tabela; chave gravada não vazia vence
      `load_config().gemini_api_key`; sem nenhuma das duas, `api_key` é `None` e
      `origin` é `ausente`; `model` cai em `DEFAULT_MODEL`. `save` confere
      `model in MODELS` **antes** de escrever qualquer coisa e levanta
      `UnknownModelError(UNKNOWN_MODEL.format(models=", ".join(MODELS)))`; grava
      o modelo sempre e a chave só quando `api_key.strip()` não é vazia.
      `forget` apaga só a linha da chave. `view` devolve `stored`, `origin`,
      `tail`, `model` e `models` — e **nenhum** valor que contenha a chave;
      `tail` são os quatro últimos caracteres da chave em vigor quando ela tem
      mais de `MIN_TO_SHOW` caracteres, e `None` caso contrário.
      *Considerando 1.1:* a tabela existe.
      *Justificativa:* RF-01, RF-02, RF-04, RF-05, RF-06. O módulo mora em
      `app/advisor/` porque a norma 29 faz do domínio uma pasta e o consultor já
      é uma; `app/config.py` continua sendo a camada de ambiente e **não é
      tocado**, o que também reduz a superfície de conflito com as cinco
      worktrees vizinhas. `view` existir separada de `current` é o que torna
      RF-05 verificável por construção: a tela recebe um dicionário que nunca
      teve a chave dentro, em vez de receber a chave e prometer não imprimi-la.
      `view` também não conhece URL nem mensagem de tela: quem grava é quem sabe
      onde o formulário posta e o que dizer depois, e é `app/routers/settings.py`
      (norma 30). A frase da recusa nasce aqui porque é aqui que `MODELS` mora —
      o router só imprime `str(refusal)`, como já faz com `InvalidValueError`.
      O limite de oito caracteres não é zelo — quatro de oito é metade do
      segredo, e a régua "no máximo quatro" precisa de um piso.

- [ ] **1.3 — Modificar `app/advisor/gemini.py`: o modelo vira parâmetro, e a
      frase da chave ausente aponta a tela.**
      `MODEL` sai do módulo. `ask` passa a
      `def ask(question: str, context: str, *, api_key: str | None, model: str) -> Reading`,
      usa `ENDPOINT.format(model=model)` e devolve `Reading(text=text, model=model)`.
      A mensagem de `app/advisor/gemini.py:57-60` passa a
      `"A leitura da IA está indisponível: falta a chave da IA. Informe em "`
      `"/configuracao. Os números da tela são os mesmos, e eles não dependem dela."`.
      Instrução, tempo limite e as quatro traduções de erro para português
      **não mudam**.
      *Considerando 1.2:* a lista de modelos e o padrão moram lá, e este arquivo
      deixa de conhecer os dois.
      *Justificativa:* RF-01, RF-03. `model` é obrigatório e sem valor padrão de
      propósito: um padrão aqui recria a constante que o item existe para tirar,
      e um chamador esquecido passaria em silêncio. A frase muda porque é ela
      que o brief nomeia como o defeito — a tela dizia o nome de uma variável de
      ambiente para um dono que não tem onde editá-la.

- [ ] **1.4 — Modificar `app/advisor/gemini.py`: a chave viaja no cabeçalho, não
      na URL.**
      Na chamada de `httpx.post` (linha 66-71), `params={"key": api_key}` sai e
      entra `headers={"x-goog-api-key": api_key}`. O corpo, o tempo limite e o
      tratamento de erro **não mudam**. Depois desta etapa o arquivo não contém
      mais a cadeia `params=`.
      *Considerando 1.3:* é a mesma chamada, já reescrita para receber `model`.
      *Justificativa:* RF-07. Query string é o pior lugar possível para um
      segredo: entra em log de servidor, em cache de proxy e em histórico por
      construção, e nenhum desses lugares está sob controle deste produto —
      é exatamente a fuga que RF-07 existe para impedir, e ela não depende de
      este produto passar a registrar chamadas de saída. A API do Gemini aceita
      as duas formas, então o custo é uma linha; o cabeçalho não é registrado
      por padrão em nenhuma delas. É etapa própria, e não um detalhe de 1.3,
      porque a auditoria de segurança que este item exige (`00-discovery.md`)
      precisa ver a mudança com o porquê colado nela.

- [ ] **1.5 — Modificar `app/routers/advisor.py`: o consultor consome o leitor.**
      `_context` (linha 106) abre `setup = config.current(conn)` e devolve
      `"has_key": bool(setup.api_key)`; `consult` (linha 64) passa a
      `ask(asked, as_text(numbers), api_key=setup.api_key, model=setup.model)`,
      com `setup = config.current(conn)` lido na própria função. O import
      `from app.config import load_config` fica órfão e **sai**; entra
      `from app.advisor import config`. **Nenhuma rota nova neste arquivo.**
      *Considerando 1.2:* o leitor existe, e o router não monta consulta nem dá
      commit (norma 30).
      *Justificativa:* RF-01, RF-08. RF-08 sai de graça: `current` lê banco e
      ambiente a cada resposta, e nada é memorizado no processo. As rotas de
      gravação **não** moram aqui, apesar de a norma 29 apontar para o router do
      domínio, porque quem sabe montar `configuracao.html` é
      `app/routers/settings.py` — e a recusa precisa sair com a tela de pé
      (etapa 1.8). Assim `app/main.py` **não é tocado** e a lista de
      `include_router` não conflita com as worktrees vizinhas.

- [ ] **1.6 — Criar `app/templates/fragments/configuracao_ia.html`: a seção da
      IA.**
      `<section id="ia" class="panel panel-wide">` com `section-title`
      `Leitura da IA`; um `lede` dizendo que a IA lê e explica e que quem calcula
      é código testado, que a chave fica no banco desta máquina — fora do
      versionamento — e que ela nunca volta inteira para a tela; a frase de
      estado, uma das três: `Nenhuma chave guardada, e o ambiente também não tem
      uma.`, `Sem chave gravada aqui, o painel usa a do ambiente, terminada em
      <code>{{ ia['tail'] }}</code>.` ou `Há uma chave guardada nesta tela,
      terminada em <code>{{ ia['tail'] }}</code>.` — o trecho da terminação só
      aparece quando `ia['tail']` existe. Um `<form class="form" method="post"
      action="{{ ia_action }}">` com `<input class="field-input" id="ia-chave"
      name="chave" type="password" autocomplete="off">` **sem atributo `value`**,
      a ajuda `Deixar em branco não altera a chave guardada.`, um
      `<select class="field-input" id="ia-modelo" name="modelo">` sobre
      `ia['models']` com `selected` no `ia['model']`, e o botão `Salvar`. Quando
      `ia['stored']`, um segundo formulário para `ia_forget_action` com o botão
      `Apagar a chave guardada`. **Nenhum** `data-config`, e **nenhum** bloco de
      `notice` ou `notice-done`.
      *Considerando 1.2:* tudo o que o fragmento imprime vem de `view`, que
      nunca viu a chave.
      *Justificativa:* RF-03, RF-04, RF-05 e norma 27. O campo sem `value` é o
      que cumpre "o campo da chave chega vazio à tela" no lugar certo — no HTML,
      antes de qualquer JavaScript —, e `type="password"` impede que uma captura
      de tela do painel leve a chave junto no momento em que ela é colada. O
      fragmento não imprime confirmação nem recusa porque
      `app/templates/configuracao.html:59-64` já as imprime no cabeçalho da tela
      para as três gravações que existem; um segundo lugar de mensagem faria
      esta seção responder diferente do resto da mesma página.
      `data-config` está proibido porque `tests/test_configuracao_screen.py:64`
      casa **todo** `data-config` da página com o catálogo de fatos e metas, e um
      atributo a mais reprovaria um teste que nada tem a ver com este item.
      Nenhuma classe, token ou cor nova: `product/00-linguagem-visual.md` é a
      fonte, `app/static/css/` está fora do escopo, e o
      `<select class="field-input">` já é o idioma de
      `app/templates/regras.html:35`.

- [ ] **1.7 — Modificar `app/templates/configuracao.html`: uma linha de
      `include`.**
      `{% include "fragments/configuracao_ia.html" %}` entra imediatamente depois
      do `</section>` da linha 136 — o que fecha `<section id="beneficiarios">`,
      aberta na linha 86 — e antes do `</main>` da linha 137.
      *Considerando 1.6:* o fragmento existe.
      *Justificativa:* RF-03. Uma linha, na posição declarada, porque cinco
      worktrees escrevem em paralelo e um `include` no meio do arquivo vira
      conflito de merge que alguém resolve no escuro. A ordem também é leitura:
      a IA fica depois do que o painel sabe sobre o dinheiro, não antes.

- [ ] **1.8 — Modificar `app/routers/settings.py`: as duas rotas de gravação e a
      chave de contexto.**
      Só se **acrescenta**; nenhuma função existente é reescrita e `_context`
      não é tocado. Um import — `from app.advisor import config as advisor_config`.
      Três constantes, junto de `PAYEE` e `CNPJ` (linhas 22-23) e de `FORGOTTEN`
      (linha 34):
      ```python
      IA = f"{SCREEN}/ia"
      IA_FORGET = f"{IA}/esquecer"
      KEY_FORGOTTEN = "Chave apagada."
      ```
      Três linhas no fim de `_answer`, depois de `context.update(...)`
      (linha 165) e antes do `return`:
      ```python
      context["ia"] = advisor_config.view(conn)
      context["ia_action"] = IA
      context["ia_forget_action"] = IA_FORGET
      ```
      Duas funções **depois** de `look_up_cnpj` (linha 113), na forma de
      `store_value`:
      ```python
      @router.post(IA)
      def store_ia(request: Request,
                   chave: Annotated[str, Form()] = "",
                   modelo: Annotated[str, Form()] = "") -> Response:
          conn = connect()
          try:
              try:
                  advisor_config.save(conn, api_key=_text(chave), model=_text(modelo))
              except advisor_config.UnknownModelError as refusal:
                  return _answer(request, conn, notice=str(refusal), status_code=400)
              return _answer(request, conn, done=SAVED)
          finally:
              conn.close()

      @router.post(IA_FORGET)
      def forget_ia(request: Request) -> Response:
          conn = connect()
          try:
              advisor_config.forget(conn)
              return _answer(request, conn, done=KEY_FORGOTTEN)
          finally:
              conn.close()
      ```
      *Considerando 1.2* e *1.6:* o leitor e o fragmento existem.
      *Justificativa:* RF-03, RF-04, RF-05, RF-06. As rotas moram aqui porque
      `_answer` é o único lugar do projeto que sabe montar `configuracao.html`, e
      é isso que faz a recusa sair com `400` **e a tela inteira de pé**, como
      `store_value`, `name_payee` e `look_up_cnpj` já fazem desde o item `015`;
      redirecionar daqui a pouco seria a única tela do painel a responder
      diferente justamente quando o dono errou. Os dois campos passam por `_text`
      porque é o que todo campo de formulário deste router faz
      (`app/routers/settings.py:145-153`), e uma exceção sem motivo é a próxima
      pergunta de alguém. As três linhas ficam em `_answer` e não em `_context`
      porque `_context` é onde os itens simultâneos vão acrescentar chave, e este
      item não pode virar dono de um arquivo que outros cinco também tocam.

- [ ] **1.9 — Modificar `app/templates/consultor.html`: a tela aponta onde se
      resolve.**
      As linhas 60-63 passam a: `Sem chave da IA a leitura não roda. Informe a
      chave em <a href="/configuracao#ia">/configuracao</a> — os números abaixo
      continuam iguais: eles não dependem dela.` A menção a `GEMINI_API_KEY`
      sai.
      *Considerando 1.5:* `has_key` continua vindo do contexto, agora pelo
      leitor.
      *Justificativa:* RF-02, RF-03. É a frase que o brief nomeia no Problema:
      a tela nomeava um problema que ela mesma não deixava resolver. O link é
      escrito à mão como `app/templates/consultor.html:35-36` já faz com
      `/dividas` e `/simulador`.

- [ ] **1.10 — Criar `tests/test_advisor_config.py` e
      `tests/test_configuracao_ia_screen.py`, e ajustar `tests/test_advisor.py`
      e `tests/test_consultor_screen.py`.**
      `tests/test_advisor_config.py`: a precedência nos três estados, os quatro
      últimos caracteres, a chave de oito caracteres que não mostra nenhum, o
      modelo fora da lista levantando `UnknownModelError` sem escrever, e
      `forget` devolvendo a vez ao ambiente sem mexer no modelo — tudo sobre
      `taxonomy_conn` (banco temporário) e `monkeypatch.setenv`.
      `tests/test_configuracao_ia_screen.py`: a seção na tela, a gravação que
      vale na chamada seguinte, o campo vazio que não apaga, o ato de apagar, o
      modelo recusado com `400` e a tela de pé, o teste do segredo — este com
      `caplog`, `capsys` e o dublê de `401` — e o teste do cabeçalho, cujo dublê
      guarda `url`, `params`, `headers` e `json` da chamada. O dublê de
      `httpx.post` é instalado por `monkeypatch.setattr` dentro de cada teste,
      como `tests/test_advisor.py:129` já faz, porque `tests/conftest.py:76-87`
      já trocou a função por uma recusa e o teste não pode sair para a rede.
      Em `tests/test_advisor.py`, as seis chamadas de `ask` (linhas 87, 100, 116,
      130, 214 e 227) ganham `model="gemini-2.5-flash"`, e a asserção da linha 89
      passa de `GEMINI_API_KEY` para `/configuracao`.
      `tests/test_consultor_screen.py` ganha o teste da tela sem chave nenhuma,
      que aponta `/configuracao` e não diz `GEMINI_API_KEY`.
      Quem executa os quatro arquivos é `pytest`, que o CI já roda; nenhum
      portão novo entra em `scripts/gates/` e `gates_runner.sh` não é tocado.
      *Considerando 1.1 a 1.9.*
      *Justificativa:* RF-01 a RF-08. As cadeias de teste são
      `chave-da-tela-0123456789ABCDEF` e `chave-do-ambiente-MB9Z`, e **nenhuma
      começa por `AIza`** — o prefixo real de uma chave do Google faria um
      varredor de segredo acusar o diff de um teste que existe justamente para
      provar que segredo não vaza. As duas se distinguem pelos quatro últimos
      caracteres (`CDEF` e `MB9Z`), que é o que torna a asserção de origem
      discriminante: com dois valores terminados igual, a tela passaria mostrando
      a chave errada. A asserção do segredo cobre resposta, `caplog` e `capsys`
      porque RF-07 fala dos três lugares, e a que só olha o corpo da resposta
      deixa passar exatamente o caminho que o brief teme — o traceback do erro do
      provedor. O teste do cabeçalho olha a URL pedida além do cabeçalho porque
      um dublê que só confirma o cabeçalho passaria igual se a chave continuasse
      indo **também** na query string.

---

## Execução sugerida

Uma fase, uma branch, integrada em `develop`. Dentro dela a ordem é de
dependência real: **1.1 → 1.2** (a tabela antes do leitor), **1.2 → 1.3, 1.5,
1.6, 1.8** (todos consomem o leitor), **1.3 → 1.4** (mesma chamada de
`httpx.post`, e 1.3 já a reescreve), **1.6 → 1.8** (o fragmento define os nomes
de contexto que a rota alimenta), **1.6 → 1.7** (o fragmento antes do
`include`), e **1.10 por último**, porque antes de 1.8 e 1.7 os testes novos
nascem vermelhos. 1.9 pode andar em qualquer ponto depois de 1.5.

O item **não** disputa arquivo com as cinco worktrees simultâneas:
`app/config.py` e `app/main.py` não são tocados; `app/templates/configuracao.html`
recebe uma linha; a migração é `015` e nenhum outro número.
`app/routers/settings.py` é o único arquivo compartilhado com peso: recebe um
import, três constantes no bloco do topo, três linhas no fim de `_answer` e duas
funções no fim da sequência de rotas — nenhuma função existente é reescrita, e
`_context`, que é onde os itens vizinhos vão acrescentar chave de contexto, não
é tocado. O resto — `app/advisor/**`, `app/routers/advisor.py`,
`app/templates/consultor.html`, o fragmento novo e os testes — é território deste
item. `app/taxonomy/`, `app/queries/`, `app/debts/`, `app/cards/`,
`app/financings/`, `app/routers/spending.py` e `app/routers/reference.py` não são
tocados.

## Pendências que viram item de roadmap

- **`docs/plano.md:87` diz que o modelo é `gemini-flash-latest`**, enquanto o
  código usa `gemini-2.5-flash` desde o item `009`. A linha está errada desde
  antes deste item, `docs/` está fora do escopo declarado, e corrigi-la aqui
  seria reconciliação de documento que não é deste PR.

## Validações de campo pendentes

- **Os três modelos declarados respondem de verdade.** `MODELS` é lista de
  código, e a suíte não pode sair para a rede (`tests/conftest.py:76-87`): o
  dublê aceita qualquer nome. Que `gemini-2.5-flash`, `gemini-2.5-pro` e
  `gemini-2.5-flash-lite` existam na conta do dono, com a chave real, só se
  observa com uma chamada real ao provedor. Item de origem:
  `027-configuracao-do-gemini`. O que fica sem verificação: cada um dos três
  nomes responder `200` com uma leitura, escolhido na tela.
- **O provedor aceita a chave no cabeçalho `x-goog-api-key`.** O dublê prova que
  este produto **envia** a chave no cabeçalho e não na URL, que é o que RF-07
  cobra; que o Google **aceite** essa forma só a primeira chamada real mostra, e
  se não aceitasse a leitura da IA responderia `401` com a chave certa. Item de
  origem: `027-configuracao-do-gemini`. O que fica sem verificação: uma pergunta
  em `/consultor`, com a chave real gravada na tela, voltar com texto em vez de
  `a chave foi recusada pelo provedor`.
- **A chave real do dono continua valendo depois da migração.** A migração `015`
  cria tabela nova e não escreve nada, então o `GEMINI_API_KEY` do `.env` do dono
  continua sendo a origem em vigor até ele gravar na tela — o que é o
  comportamento medido pelos critérios sobre banco temporário. O que só a máquina
  do dono prova é que o boot aplica `015` sobre a base real sem erro. Item de
  origem: `027-configuracao-do-gemini`.
