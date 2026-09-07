#!/usr/bin/env bash
#
# G4 — nenhum TODO, FIXME, XXX ou HACK no código.
#
# TODO é pendência guardada onde ninguém procura: não entra no roadmap, não
# vira divergência, não aparece em nenhuma revisão de prioridade. Ela envelhece
# no arquivo até que ninguém saiba mais se ainda vale. Pendência real vira item
# de roadmap ou divergência registrada — as duas coisas que alguém revisita.
#
# Este gate não tem escape: um TODO com justificativa continua sendo um TODO.
#
# Recebe a lista de arquivos por stdin. Imprime arquivo:linha:trecho.

set -uo pipefail

while IFS= read -r file || [ -n "$file" ]; do
  [ -f "$file" ] || continue
  grep -nE '\b(TODO|FIXME|XXX|HACK)\b' "$file" 2>/dev/null |
    while IFS=: read -r line content; do
      printf '%s:%s:%s\n' "$file" "$line" "$(printf '%s' "$content" | sed 's/^[[:space:]]*//')"
    done
done

exit 0
