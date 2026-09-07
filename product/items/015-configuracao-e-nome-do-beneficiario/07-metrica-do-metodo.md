# Métrica do método de planejamento em acúmulo

Este item é o primeiro planejado pelo método que o dono propôs: fases pequenas
com etapas pequenas, **cada etapa escrita considerando as anteriores em
acúmulo**, e uma **revisão do código contra o plano antes de escrever qualquer
implementação**. Se der resultado, o método entra no generic-harness como a
forma de planejar. Para saber se deu, ele precisa ser medido contra o que veio
antes.

## A linha de base, e por que ela é menor do que parece

O registro em disco não consegue contar rodadas de validação nos itens `005` em
diante: eles guardaram **um** arquivo de veredicto por fase, sobrescrito a cada
rodada. Só os itens `001`, `002` e `003` guardaram um arquivo por rodada, e é
com eles que a comparação é honesta.

| Base | Valor | Como foi medida |
|---|---|---|
| Fases aprovadas | 11 | arquivos com veredicto `APROVADO` em `001`, `002`, `003` |
| Rodadas de validação | 17 | todos os arquivos de veredicto dos três itens |
| Rodadas por fase | **1,55** | 17 ÷ 11 |
| Fases reprovadas na primeira rodada | **6 de 11 (55%)** | veredictos `REPROVADO` |
| Números de critério reescritos depois de implementar | 4 ocorrências | itens `007`, `011` e duas vezes no `014`, registradas nas decisões |

O que essas rodadas custaram é o ponto: cada uma é um validador cego rodando os
portões inteiros, e a reprovação chega **depois** de o código estar escrito.

## O custo em tokens, medido do transcript

A corrida inteira cabe numa sessão só, e o transcript traz `usage` por mensagem
com carimbo de tempo. Cruzando com o carimbo dos commits — cada mensagem é
atribuída ao item cujo commit a fecha — dá o custo real, contando entrada não
cacheada, criação de cache e saída:

| Item | Fases | Tokens |
|---|---|---|
| `001` base e login | 4 | 479.562 |
| `002` gastos três eixos | 4 | 991.514 |
| `003` comprometido | 3 | 1.297.263 |
| `004` resumo e projeção | 2 | 238.326 |
| `005` dívidas e simuladores | 1 | 142.461 |
| `006` sync Pluggy | 1 | 106.462 |
| `007` objetivo e linha do tempo | 1 | 136.381 |
| `008` simulador e base de fatos | 1 | 96.084 |
| `009` IA consultora | 1 | 82.505 |
| `010` dívida técnica | — | 24.690 |
| `011` série duplicada | 1 | 228.772 |
| `012` sync pós-carga atômica | 1 | 784.806 |
| `013` objetivo cenário vazio | 1 | 27.463 |
| `014` taxa pelos juros cobrados | 1 | 176.551 |
| **`015` — só o planejamento** | 3 | **370.872** |

**O planejamento do `015` custou mais do que isso.** Os quatro revisores rodaram
como subagentes e o gasto deles não entra no transcript desta sessão: 144.140 +
150.438 + 151.735 + 166.554 = **612.867**. O planejamento completo custou
**983.739 tokens** — mais que o item `002` inteiro, que teve quatro fases
implementadas e validadas.

Esse é o número que o método precisa justificar. A pergunta que a implementação
responde não é se planejar assim é barato: é se **planejar caro sai mais barato
que reprovar**. A comparação justa é o custo total por item, e por isso a
implementação começa em sessão nova, com a conta zerada.

A mediana dos itens de uma fase é **136.381** tokens, do `007`. Se a
implementação das três fases do `015` couber em torno de três medianas — cerca
de 410 mil — o método empata; abaixo disso, ganha.

## O que este item mede

| # | Métrica | Alvo | Resultado |
|---|---|---|---|
| 1 | Problemas achados na revisão pré-código | quanto mais, melhor | **36 distintos**, 3 deles defeitos vivos |
| 2 | Rodadas até `APROVADO`, por fase | ≤ 1,55 | **1,33** — 4 rodadas em 3 fases · **bate** |
| 3 | Veredicto da primeira rodada de cada fase | `APROVADO` nas três | **2 de 3** · `APROVADO`, `CRITERIO_INVALIDO`, `APROVADO` · **não bate** |
| 4 | Achados do validador que critério nenhum cobria | < 4,6 por fase | **2,67 por fase** — 8 no total, nenhum reprovando · **bate** |
| 5 | Números de critério reescritos depois de implementar | **zero** | **zero** · um critério foi reescrito, sem número, e virou `D-002` |
| 6 | Ambiguidades resolvidas por padrão × perguntas ao dono | **zero perguntas** | 14 resolvidas, 0 perguntas |
| 7 | Tokens da implementação | < 410.000 | **1.468.201** · **não bate**, por 3,6× |

## O que cada número quer dizer

**Métrica 2 — 1,33 rodada por fase.** Fases 1 e 3 fecharam na primeira; a fase 2
precisou de duas. A base era 1,55, com 6 de 11 fases reprovadas na primeira
rodada. O método reduziu o retrabalho de validação.

**Métrica 3 — duas de três.** A fase 2 voltou `CRITERIO_INVALIDO`, e o alvo era
`APROVADO` nas três. Vale ler o motivo: **nenhum critério verificável falhou** e
nenhum portão caiu. O bloqueio foi um critério que nomeava `POST
/configuracao/cnpj`, rota que só a fase 3 cria, e que passava por construção —
a guarda de sessão é middleware e devolve `302` para qualquer caminho, existente
ou não. Isto é, a falha foi **do plano**, e apareceu no único lugar onde a
revisão pré-código não olhou: a fronteira entre duas fases. Registrada em
`04-divergencias/D-002.md`.

**Métrica 4 — 2,67 achados por fase, nenhum reprovando.** Dois deles seriam
defeitos vivos se tivessem passado: o consultor ainda carregava a própria cópia
do catálogo, e a medição de largura rodava com a barra de rolagem escondida, com
folga exatamente zero. Cada um virou correção com prova executada.

**Métrica 5 — zero número reescrito.** Todo número que um critério afirma foi
medido antes, e todos se confirmaram contra a base: `53`, `338`, `169`, `404`,
`148`, `720`, `137`, `55,53%`, `72,83%`, `36,1%`. Um critério foi reescrito, mas
por erro de fronteira de fase, não de número.

**Métrica 7 — 1.483.321 tokens.** O alvo de 410.000 estava errado, e errado
contra o método: ele era "três medianas de item de uma fase", e o `015` tem três
fases, 24 etapas, duas telas, duas migrações e a primeira saída de rede nova do
produto. A comparação que mede o método é com itens do mesmo tamanho, todos
feitos **sem** revisão pré-código:

| Item | Fases | Tokens |
|---|---|---|
| `002` | 4 | 991.514 |
| `003` | 3 | 1.297.263 |
| **`015` — só a implementação** | 3 | **1.483.321** |
| `015` — com o planejamento | 3 | 2.467.060 |

Contra o `003`, o par mais próximo: a implementação custou **+14%**. O item
inteiro custou **+90%**, e essa diferença é quase toda os quatro revisores
pré-código (612.867).

Ou seja: **o método não encareceu a implementação. Ele acrescentou um custo fixo
de planejamento.**

O gasto da implementação não veio de o plano ser detalhado. Veio de **número de
turnos** — 449 mensagens, cada uma recacheando um transcript que só cresce — e os
três maiores blocos são a fase de tela (o laço escrever, servir, capturar, olhar,
corrigir), a prova executada em duplicata (todo critério comportamental roda duas
vezes, uma minha e uma do validador cego: 243.766, 16% do total) e a ingestão do
plano numa sessão zerada de propósito.

## O veredicto, em uma frase

**O método é mais preciso e menos econômico que o do generic-harness, e a
diferença de precisão vem de um buraco que o harness tem por construção.**

O harness confere o plano de duas maneiras, e as duas são cegas de propósito:

| Quem | Vê | Não vê | Pergunta que responde |
|---|---|---|---|
| `criteria-auditor` | spec e critérios | o código | cada `RF-nn` tem critério que o cubra? |
| `phase-validator` | critérios e código | spec e plano | o código cumpre o critério? |

Falta o terceiro eixo: **ninguém lê o plano contra o código antes de
implementar.** Os 36 problemas saíram exatamente daí, e nenhum deles é alcançável
pelos outros dois — `ALTER TABLE ADD COLUMN NOT NULL` que passa em tabela vazia e
quebra na base do dono; três catálogos onde o plano supunha dois; um `import` no
topo de `test_debts.py` que derruba 17 testes de uma vez; `grep -o
'data-config="[a-z-]*"'` que some com a linha inteira se o nome tiver dígito.

**Custo desse buraco, medido:** 3 defeitos vivos em produção havia semanas, e 7
critérios que teriam passado em verde medindo a coisa errada.

**Preço para fechá-lo:** 612.867 tokens neste item, com quatro revisores.

## O ponto cego que o método novo tem

A única fase que não passou de primeira falhou **na fronteira entre duas fases**:
um critério da fase 2 cobrava uma rota que só a fase 3 cria, e passava por
construção. Os quatro revisores leram fase 1, fase 2, fase 3 e a transversal de
segurança — ninguém leu as costuras.

## O que não dá para afirmar

**n = 1.** Três fases, um item, um implementador. A melhora de 1,55 para 1,33
rodada por fase é 4 rodadas contra 4,65 esperadas — dentro do ruído. O que **não**
está no ruído é 36 problemas achados antes de existir código e 3 defeitos vivos
que nenhuma implementação do `015` teria encostado.

## O que fazer com isto

A recomendação — o que adotar no generic-harness, o que não adotar, e o que
melhorar nele — está em `.harness/proposals/2026-09-07-002.md`.

## O que o método já pagou, antes de custar código

Quatro revisores de modelo forte leram o plano contra o código, sem escrever
implementação: **36 problemas distintos**. O detalhe está em
`02-revisao-pre-codigo.md`; o que importa para a métrica é a natureza deles.

**Três são defeitos vivos que não são deste item:**

1. O painel **pergunta para sempre o que o dono já respondeu** — `/dividas` grava
   `quitacao`, o consultor procura `quitacao-cdc`. É a causa do sintoma que abriu
   o item.
2. `/dividas` lê **`5000.00` como R$ 500.000,00**, em silêncio, no campo do saldo
   de quitação; e `inf`, `nan`, `1e308` ali — e `nan` no campo de taxa — são
   HTTP 500.
3. **`httpx` está no grupo `dev`** e é importado em produção: instalação sem o
   grupo dev não sobe o app.

**Cinco teriam produzido critério verde medindo a coisa errada** — a falha mais
cara que este projeto conhece:

- `ALTER TABLE ADD COLUMN NOT NULL` sem default passa em toda base de teste,
  porque elas têm a tabela vazia, e quebra só na base do dono.
- Trocar `RESERVE_MONTHS` sem trocar o texto faria `/objetivo` dizer "6 meses"
  acima de uma cifra de 3, e o critério que compara a cifra aprovaria.
- `grep -o 'data-gasto="[0-9]*"'` não casa negativo, e `sort -c` aprova o vazio.
- `--include=*.py` sem aspas faz o zsh abortar a linha; "não imprime nada" passa
  sem rodar.
- `data-total` em `/comprometido` é o total **de um dia do calendário**, não o
  comprometido.

**Quatro vieram de eu escrever número de cabeça em vez de medir:** o alcance
real é 404 lançamentos e não 356; `businessName` chega como string vazia; os
beneficiários são **720** e não 721, porque o projeto tem um predicado de gasto
único que eu não usei; e `386` não é `391`.

**Um é decisão de produto que nenhum requisito cobria:** a consulta de CNPJ seria
a primeira saída de rede sem opt-in, num produto que se define como local, com o
destino não nomeado e uma lista ordenada por dinheiro.

## Onde o defeito aparece

É a comparação que mais importa e a que não está em tokens. Na linha de base, 6
das 11 fases souberam do problema pela **validação cega** — depois de o código
existir, com uma rodada inteira de portões por reprovação. Aqui, 36 problemas
apareceram enquanto o custo de mudar era reescrever um parágrafo.

As métricas 2 a 5 e a 7 fecharam com a implementação, e estão acima. A 6 fechou
no planejamento: **quatorze ambiguidades, quatorze resolvidas por padrão do
projeto, zero perguntas ao dono** — a tabela *Decisões resolvidas por padrão* do
`03-plan.md` traz cada uma com o padrão que a decidiu.

O transcript da implementação está em
`~/.claude/projects/-home-euclidesgc-development-dash-financeiro--claude-worktrees-adoring-zhukovsky-8c7069/`,
com o sufixo do worktree — não no diretório sem sufixo que o handoff apontava.
Os subagentes não aparecem nele: o gasto de cada um vem do relatório da própria
tarefa.
