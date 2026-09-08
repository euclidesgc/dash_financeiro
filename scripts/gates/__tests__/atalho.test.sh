#!/usr/bin/env bash
# Prova que o portão do item 14 MORDE cada uma das três partes, e que ele
# reprova quando não consegue medir em vez de aprovar por não ter olhado.
#
# O caso que mais importa é o do universo vazio. Um portão que varre e não acha
# responde igual a um portão que varreu o diretório errado — é o defeito que o
# `medir.sh` inteiro existe para matar, e um portão novo o reintroduz de graça
# se ninguém escrever este caso.
set -uo pipefail
raiz="$(cd "$(dirname "$0")/../../.." && pwd)"
alvo="$raiz/scripts/gates/atalho.sh"
falhas=0

# Reason: without this guard, `bash <missing target>` exits 1 and **every**
# case expecting a refusal passes — the whole suite goes green measuring its
# own absence.
if [ ! -f "$alvo" ]; then
  printf '::error::%s não existe — não há o que medir\n' "$alvo" >&2
  exit 2
fi

ROADMAP='# Roadmap

- [x] `001-esqueleto` — bootstrap
- [-] `014-limite-de-taxa` — limitar requisições por conta
- [ ] `015-perfil` — ver e editar os próprios dados
'

# Reason: projeto <code file content> [roadmap content | SEM_ROADMAP] builds a
# git repository with the code and (almost always) the roadmap, and echoes
# the path. `git add` is what puts the file in `git ls-files`'s universe.
projeto() {
  local codigo="$1" roadmap="${2:-$ROADMAP}" dir
  dir="$(mktemp -d)"
  git -C "$dir" init -q .
  mkdir -p "$dir/src" "$dir/product"
  printf '%s\n' "$codigo" > "$dir/src/servico.ts"
  if [ "$roadmap" != "SEM_ROADMAP" ]; then
    printf '%s\n' "$roadmap" > "$dir/product/roadmap.md"
  fi
  git -C "$dir" add -A >/dev/null 2>&1
  printf '%s' "$dir"
}

# Reason: roda <directory> runs the gate the way the project runs it.
# `GITHUB_WORKSPACE` is unset from the environment on purpose — inside CI it
# would point at the harness's own repository, and the gate would measure
# the wrong tree either way.
roda() {
  ( cd "$1" && env -u GITHUB_WORKSPACE bash "$alvo" )
}

caso() { # caso <nome> <esperado 0|1> <conteúdo do código> [roadmap]
  local nome="$1" esperado="$2" dir obtido
  dir="$(projeto "$3" "${4:-$ROADMAP}")"
  roda "$dir" >/dev/null 2>&1
  obtido=$?
  [ "$obtido" -ne 0 ] && obtido=1
  rm -rf "$dir"
  if [ "$obtido" = "$esperado" ]; then
    printf '  ok    %s\n' "$nome"
  else
    printf '  FALHA %s — esperava %s, obteve %s\n' "$nome" "$esperado" "$obtido"
    falhas=$((falhas + 1))
  fi
}

contem() { # contem <nome> <trecho> <conteúdo do código> [roadmap]
  local nome="$1" trecho="$2" dir saida
  dir="$(projeto "$3" "${4:-$ROADMAP}")"
  saida="$(roda "$dir" 2>&1)"
  rm -rf "$dir"
  if printf '%s' "$saida" | grep -qF "$trecho"; then
    printf '  ok    %s\n' "$nome"
  else
    printf '  FALHA %s — a saída não contém "%s"\n' "$nome" "$trecho"
    falhas=$((falhas + 1))
  fi
}

COMPLETO='// atalho: trava global no processo. teto: ~50 req/s. troca: por trava por conta quando a vazão passar disso. item: 014-limite-de-taxa'
SEM_TETO='// atalho: trava global no processo. troca: por trava por conta. item: 014-limite-de-taxa'
SEM_TROCA='// atalho: trava global no processo. teto: ~50 req/s. item: 014-limite-de-taxa'
SEM_ITEM='// atalho: trava global no processo. teto: ~50 req/s. troca: por trava por conta.'
ITEM_FANTASMA='// atalho: trava global. teto: ~50 req/s. troca: por trava por conta. item: 099-nunca-existiu'
ORDEM_TROCADA='// atalho: trava global. item: 015-perfil. troca: por trava por conta. teto: ~50 req/s'
LIMPO='export const soma = (a: number, b: number) => a + b;'

caso "marcador completo com item na fila aprova" 0 "$COMPLETO"
caso "os três rótulos em qualquer ordem aprovam" 0 "$ORDEM_TROCADA"
caso "código sem marcador nenhum aprova" 0 "$LIMPO"
caso "marcador sem teto REPROVA" 1 "$SEM_TETO"
caso "marcador sem troca REPROVA — é um lembrete sem prazo" 1 "$SEM_TROCA"
caso "marcador sem item REPROVA — a dívida não existiria na fila" 1 "$SEM_ITEM"
caso "item que não está no roadmap REPROVA" 1 "$ITEM_FANTASMA"
caso "marcador com roadmap ausente REPROVA por impossibilidade de medição" 1 \
  "$COMPLETO" "SEM_ROADMAP"
caso "código limpo com roadmap ausente aprova — a fila só é exigida se há marcador" 0 \
  "$LIMPO" "SEM_ROADMAP"
caso "roadmap sem nenhum id REPROVA por impossibilidade de medição" 1 \
  "$COMPLETO" "# Roadmap sem itens"

contem "a reprovação nomeia o arquivo e a linha" "file=src/servico.ts,line=1" "$SEM_TETO"
contem "a reprovação diz qual rótulo faltou" "não declara teto" "$SEM_TETO"
contem "o item fantasma é nomeado na reprovação" "099-nunca-existiu" "$ITEM_FANTASMA"
contem "o portão diz quantos arquivos varreu" "arquivo(s) versionados varridos" "$COMPLETO"
contem "o portão diz quantos itens leu do roadmap" "item(ns) no roadmap" "$COMPLETO"
contem "sem marcador, ele diz que varreu e não achou" "0 marcador(es)" "$LIMPO"
contem "o roadmap ausente reprova por não medir, e diz isso" "não conseguiu medir" \
  "$COMPLETO" "SEM_ROADMAP"

# Reason: the comment prefix is not only C-family — a project with Python,
# SQL or shell marks with `#` and with `--`, and a gate blind to them clears
# half a repository's whole debt without ever flagging a thing.
outro_prefixo() { # outro_prefixo <nome> <arquivo> <linha> <esperado>
  local nome="$1" arquivo="$2" linha="$3" esperado="$4" dir obtido
  dir="$(mktemp -d)"
  git -C "$dir" init -q .
  mkdir -p "$dir/product"
  printf '%s\n' "$ROADMAP" > "$dir/product/roadmap.md"
  printf '%s\n' "$linha" > "$dir/$arquivo"
  git -C "$dir" add -A >/dev/null 2>&1
  roda "$dir" >/dev/null 2>&1
  obtido=$?
  [ "$obtido" -ne 0 ] && obtido=1
  rm -rf "$dir"
  if [ "$obtido" = "$esperado" ]; then
    printf '  ok    %s\n' "$nome"
  else
    printf '  FALHA %s — esperava %s, obteve %s\n' "$nome" "$esperado" "$obtido"
    falhas=$((falhas + 1))
  fi
}

outro_prefixo "marcador Python incompleto REPROVA" "tarefa.py" \
  "# atalho: varredura O(n2). teto: 10k linhas." 1
outro_prefixo "marcador SQL completo aprova" "consulta.sql" \
  "-- atalho: sem índice. teto: 100k linhas. troca: índice composto quando passar. item: 015-perfil" 0

# Reason: documentation that EXPLAINS the convention is not debt. A gate
# that counts it fails the very text that teaches the rule, and the team
# learns to delete the example instead of writing the marker.
md_ignorado() {
  local dir obtido
  dir="$(mktemp -d)"
  git -C "$dir" init -q .
  mkdir -p "$dir/product" "$dir/docs"
  printf '%s\n' "$ROADMAP" > "$dir/product/roadmap.md"
  printf '%s\n' 'Exemplo: `// atalho: trava global.` — sem teto de propósito.' \
    > "$dir/docs/convencao.md"
  # Reason: a clean code file keeps the universe non-empty — without it the
  # gate would fail for having nothing to sweep, and the case would measure
  # something else entirely.
  mkdir -p "$dir/src"
  printf '%s\n' 'export const x = 1;' > "$dir/src/servico.ts"
  git -C "$dir" add -A >/dev/null 2>&1
  roda "$dir" >/dev/null 2>&1
  obtido=$?
  rm -rf "$dir"
  if [ "$obtido" -eq 0 ]; then
    printf '  ok    %s\n' "marcador dentro de .md é ignorado — o portão não morde a própria documentação"
  else
    printf '  FALHA %s — esperava 0, obteve %s\n' "marcador em .md deveria ser ignorado" "$obtido"
    falhas=$((falhas + 1))
  fi
}
md_ignorado

# Reason: outside a git repository there is no `git ls-files`, and sweeping a
# universe it does not know answers "no marker" for the case where it never
# even looked.
fora_de_git() {
  local dir obtido saida
  dir="$(mktemp -d)"
  printf '%s\n' "$COMPLETO" > "$dir/servico.ts"
  saida="$(roda "$dir" 2>&1)"
  obtido=$?
  rm -rf "$dir"
  if [ "$obtido" -ne 0 ] && printf '%s' "$saida" | grep -qF "não conseguiu medir"; then
    printf '  ok    %s\n' "fora de repositório git REPROVA por impossibilidade de medição"
  else
    printf '  FALHA %s — esperava recusa por não medir, obteve %s\n' "fora de git" "$obtido"
    falhas=$((falhas + 1))
  fi
}
fora_de_git

if [ "$falhas" -eq 0 ]; then
  echo ""
  echo "✓ atalho: as três partes mordem, e não conseguir medir reprova."
  exit 0
fi
echo ""
echo "✗ $falhas caso(s) falharam."
exit 1
