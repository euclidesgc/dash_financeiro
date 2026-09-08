#!/usr/bin/env bash
#
# Captura várias telas numa só subida do painel.
#
# POR QUE ELE EXISTE
# `scripts/capturas.mjs` captura uma tela por chamada, e cada chamada de quem o
# usava subia um servidor, fazia um login e o matava. Numa entrega que toca seis
# telas isso é seis subidas e seis logins — e o limitador de tentativas de login
# fecha a porta antes da sexta, então a última captura sai da tela de login sem
# que ninguém perceba. Aqui o servidor sobe uma vez, o login acontece uma vez, e
# o cookie é reusado por todas as telas.
#
# Uso:
#   bash scripts/capturas-em-lote.sh --item 024-cartoes-como-entidade \
#     --telas 'configuracao=/configuracao;dividas=/dividas' \
#     [--larguras 375,768,1440] [--escuro 1440] [--porta 8123] [--data 2026-09-05]
#
# `--telas` é `nome=caminho` separado por `;`. O nome vira o do arquivo; o
# caminho é o da rota, com query string se precisar.
set -euo pipefail
cd "$(dirname "$0")/.."

ITEM=""; TELAS=""; LARGURAS="375,768,1440"; ESCURO="1440"; PORTA="8123"; DATA="2026-09-05"
while [ $# -gt 0 ]; do
  case "$1" in
    --item) ITEM="$2"; shift 2 ;;
    --telas) TELAS="$2"; shift 2 ;;
    --larguras) LARGURAS="$2"; shift 2 ;;
    --escuro) ESCURO="$2"; shift 2 ;;
    --porta) PORTA="$2"; shift 2 ;;
    --data) DATA="$2"; shift 2 ;;
    *) echo "argumento desconhecido: $1" >&2; exit 2 ;;
  esac
done
[ -n "$ITEM" ] && [ -n "$TELAS" ] || { echo "faltam --item e --telas" >&2; exit 2; }

TRABALHO="$(mktemp -d)"
SERVIDOR=""

encerra() {
  if [ -n "$SERVIDOR" ]; then
    kill "$SERVIDOR" 2>/dev/null || true
    # Reason: an orphan holding the port makes the next capture photograph
    # the previous panel.
    wait "$SERVIDOR" 2>/dev/null || true
  fi
  rm -rf -- "$TRABALHO"
}
trap encerra EXIT

export DASH_ENV_FILE=/dev/null
export DASH_DB_PATH="$TRABALHO/dash.sqlite"
export DASH_TODAY="$DATA"
export SESSION_SECRET="captura-em-lote"
export LOGIN="dono"
export PASSWORD="captura-em-lote"

# Reason: this copies the real base when it exists — the capture has to show
# the panel the owner sees, and an empty base photographs screens with no
# numbers at all. The copy is temporary and disappears at the end — the
# owner's base is never opened by the capture server, so nothing the capture
# does reaches it.
[ -f data/dash.sqlite ] && cp data/dash.sqlite "$DASH_DB_PATH"

.venv/bin/python -m app.migrate >"$TRABALHO/migracao.log" 2>&1
.venv/bin/python -m app.auth.seed >"$TRABALHO/usuario.log" 2>&1

setsid .venv/bin/python -m uvicorn app.main:create_app --factory \
  --host 127.0.0.1 --port "$PORTA" --log-level warning >"$TRABALHO/servidor.log" 2>&1 &
SERVIDOR=$!

pronto=0
for _ in $(seq 1 60); do
  if [ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORTA/login" || true)" = "200" ]; then
    pronto=1; break
  fi
  sleep 0.5
done
[ "$pronto" = "1" ] || { echo "o painel não respondeu em /login"; cat "$TRABALHO/servidor.log"; exit 1; }

# Reason: one login per server — the rate limiter counts attempts per IP,
# and on a loopback bind every client is the same IP.
COOKIE=$(curl -s -i -X POST "http://127.0.0.1:$PORTA/login" \
  -d "login=$LOGIN" -d "senha=$PASSWORD" \
  | grep -i '^set-cookie: dash_session=' | head -1 | sed 's/^[Ss]et-[Cc]ookie: //; s/;.*//')
[ -n "$COOKIE" ] || { echo "o login não devolveu cookie de sessão"; exit 1; }

capturadas=0
IFS=';' read -ra PARES <<< "$TELAS"
for par in "${PARES[@]}"; do
  nome="${par%%=*}"; caminho="${par#*=}"
  [ -n "$nome" ] && [ -n "$caminho" ] || { echo "tela mal escrita: $par" >&2; exit 2; }
  node scripts/capturas.mjs --item "$ITEM" --url "http://127.0.0.1:$PORTA$caminho" \
    --nome "$nome" --larguras "$LARGURAS" --escuro "$ESCURO" --cookie "$COOKIE"
  capturadas=$((capturadas + 1))
done

echo "capturas em lote: $capturadas tela(s), uma subida, um login, referência $DATA"
