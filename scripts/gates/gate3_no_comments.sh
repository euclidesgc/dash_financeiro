#!/usr/bin/env bash
#
# G3 — comentário só para o porquê que o código não mostra.
#
# O que este gate persegue é o comentário que repete a linha seguinte, o
# cabeçalho decorativo de seção e a nota de histórico ("antes era X",
# "adicionado na fase 12") — para isso existe o git. Legibilidade se conquista
# extraindo função ou variável com nome descritivo, não com prosa ao lado.
#
# Um comentário que começa por uma marca de justificativa passa: `motivo:`,
# `por quê:`, `decisão:`, `contorno:`, `invariante:`, `limitação:`. A marca é o
# custo de dizer que aquilo é uma razão, e não uma descrição.
#
# Comentário de várias linhas conta como UM bloco: se a primeira linha carrega
# a marca, a continuação passa junto. Justificativa raramente cabe em oitenta
# colunas, e reprovar a segunda linha ensinaria a escrever justificativa ruim.
#
# Recebe a lista de arquivos por stdin. Imprime arquivo:linha:trecho.

set -uo pipefail

while IFS= read -r file || [ -n "$file" ]; do
  [ -f "$file" ] || continue
  awk -v arquivo="$file" '
    BEGIN {
      justificativa = "(por ?qu[êe]|motivo|decis[ãa]o|contorno|workaround|invariante|limita[çc][ãa]o|restri[çc][ãa]o|ignore:|gate[0-9]-ok|coverage:ignore)"
      diretiva = "(ignore_for_file|dart format|coverage:|@|https?:|eslint-|prettier-|ts-ignore|ts-expect-error|#!|#region|#endregion)"
      bloco_justificado = 0
    }
    {
      linha = $0
      sub(/^[[:space:]]+/, "", linha)

      # Linha que não é comentário fecha o bloco corrente.
      if (linha !~ /^(\/\/|\/\/\/|#[^!])/) {
        bloco_justificado = 0
        next
      }

      if (linha ~ /gate3-ok/) { next }
      if (tolower(linha) ~ justificativa) { bloco_justificado = 1; next }
      if (linha ~ diretiva) { next }
      if (NR <= 3 && tolower(linha) ~ /(copyright|license|licen[çc]a)/) { next }

      # Continuação de um bloco cuja primeira linha declarou a razão.
      if (bloco_justificado) { next }

      printf "%s:%d:%s\n", arquivo, NR, linha
    }
  ' "$file"
done

exit 0
