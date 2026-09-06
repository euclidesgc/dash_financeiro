Você está em **dash_financeiro — painel financeiro pessoal de um usuário, rodando local. Login, dashboard das movimentações bancárias (sincronizadas da Pluggy todo dia ou sob demanda) e IA que ajuda a alcançar o plano de curto, médio e longo prazo. Stack Python 3.12 + FastAPI + Jinja2 + HTMX + SQLite. O objetivo do produto é sair de um déficit de R$ 4.940,72/mês.**, sessão nova e sem histórico. Este texto é a sua
única entrada. Leia-o inteiro antes de agir.

## O estado desta corrida — reescrito em 06/09/2026

| | |
|---|---|
| `001-base-e-login` | **concluído**. Quatro fases aprovadas por validador cego, integradas em `develop`. |
| `002-gastos-tres-eixos` | **concluído**. Quatro fases aprovadas e integradas. A fase 3 reprovou duas vezes, escalou, e o dono decidiu: critério `RF-33` reescrito e o canvas que segurava a largura corrigido. A fase 4 reprovou uma vez, por capturas com nome errado. |
| `003-comprometido` | **concluído**. Três fases aprovadas e integradas. A fase 1 reprovou duas vezes e escalou — dois critérios eram insatisfazíveis por aritmética, não por implementação. |
| `011-serie-duplicada-e-tolerancia-do-vencimento` | **próximo da fila**, e ele passa na frente do `004` de propósito. |
| `004` a `009` | não iniciados. |
| `010-lint-e-formatador-python` | dívida técnica: não há portão de lint para Python, e quatro validadores registraram a ausência. |

O produto hoje: login protegido, os 1.942 lançamentos classificados nos três
eixos, a tela de **Gastos** (cinco eixos, período livre, evolução de treze
meses, drill-down, os dois cruzamentos, resíduo visível), a tela de **Regras**,
onde a classificação se edita sem deploy e a base reclassifica na hora, e a tela
de **Comprometido** — assinaturas com valor médio e meses seguidos, parcelamentos
vivos com data de término e caixa liberado, a ação "não uso mais" reversível, e o
**calendário dos próximos 45 dias** com o que sai em cada dia.

O achado central do `003`, para não ser redescoberto: a conta ingênua diz que
**32** parcelamentos ainda devem parcela. Com a janela de vida — a última parcela
vista precisa ter caído no mês corrente ou no anterior — sobram **6**. As 26
séries mortas inflavam o mês com dinheiro que nunca sairia da conta.

**Três coisas esperam o dono, e nenhuma trava a fila:**

1. **Ratificar `D-001`** com `state.py diverge-set --item 001-base-e-login --id
   D-001 --status APROVADA --por humano`. É a única linha de `esperando_humano`.
2. **Revisar a classificação das 77 categorias** na tela de Regras. O seed é
   conservador de propósito — **nenhuma regra nasce `supérfluo`** —, porque o que
   é supérfluo na casa dele não é decisão de quem escreve o código. Por isso a
   lista de corte nasce vazia, e a tela mostra as cinco candidatas de
   `variável × importante` em vez de um painel em branco.
3. **Marcar na tela de Comprometido as assinaturas que ele não usa mais.** As
   três que o relatório de origem trata como canceláveis somam **R$ 1.099,63/mês**
   — `ANTHROPIC* CLAUDE` R$ 581,68, `Pagamento de boleto MYCON` R$ 408,95 e
   TotalPass R$ 109,00 —, mas o painel não marca nenhuma sozinho: escola,
   condomínio e financiamento também são recorrentes e não se cortam com um
   clique. Por isso a economia projetada nasce em `R$ 0,00`.

Apontamentos de validador registrados nas entregas, que merecem decisão dele: a
**interatividade depende de CDN** (htmx e Chart.js; sem rede a tela degrada para
navegação inteira, não quebra), e a **régua visual se moveu junto com a tela que
ela mede** — o parágrafo sobre cor semântica entrou no mesmo commit da tela de
Gastos.

## O que já está no disco e não se reconstrói

`data/` é real, grande e **fora do controle de versão** — e assim continua:

| Caminho | O que é |
|---|---|
| `data/processed/transacoes.{csv,json}` | os 1.942 lançamentos de seis meses, já extraídos da Pluggy |
| `data/processed/recorrentes.json` · `parcelamentos.json` | insumo direto do item `003` |
| `data/manual/` | contratos de financiamento |
| `data/relatorio_origem.md` | o relatório que originou os números congelados |

E agora existe código do produto, com **308 testes verdes**:

- `app/config.py`, `app/db.py`, `app/migrate.py`, `app/query.py` — base, com três
  migrações aplicadas.
- `app/ingest/**` — a carga: `python -m app.ingest` lê a fonte, grava em centavos
  inteiros com o sinal normalizado e **já roda o seed da taxonomia e a
  classificação no mesmo processo**.
- `app/auth/**` — Argon2id, cookie assinado de 12 h, guarda em **toda** rota
  registrada, rate-limit de 5 tentativas / 15 min persistido, logout que
  sobrevive ao reinício.
- `app/taxonomy/**` — os dez grupos, as três naturezas, as três essencialidades,
  os dois cruzamentos e 80 regras, tudo semeado de `app/taxonomy/seed.json`.
- `app/queries/**` — agregação pelos cinco eixos, cruzamentos, série de treze
  meses, drill-down, e a constante única do filtro de gasto.
- `app/commitments/**` — o motor de compromissos: `series.py` monta a série,
  `live.py` aplica a janela de vida de um mês, `schedule.py` prevê o dia pela
  mediana, `engine.py` recompõe tudo numa transação só, `mark.py` guarda o "não
  uso mais" e `calendar.py` recorta os **45 dias** que o item `004` vai consumir.
- `app/templates/**`, `app/static/css/**` — as telas de login, Gastos, Regras e
  Comprometido.

**`DASH_TODAY` existe e importa.** Sem ela, `recompute` segue o relógio da
máquina e o mesmo comando produz um conjunto vivo diferente amanhã. Toda medição
contra a base congelada usa `DASH_TODAY=2026-09-05`.

**Código Python já exercitado contra a API real da Pluggy** — reaproveite, não
reescreva: `ingestao/pluggy_extract.py`, `ingestao/pluggy_consolidate.py`,
`financas/financiamento_sac.py`, `financas/cdc_veiculo.py`.

## Por que `011` vem antes de `004`

O `004-resumo-e-projecao` projeta saldo dia a dia por 45 dias somando exatamente
os compromissos datados que o `003` produz. O validador da fase 3 mediu dois
defeitos nesse insumo, e projetar por cima deles é construir a tela principal
sobre número errado:

1. **Série que é recorrente e parcelada ao mesmo tempo sobrevive ao fim das
   parcelas.** `jim com` fechou na parcela 06/06 em 08/09/2026 e não deve mais
   nada, mas o motor mantém **também** uma linha `recurring` com a média das
   mesmas cinco cobranças. O calendário prevê −R$ 136,44 em 06/10/2026 para uma
   dívida que acabou. O invariante do `001` já diz qual das duas manda:
   parcelamento tem fim, recorrência não, e cada lançamento entra uma vez só.
2. **A previsão é apagada pelo mês inteiro, não pelo vencimento.**
   `app/commitments/calendar.py` casa lançamento com previsão por
   `(série, AAAA-MM)`. Uma cobrança avulsa no dia 5 esconderia o vencimento do
   dia 25 da mesma série. Hoje o dano é zero — um único lançamento casou na
   janela, a dois dias do previsto — e a chave por mês existe porque a mediana
   erra o dia. A correção é **tolerância em dias**, não a volta à comparação
   exata, que reabriria o problema do `jim com`.

Note que o número congelado `−R$ 12.802,64` **já inclui** a série duplicada.
Corrigi-la muda o total comprometido, e o `docs/plano.md` precisa ser reconciliado
junto — no mesmo PR da mudança, como manda a norma 8.

## Fonte de verdade, nesta ordem

`product/roadmap.md` (a fila, ordenada por dependência), `CLAUDE.md` (a norma),
**`product/00-linguagem-visual.md`** — que agora existe e é canônico: toda tela
sai dele, e nenhuma escolhe cor, tipografia, espaçamento, raio ou movimento fora
dele — e os documentos aprovados do item ativo em `product/items/<id>/`.

## O processo

Plugin **generic-harness**. **Leia o estado antes de qualquer outra coisa:**

```bash
python3 "$CLAUDE_PLUGIN_ROOT/scripts/state/state.py" read
node scripts/loop/decide-next-action.mjs
```

Se `CLAUDE_PLUGIN_ROOT` vier vazio, ele está em
`.harness/runtime/plugin-root.json`. A segunda linha diz o que **esta** sessão
faz, e é a única coisa que ela faz. Conduza pelo `/harness:start`, carregando a
skill `harness-orchestrator`. Não pule estágio.

## Credencial, e três armadilhas medidas nesta máquina

O `.env` (modo 600, gitignorado) traz `LOGIN` e **`PASSORD`** — o typo é do
dono, preservado de propósito, assim como **`GEMIMI_API_KEY`**. O código já
aceita as duas grafias de cada um.

**Armadilha 1 — o hook de permissão nega qualquer comando que leia `.env`.** Não
contorne. Todo comando que carrega configuração precisa de `DASH_ENV_FILE=/dev/null`
mais as variáveis declaradas na própria linha; sem isso o processo tenta ler o
`.env` do dono e o comando é negado. Bancos e chaves sempre em `/tmp`
(`DASH_DB_PATH=/tmp/…`, `DASH_KEY_PATH=/tmp/…`), nunca contra `data/`.

**Armadilha 2 — `rtk` reescreve a saída de comando por hook global.** Quando a
evidência de um critério precisar da saída bruta, use `rtk proxy <comando>`. No
zsh, `grep --include=*.html` precisa das aspas: `"--include=*.html"`. E **todo
critério que usa `grep -R` precisa de `--exclude-dir=__pycache__`**: o grep casa
bytes de `.pyc` por coincidência e o critério passa a medir o estado do cache do
interpretador em vez do código — já aconteceu, está proposto como lint na
`.harness/proposals/2026-09-06-005.md`.

**Armadilha 3 — o rate-limit do login fecha a porta durante a validação.** Cinco
senhas erradas do mesmo IP em quinze minutos e a sexta responde 429, mesmo com a
senha certa. Faça **um** login e reuse o cookie. Para reabrir:
`.venv/bin/python -c "import sqlite3; c=sqlite3.connect('<banco>'); c.execute('delete from login_attempts'); c.commit()"`.

**Não há MCP de navegador para os agents.** Há um Chromium em
`~/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome` e um Playwright no
cache do npx; dois validadores já os usaram para medir viewport, foco, tema
escuro e movimento reduzido. A thread principal tem o MCP do Playwright.

## Autonomia — não há humano acordado

O dono autorizou esta corrida. **Não pergunte nada a ninguém.**

1. **Decida** você, com os documentos aprovados e o `CLAUDE.md` como régua.
   Prefira a convenção mais comum e mais reversível.
2. **Aprove** com `state.py approve --stage <e> --file <caminho> --por autonomo`.
3. **Registre** em `product/items/<id>/decisoes-autonomas.md`, a cada decisão,
   não no fim.
4. **Divergência `normal`**: ratifique na opção recomendada com
   `diverge-set --status APROVADA --por autonomo`, reconcilie e siga; o trabalho
   nasce e permanece `blocked-on-D-nnn` até um humano ratificar. **Divergência
   `contrato`**: registre e **pare**.
   *Uma lição da primeira noite:* divergência é para quando existem **opções com
   impactos diferentes**. Erro material com uma única correção possível — um
   documento que se contradiz sozinho, uma lista que omite o que outro requisito
   manda incluir — é reconciliação direta, registrada em `decisoes-autonomas.md`.
   Abrir divergência para isso promove o item para a trilha completa e não
   entrega decisão nenhuma ao dono.
5. **Duas reprovações seguidas escalam sozinhas.** Não tente a terceira: escreva
   os três diagnósticos possíveis em `decisoes-autonomas.md` e pare. Foi o que
   aconteceu com a fase 3 do `002`, e a regra funcionou.

## Quando o item mexe em interface

**`product/00-linguagem-visual.md` é canônico.** Toda sessão que escreve
interface o lê antes de abrir editor. Mudar o que está lá é reconciliação de
documento canônico — no presente, sem cicatriz.

O conceito, para não ser redecidido: **um instrumento de leitura, não um app de
banco**. A unidade do produto é tempo — dias até o objetivo —, e a forma é a de
um instrumento graduado. A cifra é a protagonista, e por isso a face
monoespaçada é a principal. A escala graduada é o único ornamento, e aparece só
onde existe distância a percorrer. O painel sustenta por baixo: sem confete, sem
streak, e sem alarme decorativo.

**Antes de decidir direção visual, carregue a skill `frontend-design`.**

**A régua, que não se negocia:**

| O quê | Como se prova |
|---|---|
| Contraste AA nos dois temas | a tabela de pares do documento canônico, medida por `tests/test_contrast.py` |
| Foco visível em tudo que recebe foco | percorrer a tela inteira só com `Tab` |
| Responsivo do telefone ao monitor largo | 375, 768 e 1440 sem rolagem horizontal do corpo — **carregando na largura e também redimensionando a janela**, que são medidas diferentes e uma passa enquanto a outra falha |
| `prefers-reduced-motion` respeitado | a animação some, o estado final permanece |
| Nenhum valor mágico | a cor e o espaço vêm do token, e o portão mede |
| Estado vazio e de erro acionáveis | dizem o que aconteceu e qual é o próximo ato |

**Você não dá interface por pronta sem ter olhado para ela.** Suba o app,
navegue, **tire a captura**, e olhe. Uma tela que passa no teste e está feia
passou no teste errado. Guarde em `product/items/<id>/06-capturas/`, nomeadas
**exatamente como o critério as nomeia** — três capturas com nome diferente do
exigido reprovaram uma fase nesta corrida.

## Entrega — este repositório NÃO tem remote

Medido em 06/09/2026: `git remote -v` sai vazio, e existem `main` e `develop`.
**Enquanto for assim, isto substitui a seção seguinte:**

- Uma fase é a unidade de entrega, mas **não vira PR**. Trabalhe em
  `<nnn-slug>/fase-<n>-<slug>` e integre em `develop` com `git merge --no-ff`
  **depois** do veredicto APROVADO do validador cego e do
  `bash scripts/gates/gates_runner.sh` verde. Fase reprovada **não** se integra.
- **O corpo do PR vira arquivo**, em `product/items/<id>/05-entregas/fase-<n>.md`,
  com as sete seções da skill `pr-authoring` e a evidência de cada critério. É o
  que o dono lê de manhã.
- `scripts/merge-se-liberado.sh`, `gh stack` e o fluxo `harness.yml` **não medem
  nada sem remote** — não os chame. O portão desta corrida é o validador cego
  mais o `gates_runner.sh` local.
- **Nunca `main`.** A integração é `develop`.

Se um remote passar a existir, a seção abaixo volta a valer inteira.

## Entrega

Uma fase é um PR, na pilha (`gh stack add`, `gh stack submit`). Nunca `--force`.
Corpo de PR pela skill `pr-authoring`, com as sete seções; pendência que sobrou
vira item de roadmap **antes** de a fase fechar.

A posição é informação, e ela ordena **dentro do bloco a que o item pertence**.
Pendência de processo — portão, fluxo de CI, veredicto, varredura — vai para o
bloco de dívida técnica, ordenada ali; ela não é dependência de item de produto
nenhum.

**Merge: só pelo `scripts/merge-se-liberado.sh`, e só o PR do fundo da pilha.**
Nunca por `gh pr merge`, nunca pelo botão. Ele mergeia na branch de
**integração**, nunca na de produção.

O que **não** se faz, em nenhuma hipótese: tirar rótulo de bloqueio para
destravar, mergear PR do meio da pilha, e mergear na branch de produção.

## Antes de encerrar

Rode `state.py check` e a skill `session-retrospective`. As cinco propostas ao harness estão
em `.harness/proposals/` — leia antes de escrever a quarta,
para não repetir o que já está proposto. Deixe a árvore limpa e commitada; o
motor trata árvore suja como rodada que morreu.
