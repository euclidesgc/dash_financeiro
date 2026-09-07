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

## O que este item mede

| # | Métrica | Alvo | Resultado |
|---|---|---|---|
| 1 | Problemas achados na revisão pré-código | quanto mais, melhor | **36 distintos**, 3 deles defeitos vivos |
| 2 | Rodadas até `APROVADO`, por fase | ≤ 1,55 | a preencher |
| 3 | Veredicto da primeira rodada de cada fase | `APROVADO` nas três | a preencher |
| 4 | Achados do validador que critério nenhum cobria | menos que a média | a preencher |
| 5 | Números de critério reescritos depois de implementar | **zero** | a preencher |
| 6 | Ambiguidades resolvidas por padrão × perguntas ao dono | **zero perguntas** | 7 resolvidas, 0 perguntas |

A métrica 6 já fechou no planejamento: as sete dúvidas estão na tabela
*Decisões resolvidas por padrão* do `03-plan.md`, cada uma com o padrão do
projeto que a decidiu, e nenhuma virou pergunta.

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

## O que já dá para dizer do método

O planejamento em acúmulo custou **uma sessão** e ainda não escreveu código. A
comparação honesta não é com o tempo: é com **onde** o defeito aparece. Na linha
de base, 6 das 11 fases souberam do problema pela validação cega — isto é,
**depois** de o código existir, e cada reprovação custa uma rodada inteira de
portões. Aqui, 36 problemas apareceram enquanto o custo de mudar era reescrever
um parágrafo.

As métricas 2 a 5 só fecham depois de implementar. A 6 fechou: **quatorze
ambiguidades, quatorze resolvidas por padrão do projeto, zero perguntas ao dono**
— a tabela *Decisões resolvidas por padrão* do `03-plan.md` traz cada uma com o
padrão que a decidiu.
