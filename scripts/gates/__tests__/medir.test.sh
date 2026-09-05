#!/usr/bin/env bash
# Prova que cada asserção de medir.sh REPROVA quando deve. Uma biblioteca de
# portão sem este teste carrega o defeito que ela existe para matar, um nível
# acima: ninguém sabe se ela morde.
#
# O sandbox fica num caminho previsível e nada é apagado por trap — faxina
# destrutiva em trap é a linha que limpa a árvore errada no dia em que a
# variável vem vazia.
set -uo pipefail
aqui="$(cd "$(dirname "$0")" && pwd)"
lib="${MEDIR_SH:-$aqui/../medir.sh}"
[ -f "$lib" ] || { printf 'medir.sh não encontrado em %s\n' "$lib" >&2; exit 2; }
tmp="${TMPDIR:-/tmp}/medir-test-$$"
mkdir -p "$tmp/existe"
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

caso "exige_caminho passa quando existe" 0 \
  "GITHUB_WORKSPACE='$tmp'; source '$lib'; exige_caminho existe 'um diretório'"
caso "exige_caminho REPROVA quando não existe" 1 \
  "GITHUB_WORKSPACE='$tmp'; source '$lib'; exige_caminho nao-existe 'um diretório'"
caso "exige_comando passa com binário real" 0 \
  "source '$lib'; exige_comando find"
caso "exige_comando REPROVA com binário inexistente" 1 \
  "source '$lib'; exige_comando binario-inexistente-42"

: > "$tmp/gerado.txt"
antes="$(stat -c %Y "$tmp/gerado.txt")"
caso "exige_escrita REPROVA quando o gerador não escreveu" 1 \
  "GITHUB_WORKSPACE='$tmp'; source '$lib'; exige_escrita gerado.txt $antes"
caso "exige_escrita passa quando o arquivo foi reescrito" 0 \
  "GITHUB_WORKSPACE='$tmp'; source '$lib'; sleep 1; touch '$tmp/gerado.txt'; exige_escrita gerado.txt $antes"
caso "exige_escrita REPROVA quando o arquivo nem existe" 1 \
  "GITHUB_WORKSPACE='$tmp'; source '$lib'; exige_escrita nunca-gerado.txt 0"

# O caso que originou tudo: contar sob diretório inexistente tem de reprovar,
# nunca devolver zero em silêncio.
caso "conta_sob REPROVA quando o diretório não existe" 1 \
  "GITHUB_WORKSPACE='$tmp'; source '$lib'; conta_sob apps/api/src -name '*.ts'"
caso "conta_sob conta quando o diretório existe" 0 \
  "GITHUB_WORKSPACE='$tmp'; source '$lib'; conta_sob existe -type f"

caso "exige_pacote_pnpm REPROVA quando o filtro não casa pacote" 1 \
  "source '$lib'; exige_pacote_pnpm pacote-inexistente-42 'um pacote do workspace'"
# As duas asserções abaixo precisam de um workspace pnpm de verdade, então elas
# montam o seu: um teste que só passa no repositório onde nasceu não prova nada
# sobre o script que o harness entrega a outro projeto.
if command -v pnpm >/dev/null 2>&1; then
  ws="$tmp/ws"
  mkdir -p "$ws/packages/alvo"
  printf 'packages:\n  - "packages/*"\n' > "$ws/pnpm-workspace.yaml"
  printf '{"name":"raiz","private":true}\n' > "$ws/package.json"
  printf '{"name":"alvo","version":"1.0.0"}\n' > "$ws/packages/alvo/package.json"
  git -C "$ws" init -q 2>/dev/null

  # `medir_raiz` prefere `GITHUB_WORKSPACE`: sem apontá-lo para cá, dentro do CI
  # a função ignora o `cd` do caso e mede a raiz do repositório, onde o filtro
  # não casa pacote nenhum. Passava local e falhava só no CI.
  caso "exige_pacote_pnpm passa com um pacote real do workspace" 0 \
    "cd '$ws'; GITHUB_WORKSPACE='$ws'; source '$lib'; exige_pacote_pnpm alvo 'o pacote alvo'"

  # O marcador tem de vir do shell do sistema. Um `sh` que o PATH ofereça — e
  # `pnpm exec` oferece o `node_modules/.bin` do pacote antes de tudo — mataria
  # a medição e ainda daria execução de código a quem plantasse o binário.
  mkdir -p "$tmp/bin-sequestrado"
  printf '#!/bin/sh\nexit 0\n' > "$tmp/bin-sequestrado/sh"
  chmod +x "$tmp/bin-sequestrado/sh"
  caso "exige_pacote_pnpm ignora o 'sh' que o PATH oferece" 0 \
    "cd '$ws'; GITHUB_WORKSPACE='$ws'; PATH=\"$tmp/bin-sequestrado:\$PATH\"; source '$lib'; exige_pacote_pnpm alvo 'o pacote alvo'"
else
  printf '  pulado  as duas asserções de exige_pacote_pnpm — pnpm não está no PATH\n'
fi

if [ "$falhas" -eq 0 ]; then
  printf '\n✓ medir.sh: todas as asserções mordem.\n'
else
  printf '\n✗ %s asserção(ões) não reprovaram quando deveriam.\n' "$falhas" >&2
  exit 1
fi
