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
# `por quê:`, `decisão:`, `contorno:`, `invariante:`, `limitação:` — ou o
# equivalente em inglês, `reason:`, `why:`, `decision:`, `workaround:`,
# `invariant:`, `constraint:`, `limitation:`. As duas línguas convivem: a
# norma 16 pede inglês, mas a árvore ainda tem marca em português, e tirar as
# duas de uma vez deixaria o portão vermelho no meio da migração (fase 2
# converte o que sobrar). A marca é o custo de dizer que aquilo é uma razão, e
# não uma descrição.
#
# O bloco de comentário que ABRE o arquivo — antes de qualquer linha de
# código — é cabeçalho, e passa sem marca: reconhecido pela posição, não pelo
# texto. Shebang e bloco de licença antes dele não fecham essa janela; a
# primeira linha de código, sim. É a diferença entre documentar o arquivo e
# narrar a linha seguinte.
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
      # Alternância, não classe: o motor de regex do awk compara byte a byte, e
      # uma classe como [ãa] espera UM byte onde "ã" ocupa dois — então as marcas
      # acentuadas que a documentação acima manda usar nunca casavam.
      justificativa = "(por ?qu(ê|e)|motivo|decis(ã|a)o|contorno|workaround|invariante|limita(ç|c)(ã|a)o|restri(ç|c)(ã|a)o|(reason|decision|why|invariant|constraint|limitation):|ignore:|gate[0-9]-ok|coverage:ignore)"
      diretiva = "(ignore_for_file|dart format|coverage:|@|https?:|eslint-|prettier-|ts-ignore|ts-expect-error|#!|#region|#endregion)"
      bloco_justificado = 0
      # Invariante: enquanto nenhuma linha de código apareceu, o bloco que
      # abre o arquivo é cabeçalho e passa por posição. Fecha na primeira
      # linha de código.
      sem_codigo_ainda = 1
    }
    {
      linha = $0
      sub(/^[[:space:]]+/, "", linha)

      # Contorno: comentário vazio ("#" ou "//" sem texto) é separador de
      # parágrafo dentro de um bloco, não fecha a janela do cabeçalho nem
      # interrompe a continuação de um bloco já justificado. `#[^!]` mais
      # abaixo exige um segundo byte, e um "#" sozinho não tem um — sem este
      # desvio, o separador em branco que todo cabeçalho de script usa contava
      # como código e fechava o cabeçalho na segunda linha do arquivo.
      if (linha ~ /^(\/\/\/?|#)[[:space:]]*$/) { next }

      eh_shebang = (linha ~ /^#!/)

      # Decisão: linha que não é comentário fecha o bloco corrente, mas
      # shebang é a exceção — não é comentário e não é código, então não
      # fecha a janela do cabeçalho, que é o caso que o item pede para não
      # quebrar.
      if (linha !~ /^(\/\/|\/\/\/|#[^!])/) {
        bloco_justificado = 0
        if (linha != "" && !eh_shebang) { sem_codigo_ainda = 0 }
        next
      }

      if (sem_codigo_ainda) { next }

      if (linha ~ /gate3-ok/) { next }
      if (tolower(linha) ~ justificativa) { bloco_justificado = 1; next }
      if (linha ~ diretiva) { next }

      # Continuação de um bloco cuja primeira linha declarou a razão.
      if (bloco_justificado) { next }

      printf "%s:%d:%s\n", arquivo, NR, linha
    }
  ' "$file"
done

exit 0
