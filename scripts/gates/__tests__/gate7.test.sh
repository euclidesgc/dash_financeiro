#!/usr/bin/env bash
# Prova que G7 recusa o router que escreve a própria consulta com o driver
# sqlite3 da biblioteca padrão (execute, commit, texto SQL), sem acusar o
# router que só chama a camada de consulta nem o arquivo que não é router.
#
# Cada caso acusado tem o seu par limpo: um portão que sempre acusa passaria
# nos acusados, e um que nunca acusa passaria nos limpos — só os dois lados
# juntos provam a fronteira.
#
# O sandbox fica num caminho previsível e nada é apagado por trap.
set -uo pipefail
raiz="$(cd "$(dirname "$0")/../../.." && pwd)"
alvo="$raiz/scripts/gates/gate7_layer_boundary.sh"
falhas=0

if [ ! -f "$alvo" ]; then
  printf '::error::%s não existe — não há o que medir\n' "$alvo" >&2
  exit 2
fi

tmp="${TMPDIR:-/tmp}/gate7-test-$$"
mkdir -p "$tmp/app/routers" "$tmp/app/queries"

h='#'

executa="$tmp/app/routers/executa.py"
cat > "$executa" <<EOF
def screen(conn):
    rows = conn.execute(_QUERY).fetchall()
    return rows
EOF

grava="$tmp/app/routers/grava.py"
cat > "$grava" <<EOF
def mark(conn, key):
    dismiss(conn, key)
    conn.commit()
EOF

texto_sql="$tmp/app/routers/texto_sql.py"
cat > "$texto_sql" <<EOF
_COUNT = (
    "SELECT count(*) FROM transactions"
)
EOF

escapado="$tmp/app/routers/escapado.py"
cat > "$escapado" <<EOF
def screen(conn):
    return conn.execute(_QUERY)  ${h} gate7-ok fixture of the escape
EOF

delegado="$tmp/app/routers/delegado.py"
cat > "$delegado" <<EOF
def screen(conn, context):
    context.update(rows=rule_listing(conn))
    return context
EOF

consulta="$tmp/app/queries/consulta.py"
cat > "$consulta" <<EOF
_COUNT = "SELECT count(*) FROM transactions"


def count(conn):
    return conn.execute(_COUNT).fetchone()[0]
EOF

saida="$(find "$tmp" -type f -name '*.py' | bash "$alvo")"

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

acusado "router que chama conn.execute é acusado" "$executa" 2
acusado "router que dá commit é acusado" "$grava" 3
acusado "router que carrega texto SQL é acusado" "$texto_sql" 2
limpo "a marca gate7-ok na linha perdoa" "$escapado"
limpo "router que só chama a camada de consulta passa" "$delegado"
limpo "consulta fora de router passa" "$consulta"

if [ "$falhas" -eq 0 ]; then
  printf '\n✓ gate7: router com consulta ou transação própria é recusado; delegação passa.\n'
  exit 0
fi
printf '\n✗ %s caso(s) falharam.\n' "$falhas" >&2
exit 1
