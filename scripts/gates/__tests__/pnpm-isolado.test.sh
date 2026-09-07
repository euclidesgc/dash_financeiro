#!/usr/bin/env bash
# Prova que o portão do pnpm isolado MORDE, e que ele separa três coisas que a
# leitura ingênua confunde: não usar a ação, usar a ação sem `dest`, e não
# conseguir ler o fluxo.
#
# O caso do vazio é o que costuma faltar. Um repositório que não usa
# `pnpm/action-setup` não tem defeito nenhum, e o portão precisa dizer isso em
# vez de reprovar; mas um YAML ilegível não é "nenhuma referência", é medição
# impossível — e passar ali seria exatamente o defeito que a régua da casa
# proíbe: não conseguir medir é recusa, nunca aprovação.
set -uo pipefail
raiz="$(cd "$(dirname "$0")/../../.." && pwd)"
alvo="$raiz/scripts/gates/pnpm_isolado.sh"
falhas=0

[ -f "$alvo" ] || {
  printf '✗ pnpm isolado: o alvo %s não existe — não há o que medir.\n' "$alvo" >&2
  exit 2
}

caso() { # caso <nome> <esperado 0|1> <trecho na saída> <conteúdo do fluxo>
  local nome="$1" esperado="$2" trecho="$3" corpo="$4" casa saida obtido
  casa="$(mktemp -d)"
  mkdir -p "$casa/.github/workflows" "$casa/scripts/gates"
  cp "$raiz/scripts/gates/medir.sh" "$casa/scripts/gates/medir.sh"
  cp "$alvo" "$casa/scripts/gates/pnpm_isolado.sh"
  printf '%s' "$corpo" > "$casa/.github/workflows/ci.yml"
  saida="$(env GITHUB_WORKSPACE="$casa" bash "$casa/scripts/gates/pnpm_isolado.sh" 2>&1)"
  obtido=$?
  [ "$obtido" -ne 0 ] && obtido=1
  if [ "$obtido" != "$esperado" ]; then
    printf '  FALHA %s — esperava %s, obteve %s\n' "$nome" "$esperado" "$obtido"
    printf '%s\n' "$saida" | sed 's/^/        /'
    falhas=$((falhas + 1))
    return
  fi
  if [ -n "$trecho" ] && ! printf '%s' "$saida" | grep -qF "$trecho"; then
    printf '  FALHA %s — a saída não contém %s\n' "$nome" "$trecho"
    printf '%s\n' "$saida" | sed 's/^/        /'
    falhas=$((falhas + 1))
    return
  fi
  printf '  ok    %s\n' "$nome"
}

CABECA='name: X
on: [push]
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
'

caso 'dest em runner.temp passa' 0 '0 sem `dest`' "${CABECA}      - uses: pnpm/action-setup@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        with:
          dest: \${{ runner.temp }}/setup-pnpm
"

caso 'SEM dest REPROVA' 1 'sem `dest`' "${CABECA}      - uses: pnpm/action-setup@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
"

caso 'sem dest, a saída diz o que escrever' 1 'runner.temp }}/setup-pnpm' "${CABECA}      - uses: pnpm/action-setup@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
"

caso 'dest com ~ REPROVA' 1 'dentro do HOME' "${CABECA}      - uses: pnpm/action-setup@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        with:
          dest: ~/setup-pnpm
"

caso 'dest com HOME REPROVA' 1 'dentro do HOME' "${CABECA}      - uses: pnpm/action-setup@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        with:
          dest: \$HOME/setup-pnpm
"

caso 'outro with, sem dest, ainda REPROVA' 1 'sem `dest`' "${CABECA}      - uses: pnpm/action-setup@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        with:
          version: 10.20.0
"

# O CASO DO VAZIO: nenhuma referência não é defeito, e o portão diz o número.
caso 'fluxo sem a ação nenhuma PASSA, e diz 0' 0 'medido: 0 referência(s)' "${CABECA}      - run: \"true\"
"

# O CASO DO ILEGÍVEL: não é "nenhuma referência", é medição impossível.
caso 'YAML ilegível RECUSA, e não passa por vazio' 1 'não é YAML legível' 'name: X
on: [push
jobs: : :
'

# Uma referência boa não absolve a ruim que está ao lado.
caso 'uma boa e uma ruim no mesmo job REPROVA' 1 'sem `dest`' "${CABECA}      - uses: pnpm/action-setup@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        with:
          dest: \${{ runner.temp }}/setup-pnpm
      - uses: pnpm/action-setup@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
"

# SEM PyYAML O PORTÃO RECUSA, E NÃO EXPLODE
#
# Ter `python3` no PATH não é ter o módulo que o portão importa. Um `import` que
# falta estoura traceback antes de qualquer recusa, e o que chega a quem lê é um
# rastro de pilha. Pior: num runner com o Python do sistema o módulo costuma
# existir, e num com `setup-python` limpo não — o mesmo portão passa numa
# máquina e explode noutra, por um motivo que a mensagem não diz. Medido: foi
# exatamente assim que este portão nasceu vermelho no CI e verde na máquina de
# quem o escreveu.
sem_pyyaml() {
  local casa saida obtido
  casa="$(mktemp -d)"
  mkdir -p "$casa/.github/workflows" "$casa/scripts/gates" "$casa/bin"
  cp "$raiz/scripts/gates/medir.sh" "$casa/scripts/gates/medir.sh"
  cp "$alvo" "$casa/scripts/gates/pnpm_isolado.sh"
  printf 'name: X\non: [push]\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - run: "true"\n' \
    > "$casa/.github/workflows/ci.yml"
  printf '#!/usr/bin/env bash\nif [ "${1:-}" = "-c" ] && [ "${2:-}" = "import yaml" ]; then exit 1; fi\nexec %s "$@"\n' \
    "$(command -v python3)" > "$casa/bin/python3"
  chmod +x "$casa/bin/python3"
  saida="$(env GITHUB_WORKSPACE="$casa" PATH="$casa/bin:$PATH" bash "$casa/scripts/gates/pnpm_isolado.sh" 2>&1)"
  obtido=$?
  rm -rf "$casa"
  if [ "$obtido" -eq 0 ]; then
    printf '  FALHA sem PyYAML o portão PASSOU — medição impossível virou aprovação\n'
    falhas=$((falhas + 1))
    return
  fi
  if ! printf '%s' "$saida" | grep -qF "não conseguiu medir"; then
    printf '  FALHA sem PyYAML o portão morreu sem dizer que não conseguiu medir\n'
    printf '%s\n' "$saida" | sed 's/^/        /'
    falhas=$((falhas + 1))
    return
  fi
  printf '  ok    sem PyYAML o portão RECUSA por impossibilidade de medição\n'
}
sem_pyyaml

[ "$falhas" -eq 0 ] && { printf '✓ pnpm isolado: as asserções mordem, e o vazio não é o ilegível\n'; exit 0; }
printf '✗ pnpm isolado: %s caso(s) falharam\n' "$falhas" >&2
exit 1
