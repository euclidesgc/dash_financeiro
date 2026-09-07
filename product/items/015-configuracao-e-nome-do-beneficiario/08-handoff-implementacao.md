# Handoff — implementação do `015`, em sessão nova

Este documento existe porque a implementação começa com a conta de tokens
zerada, para que o custo dela possa ser comparado com os itens anteriores. Quem
abrir a sessão nova lê isto primeiro e não precisa de mais nada da sessão de
planejamento.

## Onde o trabalho está

- **Plano aprovado:** `product/items/015-configuracao-e-nome-do-beneficiario/03-plan.md`
  — três fases, 24 etapas, critérios tipados. É o contrato.
- **Requisitos:** `01-brief.md`, `RF-01` a `RF-30` mais os sufixados.
- **Por que o plano está assim:** `02-revisao-pre-codigo.md` — 36 problemas que
  quatro revisores acharam antes de existir código. Leia antes de discordar de
  uma etapa: a maioria das escolhas estranhas está explicada ali.
- **Medição:** `07-metrica-do-metodo.md` — a linha de base e o que falta medir.
- **Estado do harness:** item em `execute`, brief e plano aprovados por humano.

## Como implementar

Uma fase por vez, na ordem. **Uma fase é um PR**, e a integração é `develop` —
nunca `main`. Cada fase termina com **uma** validação cega do `phase-validator`,
que é sempre um agente novo e nunca recebe o plano, o brief nem veredicto
anterior. Achado que o próprio veredicto marca como "não reprova" vira correção
com teste que falha sem ela, nomeada na entrega — **nunca uma rodada nova**.
Rodada nova só se o veredicto for `REPROVADO` ou `CRITERIO_INVALIDO`.

Nunca troque de branch enquanto um validador estiver rodando.

## O que medir, e anotar em `07-metrica-do-metodo.md`

| # | Métrica | Alvo |
|---|---|---|
| 1 | Problemas achados na revisão pré-código | fechado: **36** |
| 2 | Rodadas até `APROVADO`, por fase | ≤ 1,55 |
| 3 | Veredicto da primeira rodada de cada fase | `APROVADO` nas três |
| 4 | Achados do validador que critério nenhum cobria | < 4,6 por fase |
| 5 | Números de critério reescritos depois de implementar | **zero** |
| 6 | Ambiguidades resolvidas por padrão × perguntas | fechado: 14 × 0 |
| 7 | **Tokens da implementação** | < 410.000 para as três fases |

Guarde **um arquivo de veredicto por rodada** em `05-veredictos/`, sem
sobrescrever: os itens `005` em diante sobrescreveram e por isso o disco não
sabe contar rodadas neles.

A métrica 7 se mede no fim, do transcript da sessão nova, somando
`input_tokens + cache_creation_input_tokens + output_tokens` de cada mensagem, e
somando à parte o gasto de qualquer subagente.

## Restrições que valem sem discussão

- **O hook de permissão nega qualquer comando que leia `.env`.** Não contorne e
  não insista. O código lê por `os.environ`; o `.env.example` documenta os nomes.
  Critério que precise provar que a variável existe prova pelo comportamento — o
  app sobe, o login funciona.
- **`rtk` reescreve saída de comando por hook global.** Quando a evidência de um
  critério precisar da saída bruta e íntegra, use `rtk proxy <comando>`.
- Nunca tirar rótulo de bloqueio para destravar, nunca mergear PR do meio da
  pilha, nunca mergear na branch de produção.
- Segredo nunca no repositório, nunca em HTML, nunca em log.
- As normas e invariantes do `CLAUDE.md` valem integralmente. As que este item
  mais toca: 22 (centavos inteiros), 24 (login antes de qualquer rota que
  devolva dado), 26 (o que só o humano sabe é parâmetro de tela), 12 (pendência
  vira item de roadmap), 15 (sem dependência não declarada), 16 (código e
  commits em inglês, documento e interface em pt-BR), 11 (zero comentário,
  exceto o porquê que o código não mostra).
- Antes de escrever qualquer tela, carregue a skill `frontend-design`, e leia
  `product/00-linguagem-visual.md`, que é canônico.

## As três armadilhas que já custaram caro nesta corrida

1. **Número de critério escrito de cabeça.** Aconteceu em `007`, `011` e duas
   vezes no `014`. Se um critério afirma um número, meça antes de implementar,
   não depois.
2. **Captura escrita em diretório inexistente.** Quatro vezes, porque o script
   era recriado por `sed` a cada item. A etapa **2.5** manda versionar
   `scripts/capturas.mjs` — faça-a antes de qualquer captura.
3. **`gates_runner.sh` aprova falso** numa árvore sem `.git`: imprime
   `0 arquivo(s) considerados` e sai `0`. Portão que não conseguiu medir
   reprova, nunca aprova.

## Comece por aqui

Fase 1, etapa 1.1 — a migração `010_settings.sql`. Leia a etapa inteira no
plano: ela tem um `DEFAULT` que parece detalhe e não é, e uma regra de
precedência para quando o nome canônico já existir dos dois lados.
