# Brief — 029-o-guarda-reconhece-uma-forma-so-de-perguntar-as-horas

**Item:** `029-o-guarda-reconhece-uma-forma-so-de-perguntar-as-horas` · **Trilha:** rápida

> Este documento funde PRD e spec.

## Problema

O guarda que impede uma rota de resolver a data de tela por conta própria procura
o **literal** `date.today()`. Três formas equivalentes escapam: `datetime.now().date()`,
`datetime.today()`, e um apelido de import (`from datetime import date as d`,
depois `d.today()`).

Guarda que reconhece uma forma só é guarda que ensina a contornar. E o silêncio
dele é caro: sem a data de referência, nenhuma tela é comparável com os números
congelados do documento de referência — foi por isso que o item `016` existiu.

## Escopo

O guarda reconhece a chamada ao relógio pela árvore sintática do módulo, não por
texto, e alcança as formas que hoje escapam — inclusive por apelido de import.

## Não-escopo

- **Nenhum módulo de rota muda.** O item é a rede, não o que ela pega.
- **A varredura recursiva do `020` não muda.** Ela já desce e já chaveia por
  caminho relativo.
- **Nada fora de `app/routers/` passa a ser varrido.**

## Requisitos

- **RF-01.** O guarda acusa `date.today()`, `datetime.today()`,
  `datetime.now().date()` e `datetime.now()` dentro de um módulo de rota.
- **RF-02.** O guarda acusa a mesma chamada feita por **apelido de import** —
  `from datetime import date as d` seguido de `d.today()`, e
  `import datetime as dt` seguido de `dt.datetime.now()`.
- **RF-03.** O guarda **não** acusa a cadeia quando ela aparece em comentário ou
  em literal de texto: reconhecer por árvore sintática é o que separa os dois.
- **RF-04.** O guarda continua não acusando módulo que consome o leitor único da
  data de referência, e continua alcançando subpasta de qualquer profundidade e
  chaveando por caminho relativo — o que o item `020` entregou não regride.
- **RF-05.** Os módulos de rota de hoje continuam passando: nenhum deles resolve
  a data por conta própria.
