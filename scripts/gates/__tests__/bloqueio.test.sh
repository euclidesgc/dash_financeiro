#!/usr/bin/env bash
# Prova que a trava de bloqueio MORDE, e morde no formato em que o GitHub
# entrega os rótulos de verdade.
#
# O caso que importa é o terceiro: `toJSON` devolve JSON indentado, e a versão
# anterior desta verificação — `tr -d '[]"' | grep '^blocked-on-'` — respondia
# "nenhum bloqueio pendente" para um PR rotulado, porque a linha vinha com dois
# espaços na frente e a âncora não casava. O PR #13 passou verde com o rótulo
# posto. Sem este caso, a próxima reescrita reintroduz o mesmo silêncio.
set -uo pipefail
raiz="$(cd "$(dirname "$0")/../../.." && pwd)"
alvo="$raiz/scripts/gates/bloqueio.sh"
falhas=0

caso() { # caso <nome> <esperado 0|1> <corpo>
  local nome="$1" esperado="$2" corpo="$3" obtido
  ( eval "$corpo" ) >/dev/null 2>&1
  obtido=$?
  [ "$obtido" -ne 0 ] && obtido=1
  if [ "$obtido" = "$esperado" ]; then
    printf '  ok    %s\n' "$nome"
  else
    printf '  FALHA %s — esperava %s, obteve %s\n' "$nome" "$esperado" "$obtido"
    falhas=$((falhas + 1))
  fi
}

contem() { # contem <nome> <trecho> <corpo>
  local nome="$1" trecho="$2" corpo="$3" saida
  saida="$( ( eval "$corpo" ) 2>&1 )"
  if printf '%s' "$saida" | grep -qF "$trecho"; then
    printf '  ok    %s\n' "$nome"
  else
    printf '  FALHA %s — a saída não contém "%s"\n' "$nome" "$trecho"
    falhas=$((falhas + 1))
  fi
}

INDENTADO='[
  "blocked-on-D-011"
]'
INDENTADO_MISTO='[
  "bug",
  "blocked-on-D-011",
  "enhancement"
]'

caso "PR sem rótulo nenhum passa" 0 \
  "export ROTULOS='[]'; bash '$alvo'"
caso "PR só com rótulos comuns passa" 0 \
  "export ROTULOS='[\"bug\",\"enhancement\"]'; bash '$alvo'"
caso "rótulo de bloqueio em JSON de uma linha REPROVA" 1 \
  "export ROTULOS='[\"blocked-on-D-011\"]'; bash '$alvo'"
caso "rótulo de bloqueio em JSON indentado REPROVA — o formato que o toJSON entrega" 1 \
  "export ROTULOS='$INDENTADO'; bash '$alvo'"
caso "bloqueio misturado a rótulos comuns REPROVA" 1 \
  "export ROTULOS='$INDENTADO_MISTO'; bash '$alvo'"
caso "ROTULOS ausente REPROVA por impossibilidade de medição" 1 \
  "unset ROTULOS; bash '$alvo'"
caso "ROTULOS que não é JSON REPROVA por impossibilidade de medição" 1 \
  "export ROTULOS='blocked-on-D-011'; bash '$alvo'"
caso "ROTULOS que é JSON mas não é lista de nomes REPROVA" 1 \
  "export ROTULOS='{\"name\":\"blocked-on-D-011\"}'; bash '$alvo'"

contem "a reprovação nomeia o rótulo que trava" "blocked-on-D-011" \
  "export ROTULOS='$INDENTADO'; bash '$alvo'"
contem "o portão diz quantos rótulos mediu" "medido: 3 rótulo(s)" \
  "export ROTULOS='$INDENTADO_MISTO'; bash '$alvo'"
contem "a ausência de ROTULOS reprova por não medir, e diz isso" "não conseguiu medir" \
  "unset ROTULOS; bash '$alvo'"

if [ "$falhas" -eq 0 ]; then
  echo ""
  echo "✓ bloqueio: a trava morde o rótulo indentado e reprova quando não mede."
  exit 0
fi
echo ""
echo "✗ $falhas caso(s) falharam."
exit 1
