#!/usr/bin/env bash
#
# Local run behind the single "Executar" entry of .vscode/launch.json:
# prepares the database, serves the API on 127.0.0.1:8000 and the Vite front
# on localhost:5173, opens the panel in the default browser once both answer,
# and stops both when it exits (Ctrl+C, the debug stop button, or either
# server dying).

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

PYTHON="$ROOT/.venv/bin/python"
API_URL=http://127.0.0.1:8000/
FRONT_URL=http://localhost:5173/app/
READY_TIMEOUT_SECONDS=${DASH_DEV_READY_TIMEOUT:-90}

if [ ! -x "$PYTHON" ]; then
  echo "Ambiente Python ausente em .venv. Rode: uv sync" >&2
  exit 1
fi

answers() {
  curl -s -o /dev/null --max-time 2 "$1"
}

for url in "$API_URL" "$FRONT_URL"; do
  if answers "$url"; then
    echo "Já existe um servidor respondendo em $url. Encerre-o antes de executar de novo." >&2
    exit 1
  fi
done

echo "Preparando a base local…"
"$PYTHON" -m app.migrate
"$PYTHON" -m app.auth.seed
"$PYTHON" -m app.ingest

# Reason: job control gives each server its own process group, so the cleanup
# reaches the grandchildren too (pnpm starts Vite as a child and would leave
# it holding port 5173 if only pnpm were killed). A background group that
# reads the terminal is stopped by SIGTTIN, hence stdin from /dev/null.
set -m

pids=()
cleanup() {
  trap - EXIT HUP INT TERM
  for pid in "${pids[@]}"; do
    kill -TERM -- "-$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

"$PYTHON" -m app </dev/null &
pids+=("$!")
# Reason: without strictPort Vite moves to 5174 when 5173 is taken, and the
# browser would open a page nobody serves.
pnpm dev --strictPort </dev/null &
pids+=("$!")

deadline=$((SECONDS + READY_TIMEOUT_SECONDS))
until answers "$API_URL" && answers "$FRONT_URL"; do
  for pid in "${pids[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "Um dos servidores parou antes de responder." >&2
      exit 1
    fi
  done
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "API ou front não responderam em ${READY_TIMEOUT_SECONDS}s." >&2
    exit 1
  fi
  sleep 0.5
done

echo "Painel no ar: $FRONT_URL"
# Reason: the browser goes to a session of its own — started inside this
# terminal's session, a browser that was not yet running would take the
# terminal's hangup when the run stops, and the cleanup above must never
# reach it.
setsid -f xdg-open "$FRONT_URL" >/dev/null 2>&1 || echo "Não consegui abrir o navegador; acesse $FRONT_URL" >&2

set +e
wait -n "${pids[@]}"
status=$?
echo "Um dos servidores parou (código $status); encerrando o outro." >&2
exit "$status"
