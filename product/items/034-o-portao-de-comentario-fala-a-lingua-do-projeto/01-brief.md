# Brief — 034-o-portao-de-comentario-fala-a-lingua-do-projeto

**Trilha:** rápida · **Este documento funde discovery, PRD e spec.**
**Absorve o item `031`**, que era a consequência deste. Norma 20: segunda
ocorrência é causa raiz, não segundo remendo.

## Problema

Duas normas do projeto se contradizem, e o que decide qual delas vale é o acaso
de qual arquivo o portão alcança.

- **Norma 16** manda escrever código em inglês.
- **Norma 11** só aceita comentário que diga um porquê.
- **O portão que cobra a norma 11 reconhece a justificativa por palavra em
  português** — `motivo`, `decisão`, `contorno`, `invariante`, `limitação`,
  `restrição` — e por nenhuma em inglês.

Um comentário de decisão escrito na língua que a norma 16 manda usar é **reprovado
pelo portão**. Um escrito em português passa e **viola a norma 16**.

## O tamanho real, medido em 08/09/2026

Rodando o portão sobre a árvore inteira: **1.129 linhas acusadas em 103
arquivos** — que são **407 blocos** de comentário. Por área: `app` 187 blocos,
`scripts` 174, `tests` 46.

E a amostra mostra que **a maior parte não é comentário ruim**. São justificativas
legítimas, em inglês, sem marca — e cabeçalhos de arquivo de script, que
documentam o contrato do próprio arquivo e não têm outro lugar onde morar. O
portão trata os três casos como um só.

Por isso o portão hoje só julga as linhas acrescentadas desde o commit que o
ligou. **Portão com recorte é portão com prazo:** ou a árvore antiga se adapta, ou
o recorte vira permanente e a norma 11 volta a valer só para quem chegou depois.

## Escopo

O portão reconhece justificativa na língua em que o projeto escreve código,
distingue cabeçalho de arquivo de comentário ao lado de código, e passa a julgar
a árvore inteira — sem recorte.

## Requisitos

- **RF-01.** O portão reconhece marcas de justificativa em inglês, e continua
  reconhecendo as em português enquanto elas existirem na árvore.
- **RF-02.** O portão distingue o **cabeçalho de arquivo** — o bloco que abre um
  script ou módulo e documenta o que ele faz e como se usa — de comentário ao
  lado de código. Cabeçalho não é comentário que repete a linha seguinte.
- **RF-03.** Todo comentário da árvore que sobreviver ao portão corrigido tem uma
  justificativa de verdade; o que não tiver é apagado ou reescrito.
- **RF-04.** O recorte por diff **sai**: o portão passa a julgar a árvore inteira,
  e `.harness/gates.json` deixa de trazer `modo: diff` para ele.
- **RF-05.** Nenhum comportamento muda. Comentário não executa.

## Riscos

- **Apagar a razão junto com a prosa.** Um comentário sem marca pode ser a única
  explicação de uma decisão cara. RF-03 pede julgamento por bloco, não varredura
  automática — e o que se perde não volta do git com facilidade.
