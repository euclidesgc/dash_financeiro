#!/usr/bin/env bash
# Asserções para portão. Carregue com `source scripts/gates/medir.sh`.
#
# gate3-ok: o texto abaixo é a razão de o arquivo existir, não a mecânica dele.
#
# A CAUSA RAIZ QUE ISTO EXISTE PARA MATAR
#
# Um portão faz duas perguntas, e quase todo mundo escreve só a segunda:
#
#   1. consegui medir?
#   2. o que medi?
#
# Quando a primeira fica implícita, o predicado responde igual para "procurei e
# não achei" e para "não consegui procurar" — e o portão passa por não ter
# medido. Aconteceu quatro vezes num único dia no primeiro projeto real:
#
#   find apps/api/src -name '*.ts'   → vazio se não há fonte E se o diretório
#                                      não existe. A guarda do CI rodava dentro
#                                      de apps/api por causa de um
#                                      working-directory herdado, procurava
#                                      apps/api/apps/api/src, e respondia "não
#                                      há código" em toda branch.
#   git diff --exit-code <arquivo>   → 0 se está idêntico E se o gerador não
#                                      escreveu nada.
#   contador de progresso com CPU    → CPU sempre sobe, então "nada mudou"
#                                      nunca acontecia e o alarme nunca tocava.
#
# A regra: **não conseguir medir é reprovação, nunca aprovação.** Estas funções
# fazem a pergunta 1 falhar fechada e em voz alta, para a pergunta 2 só ser
# feita quando tiver sentido.
set -uo pipefail

# Reason: the anchor is never the current directory — that is exactly what
# shifts underneath you.
medir_raiz() {
  printf '%s' "${GITHUB_WORKSPACE:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
}

_reprova() {
  printf '::error::portão não conseguiu medir: %s\n' "$1" >&2
  printf 'REPROVADO por impossibilidade de medição, não por resultado.\n' >&2
  exit 1
}

exige_caminho() {
  local alvo="$(medir_raiz)/$1"
  [ -e "$alvo" ] || _reprova "$1 não existe sob $(medir_raiz) — esperava $2"
}

exige_comando() {
  command -v "$1" >/dev/null 2>&1 || _reprova "o comando '$1' não está no PATH"
}

# Reason: exige_modulo_python <module> <why it is necessary> — having
# `python3` on PATH is not having the module the gate imports. A missing
# `import` throws a traceback BEFORE any `_reprova` runs, and what the reader
# gets is a stack trace — not "failed to measure". Worse: on a runner with
# the system Python the module usually exists, and on one with a clean
# `setup-python` it does not; the same gate passes on one machine and blows
# up on another for a reason the message never names.
exige_modulo_python() {
  python3 -c "import $1" >/dev/null 2>&1 ||
    _reprova "o módulo python '$1' não está disponível — $2"
}

# Reason: exige_escrita <file> <epoch instant before generation> proves the
# tool actually wrote, instead of accepting silence as success.
exige_escrita() {
  local arquivo="$(medir_raiz)/$1" antes="$2"
  [ -f "$arquivo" ] || _reprova "$1 não existe depois da geração"
  local depois; depois="$(stat -c %Y "$arquivo" 2>/dev/null || echo 0)"
  [ "$depois" -gt "$antes" ] || _reprova "$1 não foi reescrito — o gerador não rodou, e comparar o que ninguém gerou aprova qualquer coisa"
}

# Reason: conta_sob <relative path> <find expression...> only counts after
# proving there is something to count over.
conta_sob() {
  local rel="$1"; shift
  exige_caminho "$rel" "um diretório para contar"
  find "$(medir_raiz)/$rel" "$@" 2>/dev/null | wc -l
}

# Reason: exige_pacote_pnpm <filter> <what it should match> — `pnpm --filter
# <nonexistent> <script>` prints "No projects matched the filters" and exits
# 0. It is the fourth shape of the table: the CI step passes without having
# run anything, and the whole workflow stays green for failing to measure.
exige_pacote_pnpm() {
  local filtro="$1" descricao="$2" saida casados
  exige_comando pnpm
  # Reason: the marker is the measurement, and `/bin/sh` by absolute path is
  # what prints it. Counting the output's lines would pass on pnpm's own "No
  # projects matched" notice, which it sends to standard output; and calling
  # `sh` by name would let `pnpm exec` resolve it inside the package's
  # `node_modules/.bin`, where a dependency declaring `"bin": {"sh": ...}`
  # would answer in the shell's place.
  saida="$(cd "$(medir_raiz)" && pnpm --filter "$filtro" exec /bin/sh -c 'echo PACOTE_MEDIDO' 2>&1)" || true
  # Reason: `grep -c` exits 1 when it counts zero, and GitHub Actions' `run:`
  # executes under `bash -e` — without the `|| true`, the assertion would die
  # on the assignment and the step would go red without printing a single
  # line of what it measured.
  casados="$(printf '%s\n' "$saida" | grep -c '^PACOTE_MEDIDO$' || true)"
  echo "medido: $casados pacote(s) casados pelo filtro '$filtro'"
  if [ "$casados" -lt 1 ]; then
    printf '%s\n' "$saida" >&2
    _reprova "o filtro pnpm '$filtro' não casou pacote nenhum — esperava $descricao, e os passos seguintes sairiam 0 sem rodar"
  fi
}
