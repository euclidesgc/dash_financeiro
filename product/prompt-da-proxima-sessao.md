Você está em **dash_financeiro — painel financeiro pessoal de um usuário, rodando local. Login, dashboard das movimentações bancárias (sincronizadas da Pluggy todo dia ou sob demanda) e IA que ajuda a alcançar o plano de curto, médio e longo prazo. Stack Python 3.12 + FastAPI + Jinja2 + HTMX + SQLite. O objetivo do produto é sair de um déficit de R$ 4.940,72/mês.**, sessão nova e sem histórico. Este texto é a sua
única entrada. Leia-o inteiro antes de agir.

## O estado desta corrida — reescrito em 06/09/2026, 02h

A primeira noite autônoma rodou e **parou por escalada**, como manda a regra. O
que existe agora:

| | |
|---|---|
| `001-base-e-login` | **concluído**. Quatro fases aprovadas por validador cego, integradas em `develop`. |
| `002-gastos-tres-eixos` | **em execução**, fases 1 e 2 aprovadas e integradas; **fase 3 escalada** depois de duas reprovações seguidas. |
| `003` a `009` | não iniciados. |
| `010-lint-e-formatador-python` | dívida técnica nova no roadmap: não há portão de lint para Python, e três validadores registraram a ausência. |

**A primeira coisa que esta sessão faz é decidir a escalada da fase 3.** O motor
recusa avançar enquanto ela estiver aberta, e está certo: duas reprovações no
mesmo lugar significam que algo a montante está errado. O diagnóstico completo,
com a evidência de cada uma, está em
`product/items/002-gastos-tres-eixos/decisoes-autonomas.md`, seção **"Escalada"**.
Em resumo, são duas coisas independentes:

1. **Defeito real, causa raiz isolada:** o `<canvas>` do gráfico segura a
   largura do container de grid e nunca encolhe, então a tela ganha rolagem
   horizontal quando a **janela é redimensionada** para 375 ou 768 px (carregar
   já estreito passa). O validador confirmou o mecanismo injetando estilo no
   navegador: `.panels, .panel, .chart { min-width: 0 }` mais
   `.chart-canvas { max-width: 100% }` → `375 vs 375 | canvas=325`. É correção
   de três linhas de CSS mais o teste que a trava.
2. **Critério errado:** o `RF-33` exige que os totais dos **dois** cruzamentos
   mudem ao trocar o período, e o `RF-48` exige um banco em que um deles vale
   `R$ 0,00` em todo período. Nenhuma implementação passa. Reescrever a cláusula
   (o total do cruzamento **atribuído** muda, e a soma das candidatas do
   cruzamento vazio também — medido: `−R$ 29.279,70` → `−R$ 23.928,48`) exige
   `exception-open` no plano, `plan-writer`, e reaprovação.

Feito isso, revalide a fase 3 com um **validador novo**, integre, e siga:
fase 4 do `002` (tela de Regras), depois `003`, `004`, `005`, `007`, `008`, e
por último `006` e `009`, que dependem de terceiro.

**O que a fase 4 do `002` precisa saber antes de começar:** um validador mediu
que regra de expressão é compilada **sem** `re.IGNORECASE` e casada contra a
descrição normalizada — minúscula, sem acento e **sem dígito**. Uma regra
gravada como `Uber`, `99app` ou `saúde` é aceita e casa zero lançamentos, em
silêncio. A tela de Regras é o lugar de resolver isso: ela já recebe de
`create_rule` quantos lançamentos a regra alcançou, e precisa dizer isso na hora.

## O que já está no disco e não se reconstrói

`data/` é real, grande e **fora do controle de versão** — e assim continua:

| Caminho | O que é |
|---|---|
| `data/processed/transacoes.{csv,json}` | os 1.942 lançamentos de seis meses, já extraídos da Pluggy |
| `data/processed/recorrentes.json` · `parcelamentos.json` | insumo direto do item `003` |
| `data/manual/` | contratos de financiamento |
| `data/relatorio_origem.md` | o relatório que originou os números congelados |

E agora existe código do produto, com 222 testes verdes:

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
- `app/templates/**`, `app/static/css/**` — a tela de login e a de Gastos.

**Código Python já exercitado contra a API real da Pluggy** — reaproveite, não
reescreva: `ingestao/pluggy_extract.py`, `ingestao/pluggy_consolidate.py`,
`financas/financiamento_sac.py`, `financas/cdc_veiculo.py`.

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
zsh, `grep --include=*.html` precisa das aspas: `"--include=*.html"`.

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

Rode `state.py check` e a skill `session-retrospective`. As três propostas da
primeira noite estão em `.harness/proposals/` — leia antes de escrever a quarta,
para não repetir o que já está proposto. Deixe a árvore limpa e commitada; o
motor trata árvore suja como rodada que morreu.
