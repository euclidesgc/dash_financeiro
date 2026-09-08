# Brief — 035-a-recusa-diz-o-que-faltou

**Trilha:** rápida · **Este documento funde discovery, PRD e spec.**

## Problema

Quando o dono corrige a classificação de um lançamento e não escolhe um grupo
existente nem digita um novo, o servidor recusa — corretamente, porque nenhuma
linha de grupo tem identificador nulo. Mas a mensagem que chega à tela mostra
literalmente **`None`** no lugar do termo que faltou.

`None` não é português, não é o nome de nada que o dono digitou, e não diz o que
fazer em seguida. A recusa está certa e a explicação está quebrada — e é a
explicação que decide se ele corrige ou desiste.

Achado pelo implementador do item `018` ao tornar o tipo honesto (`int | None`),
registrado em vez de corrigido em silêncio, porque mudar a mensagem é mudança de
comportamento fora do escopo daquela fase.

## Escopo

Toda recusa de correção de classificação diz, em português, **o que faltou** e o
que o dono precisa fazer.

## Requisitos

- **RF-01.** A recusa por grupo ausente diz que falta escolher ou nomear um
  grupo. Nunca imprime `None`.
- **RF-02.** Nenhuma mensagem de recusa do painel imprime `None`, `null` ou o
  nome de um símbolo de código.
- **RF-03.** A recusa continua sendo `400`, e continua não gravando nada.
- **RF-04.** As recusas que já diziam algo útil não mudam de texto.

## Riscos

- **Trocar a mensagem e perder a recusa.** RF-03 é o que mede: o `400` e a
  ausência de escrita continuam.
