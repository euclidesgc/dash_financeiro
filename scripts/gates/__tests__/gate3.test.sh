#!/usr/bin/env bash
# Prova que G3 aprendeu a marca de justificativa em inglês sem esquecer a em
# português, e que ele distingue cabeçalho de comentário ao lado de código.
#
# O par que mais importa é o dos dois últimos casos: o mesmo texto, sem marca,
# passa quando abre o arquivo e é acusado quando mora ao lado de uma linha de
# código. Sem os dois lados desse par, um portão que sempre perdoa (ou que
# sempre acusa) provaria o teste igualmente — a distinção por posição só se
# prova comparando as duas.
#
# O sandbox fica num caminho previsível e nada é apagado por trap — faxina
# destrutiva em trap é a linha que limpa a árvore errada no dia em que a
# variável vem vazia.
set -uo pipefail
raiz="$(cd "$(dirname "$0")/../../.." && pwd)"
alvo="$raiz/scripts/gates/gate3_no_comments.sh"
falhas=0

if [ ! -f "$alvo" ]; then
  printf '::error::%s não existe — não há o que medir\n' "$alvo" >&2
  exit 2
fi

tmp="${TMPDIR:-/tmp}/gate3-test-$$"
mkdir -p "$tmp"

# Workaround: the fixtures below write an unmarked comment on purpose —
# that is the case the gate has to flag. Written as literal text, those
# lines would also be an unmarked comment of THIS test file, and measuring
# the tree would count the test itself as debt. `h` makes the "#" only be
# born in the generated file, never in this script's own source.
h='#'

marca_en="$tmp/marca_en.py"
cat > "$marca_en" <<'EOF'
def f():
    x = 1
    # Reason: retries protect against a flaky upstream, not a local bug.
    return x
EOF

marca_pt="$tmp/marca_pt.py"
cat > "$marca_pt" <<'EOF'
def f():
    x = 1
    # motivo: o upstream falha de forma intermitente, não é bug local.
    return x
EOF

sem_marca="$tmp/sem_marca.py"
cat > "$sem_marca" <<EOF
def f():
    x = 1
    $h this retries because the upstream is flaky
    return x
EOF

cabecalho="$tmp/cabecalho.sh"
cat > "$cabecalho" <<EOF
#!/usr/bin/env bash
$h This script backs up the database nightly and rotates old copies.
set -euo pipefail
echo hi
EOF

cabecalho_com_licenca="$tmp/cabecalho_com_licenca.sh"
cat > "$cabecalho_com_licenca" <<EOF
#!/usr/bin/env bash
$h Copyright 2026 the project.
$h Licensed under the terms in LICENSE.

$h This script backs up the database nightly and rotates old copies.
set -euo pipefail
echo hi
EOF

mesmo_texto_no_meio="$tmp/mesmo_texto_no_meio.sh"
cat > "$mesmo_texto_no_meio" <<EOF
#!/usr/bin/env bash
set -euo pipefail
$h This script backs up the database nightly and rotates old copies.
echo hi
EOF

paragrafo_herdado="$tmp/paragrafo_herdado.py"
cat > "$paragrafo_herdado" <<EOF
def f():
    x = 1
    ${h} Reason: retries protect against a flaky upstream, not a local bug.
    ${h}
    ${h} ---- secao decorativa sem marca nenhuma ----
    y = 2
    return x + y
EOF

historia_herdada="$tmp/historia_herdada.py"
cat > "$historia_herdada" <<EOF
def f():
    x = 1
    ${h} Decision: the ceiling is twelve digits.
    ${h}
    ${h} antes era feito de outra forma, mudou na fase 12
    return x
EOF

marca_no_meio_da_frase="$tmp/marca_no_meio_da_frase.py"
cat > "$marca_no_meio_da_frase" <<EOF
def f():
    x = 1
    ${h} I have no idea why this works but for some reason: it does, whatever
    return x
EOF

saida="$(find "$tmp" -type f | bash "$alvo")"

limpo() { # limpo <nome> <arquivo>
  local nome="$1" arquivo="$2"
  if printf '%s\n' "$saida" | grep -qF "$arquivo:"; then
    printf '  FALHA %s — %s foi acusado, e não devia\n' "$nome" "$(basename "$arquivo")"
    falhas=$((falhas + 1))
  else
    printf '  ok    %s\n' "$nome"
  fi
}

acusado() { # acusado <nome> <arquivo> <linha>
  local nome="$1" arquivo="$2" linha="$3"
  if printf '%s\n' "$saida" | grep -qF "$arquivo:$linha:"; then
    printf '  ok    %s\n' "$nome"
  else
    printf '  FALHA %s — esperava %s:%s: na saída\n' "$nome" "$(basename "$arquivo")" "$linha"
    falhas=$((falhas + 1))
  fi
}

limpo "comentário com marca em inglês (Reason:) passa" "$marca_en"
limpo "comentário com marca em português (motivo:) continua passando" "$marca_pt"
acusado "comentário sem marca nenhuma é acusado" "$sem_marca" 3
limpo "cabeçalho de arquivo sem marca passa" "$cabecalho"
limpo "cabeçalho depois de shebang e bloco de licença passa" "$cabecalho_com_licenca"
acusado "o mesmo texto, ao lado de código, é acusado" "$mesmo_texto_no_meio" 3
acusado "parágrafo sem marca depois de linha de comentário vazia é acusado" "$paragrafo_herdado" 5
acusado "nota de histórico não herda a justificativa do parágrafo anterior" "$historia_herdada" 5
acusado "marca no meio da frase não paga o pedágio" "$marca_no_meio_da_frase" 3

if [ "$falhas" -eq 0 ]; then
  printf '\n✓ gate3: reconhece inglês e português, e distingue cabeçalho de comentário ao lado de código.\n'
  exit 0
fi
printf '\n✗ %s caso(s) falharam.\n' "$falhas" >&2
exit 1
