#!/usr/bin/env bash
#
# G3 — comment only for the why that the code does not show.
#
# What this gate goes after is the comment that repeats the next line, the
# decorative section header, and the history note ("used to be X", "added in
# phase 12") — that is what git is for. Readability is earned by extracting a
# function or a descriptively named variable, not by prose alongside it.
#
# A comment that opens with a justification tag passes: `motivo:`, `por quê:`,
# `decisão:`, `contorno:`, `invariante:`, `limitação:` — or the English
# equivalent, `reason:`, `why:`, `decision:`, `workaround:`, `invariant:`,
# `constraint:`, `limitation:`. The two languages coexist: norm 16 asks for
# English, but the tree still carries Portuguese tags, and dropping both at
# once would leave the gate red in the middle of the migration (phase 2
# converts what is left). The tag is the toll for calling something a reason,
# and not a description.
#
# The comment block that OPENS the file — before any line of code — is a
# header, and it passes without a tag: recognised by position, not by text.
# A shebang and a licence block before it do not close that window; the first
# line of code does. It is the difference between documenting the file and
# narrating the next line.
#
# A multi-line comment counts as ONE block: if the first line carries the
# tag, the continuation passes with it. Justification rarely fits in eighty
# columns, and failing the second line would teach people to write bad
# justification.
#
# Receives the file list over stdin. Prints file:line:snippet.

set -uo pipefail

while IFS= read -r file || [ -n "$file" ]; do
  [ -f "$file" ] || continue
  awk -v arquivo="$file" '
    BEGIN {
      # Reason: alternation, not a character class — the regex engine of awk
      # compares byte by byte, and a class like [ãa] expects ONE byte where
      # "ã" takes two, so the accented tags the documentation above tells you
      # to use never matched.
      justificativa = "(por ?qu(ê|e)|motivo|decis(ã|a)o|contorno|workaround:|invariante|limita(ç|c)(ã|a)o|restri(ç|c)(ã|a)o|(reason|decision|why|invariant|constraint|limitation):|ignore:|gate[0-9]-ok|coverage:ignore)"
      diretiva = "(ignore_for_file|dart format|coverage:|@|https?:|eslint-|prettier-|ts-ignore|ts-expect-error|#!|#region|#endregion)"
      bloco_justificado = 0
      # Invariant: as long as no line of code has appeared, the block that
      # opens the file is a header and passes by position. It closes on the
      # first line of code.
      sem_codigo_ainda = 1
    }
    {
      linha = $0
      sub(/^[[:space:]]+/, "", linha)

      # Decision: an empty comment ("#" or "//" with no text) closes the
      # paragraph and does NOT close the header window. Both halves cost
      # dearly to learn. Without the second, the blank separator every script
      # header uses counted as code and closed the header on the second line
      # of the file, because `#[^!]` demands a second byte a lone "#" does not
      # have. Without the first, a tag anywhere in the block contaminated
      # every following paragraph: decorative header, history note, and prose
      # with no tag at all passed by inheriting justification that belonged
      # to another paragraph.
      if (linha ~ /^(\/\/\/?|#)[[:space:]]*$/) { bloco_justificado = 0; next }

      eh_shebang = (linha ~ /^#!/)

      # Decision: a line that is not a comment closes the current block, but
      # a shebang is the exception — it is neither comment nor code, so it
      # does not close the header window, which is the case the item asks
      # not to break.
      if (linha !~ /^(\/\/|\/\/\/|#[^!])/) {
        bloco_justificado = 0
        if (linha != "" && !eh_shebang) { sem_codigo_ainda = 0 }
        next
      }

      if (sem_codigo_ainda) { next }

      if (linha ~ /gate3-ok/) { next }

      # Invariant: the tag counts at the start of the comment, not anywhere in
      # the sentence. Without an anchor, "no idea why this works" pays the
      # toll the tag exists to charge, and the gate turns into decoration.
      texto = linha
      sub(/^(\/\/\/?|#)[[:space:]]*/, "", texto)
      if (tolower(texto) ~ ("^" justificativa)) { bloco_justificado = 1; next }
      if (linha ~ diretiva) { next }

      # Reason: continuation of a block whose first line already declared the
      # reason.
      if (bloco_justificado) { next }

      printf "%s:%d:%s\n", arquivo, NR, linha
    }
  ' "$file"
done

exit 0
