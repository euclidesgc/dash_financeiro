Você está em **dash_financeiro — painel financeiro pessoal de um usuário, rodando local. Login, dashboard das movimentações bancárias (sincronizadas da Pluggy todo dia ou sob demanda) e IA que ajuda a alcançar o plano de curto, médio e longo prazo. Stack Python 3.12 + FastAPI + Jinja2 + HTMX + SQLite. O objetivo do produto é sair de um déficit de R$ 4.940,72/mês.**, sessão nova e sem histórico. Este texto é a sua
única entrada. Leia-o inteiro antes de agir.

## O estado desta corrida — escrito em 05/09/2026, 21h

O dono aprovou o roadmap e autorizou a corrida. Ele dorme; ninguém responde
pergunta até de manhã.

**A corrida começa do zero de processo**: `product/state.json` tem
`active_item: null` e `product/items/` ainda não existe. A primeira ação é abrir
o `001-base-e-login`. Não há fase pela metade para retomar.

**O que já está no disco e não se reconstrói.** `data/` é real, grande e **fora
do controle de versão** — e assim continua:

| Caminho | O que é |
|---|---|
| `data/processed/transacoes.{csv,json}` | os 1.942 lançamentos de seis meses, já extraídos da Pluggy |
| `data/processed/recorrentes.json` · `parcelamentos.json` | insumo direto do item `003` |
| `data/manual/` | contratos de financiamento |
| `data/relatorio_origem.md` | o relatório que originou os números congelados |

**Código Python já exercitado contra a API real da Pluggy** — reaproveite, não
reescreva: `ingestao/pluggy_extract.py`, `ingestao/pluggy_consolidate.py`,
`financas/financiamento_sac.py`, `financas/cdc_veiculo.py`. São 860 linhas que já
rodaram; refazê-las é gastar a noite reconstruindo o que funciona.

**A ordem da noite, e o porquê dela.** `001` → `002` → `003` → `004` é um bloco
autossuficiente: lê o que já está no disco e **não depende de credencial de
terceiro nenhuma**. Ele termina na tela que impede de entrar no cheque especial a
3,52% a.m., que é onde este produto ganha o real marginal. Só então `005`, `007`
e `008`. `006` e `009` ficam por último porque dependem de terceiro.

**Trilha por item, decidida pelo dono:** rápida (brief → plano com critérios
tipados → validador cego → entrega) em `001`–`005`, `007` e `008`; **completa**,
com spec escrita, em `006` e `009`. A régua não é tamanho, é modo de falha: item
interno erra alto e a prova é local e barata; sync e IA erram **em silêncio** —
dado velho com cara de fresco, número citado errado —, e é ali que a spec paga o
próprio custo.

**Nada trava por falta de credencial.** `006` se constrói contra fixture gravada
e `009` contra resposta gravada do Gemini; a chamada real vira linha em
"Validações de campo pendentes" do roadmap. Parar a corrida para esperar um
humano acordar é exatamente o desperdício que o modo autônomo existe para evitar.

**As três pendências humanas não bloqueiam** — saldo de quitação do CDC do
Duster, custo de transporte sem o carro, taxa dos cartões. Até o `008` o motor usa
**premissa declarada na tela**; a partir do `008` elas viram mecanismo do produto.

**Os números de referência estão congelados em `docs/plano.md`, medidos em
05/09/2026.** Nenhum critério compara contra relatório regenerável: em um mês ele
passaria por construção, medindo nada.

**`product/00-linguagem-visual.md` ainda não existe.** Quem o escreve é o `001`,
antes da primeira tela — e a partir daí ele é canônico, como manda a seção sobre
interface mais abaixo.

## Credencial inicial, e duas armadilhas medidas nesta máquina

O `.env` (modo 600, gitignorado) traz o login que semeia o usuário do painel:
`LOGIN` e **`PASSORD`** — o typo é do dono, preservado de propósito, assim como
**`GEMIMI_API_KEY`**. **Aceite as duas grafias de cada um**
(`PASSORD`/`PASSWORD`, `GEMIMI_API_KEY`/`GEMINI_API_KEY`) em vez de exigir que o
arquivo seja corrigido.

O seed do `001` lê do ambiente, grava **hash Argon2** e é idempotente. A senha
nunca vai para o banco em claro, nem para log, nem para HTML.

**Armadilha 1 — o hook de permissão nega qualquer comando que leia `.env`.**
Medido: `grep -oE '^[A-Z_]+=' .env` foi **negado**. Não contorne e não insista. O
código que você escreve lê por `os.environ`; o `.env.example` documenta os nomes.
Critério que precise provar que a variável existe prova **pelo comportamento** —
o app sobe, o login funciona —, nunca lendo o arquivo.

**Armadilha 2 — `rtk` reescreve a saída de comando por hook global.** Quando a
evidência de um critério precisar da saída bruta e íntegra, use
`rtk proxy <comando>`.

## Fonte de verdade, nesta ordem

`product/roadmap.md` (a fila, ordenada por dependência), `CLAUDE.md` (a
norma), `product/00-linguagem-visual.md` quando o item mexe em interface — ver a
seção sobre isso — e os documentos aprovados do item ativo em
`product/items/<id>/`.

## O processo

Plugin **generic-harness**. **Leia o estado antes de qualquer outra coisa:**

```bash
python3 "$CLAUDE_PLUGIN_ROOT/scripts/state/state.py" read
node scripts/loop/decide-next-action.mjs
```

O motor preparou o canal que leva `CLAUDE_PLUGIN_ROOT` ao shell. Se ainda assim
o caminho vier vazio — sessão aberta à mão, sem o motor —, ele está em
`.harness/runtime/plugin-root.json`; leia de lá e use o caminho absoluto, em vez
de procurar o script.

A segunda linha diz o que **esta** sessão faz — um estágio, uma fase, um
reparo de critério, o fechamento de um item, ou a abertura do próximo — e é a
única coisa que ela faz. Conduza pelo `/harness:start`, carregando a skill
`harness-orchestrator`. Não pule estágio; `state.py` recusa salto e a recusa é
o portão funcionando.

## Autonomia — não há humano acordado

O dono autorizou esta corrida. **Não pergunte nada a ninguém.** Onde o fluxo
pediria decisão ou aprovação humana:

1. **Decida** você, com os documentos aprovados e o `CLAUDE.md` como régua.
   Prefira sempre a convenção mais comum e mais reversível.
2. **Aprove** com `state.py approve --stage <e> --file <caminho> --por autonomo`.
   Sempre com `--file` — sem ele a aprovação não amarra a um conteúdo — e
   sempre com `--por autonomo`: é o que separa, de manhã, o que gente decidiu
   do que a máquina decidiu sozinha.
3. **Registre** em `product/items/<id>/decisoes-autonomas.md`, a partir de
   `$HARNESS_PLUGIN_ROOT/skills/autonomous-run/templates/decisoes-autonomas.md`:
   uma linha por decisão, com a alternativa descartada e o porquê, e uma linha
   por aprovação autônoma. É o que o dono lê de manhã. Atualize a cada decisão,
   não no fim.
4. **Divergência `normal`**: ratifique na opção recomendada com
   `diverge-set --status APROVADA --por autonomo`, reconcilie e siga. O PR
   nasce e permanece `blocked-on-D-nnn` até um humano ratificar — é assim que
   deve ser. **Divergência `contrato`**: registre e **pare**; a decisão é do
   dono, porque a premissa errada se espalha para quem consome o contrato.
5. **Duas reprovações seguidas** escalam sozinhas. Não tente a terceira:
   escreva os três diagnósticos possíveis em `decisoes-autonomas.md` e pare.

## Quando o item mexe em interface

Uma sessão nasce limpa e não viu o que a anterior desenhou. Sem uma fonte
escrita, a segunda tela escolhe outra paleta que a terceira contradiz, e de
manhã existem três produtos dentro do mesmo repositório. Por isso:

**`product/00-linguagem-visual.md` é canônico, como o PRD de produto.** Toda
sessão que escreve interface o lê antes de abrir editor, e nenhuma escolhe cor,
tipografia, espaçamento, raio ou movimento fora dele. Ele nasce no item que
monta o sistema de design; a partir daí, mudar o que está lá é reconciliação de
documento canônico — no presente, sem cicatriz — e não uma segunda opinião ao
lado.

**Antes de decidir direção visual, carregue a skill `frontend-design`.** Ela
existe para o problema que é exatamente o desta corrida: escolha de madrugada,
sem ninguém para reagir, tende ao gabarito. Três looks denunciam design gerado
por máquina, e a skill os nomeia — creme com serifa de alto contraste e acento
terracota; quase-preto com um acento verde-ácido; jornal com fios de cabelo e
raio zero. Se a paleta chegou num deles, ela não foi escolhida.

**A régua, que não se negocia:**

| O quê | Como se prova |
|---|---|
| Contraste AA nos dois temas | varredura de acessibilidade sem violação crítica nem séria |
| Foco visível em tudo que recebe foco | percorrer a tela inteira só com `Tab` |
| Responsivo do telefone ao monitor largo | 375, 768 e 1440 sem rolagem horizontal do corpo |
| `prefers-reduced-motion` respeitado | a animação some, o estado final permanece |
| Nenhum valor mágico | a cor e o espaço vêm do token, e o portão mede |
| Estado vazio e de erro acionáveis | dizem o que aconteceu e qual é o próximo ato |

**Você não dá interface por pronta sem ter olhado para ela.** Critério
`comportamental` de tela roda no navegador de verdade: suba o app, navegue,
**tire a captura**, e olhe. Uma tela que passa no teste e está feia passou no
teste errado — a captura é o que separa "os elementos existem" de "a página
está boa". Guarde em `product/items/<id>/06-capturas/`, nomeadas pelo estado que
mostram: são a evidência do critério e o que o dono vê de manhã sem subir nada.

## Entrega — este repositório NÃO tem remote

Medido em 05/09/2026: `git remote -v` sai vazio, e existem apenas `main` e
`develop`. **Enquanto for assim, isto substitui a seção seguinte:**

- Uma fase continua sendo a unidade de entrega, mas **não vira PR**. Trabalhe em
  `fase/<item>-<n>` e integre em `develop` com `git merge --no-ff` **depois** do
  veredicto APROVADO do validador cego e do `bash scripts/gates/gates_runner.sh`
  verde.
- **O corpo do PR não deixa de existir — ele vira arquivo.** Escreva-o em
  `product/items/<id>/05-entregas/fase-<n>.md`, com as mesmas seções da skill
  `pr-authoring` e a evidência de cada critério. É o que o dono lê de manhã, e sem
  ele a fase não fecha.
- `scripts/merge-se-liberado.sh`, `gh stack` e o fluxo `harness.yml` **não medem
  nada sem remote** — não os chame e não conte com eles. O portão desta corrida é
  o validador cego mais o `gates_runner.sh` local.
- **Nunca `main`.** A integração é `develop`; subir para produção segue sendo
  decisão do dono.

Se um remote passar a existir, a seção abaixo volta a valer inteira.

## Entrega

Uma fase é um PR, na pilha (`gh stack add`, `gh stack submit`). Nunca `--force`.
Corpo de PR pela skill `pr-authoring`, com as sete seções; pendência que sobrou
vira item de roadmap **antes** de a fase fechar.

A posição é informação, e ela ordena **dentro do bloco a que o item pertence**.
Pendência de processo — portão, fluxo de CI, veredicto, varredura — vai para o
bloco de dívida técnica, ordenada ali; ela não é dependência de item de produto
nenhum. Promovê-la ao topo é a régua local certa e o agregado errado: numa noite,
seis pendências de CI nascidas de fases diferentes, cada uma inserida
corretamente por uma sessão que não via as outras, reconstituíram a fila de
infraestrutura inteira na frente do produto priorizado. Ninguém errou uma vez —
o erro foi acertar seis vezes.

**Merge: só pelo `scripts/merge-se-liberado.sh`, e só o PR do fundo da pilha.**
Nunca por `gh pr merge`, nunca pelo botão. O script é a tranca — mede rótulo de
bloqueio, verificação vermelha, verificação **pendente** e a situação de cada PR
abaixo, com teto de tempo em toda chamada de rede, e recusa o que não conseguiu
medir.

Ele mergeia na branch de **integração**, nunca na de produção. É o que torna o
merge autônomo aceitável: o que entra ali passou pelo validador cego, pelos
portões e pelo CI, e ainda espera a decisão do dono para subir. E uma pilha que
só cresce vira, de manhã, trinta PRs que ninguém revisa, cada um partindo de uma
base mais distante do que já foi aprovado — que é a forma de a corrida terminar
sem nada aproveitável.

O que **não** se faz, em nenhuma hipótese: tirar rótulo de bloqueio para
destravar, mergear PR do meio da pilha, e mergear na branch de produção.

## Antes de encerrar

Rode `state.py check` e a skill `session-retrospective`: a proposta em
`.harness/proposals/` é o que o harness aprende com esta noite. Deixe a árvore
limpa e commitada; o motor trata árvore suja como rodada que morreu.
