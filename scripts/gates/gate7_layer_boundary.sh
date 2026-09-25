#!/usr/bin/env bash
#
# G7 — the router does not build a query or control a transaction.
#
# Reason: `router.py` translates HTTP; `service.py` decides; the query and
# the commit live below it. When the router builds the `select` and issues
# the `commit`, the business rule ends up living next to the status code, and
# stops being exercisable without booting the whole application — so nobody
# writes the boundary test.
#
# Deliberate limitation: receiving the session by dependency (`db:
# AsyncSession = Depends(...)`) and passing it on to the service PASSES. That
# is FastAPI's current idiom and the primary source does not forbid it; what
# this gate charges is building the query and controlling the transaction,
# which belong to another layer.
#
# The same boundary holds for the standard library driver this project
# uses: a router that calls `conn.execute(...)`, `conn.commit()` or carries
# an SQL string is a screen writing its own query, and the next screen that
# answers the same question writes it again.
#
# Escape: `# gate7-ok` on the same line, with the reason written alongside.
#
# Receives the file list over stdin. Prints file:line:snippet.

set -uo pipefail

while IFS= read -r file || [ -n "$file" ]; do
  [ -f "$file" ] || continue
  case "$file" in
    *_test.py|test_*.py|*/tests/*) continue ;;
    */router.py|*/routers/*.py|*/api.py) ;;
    *) continue ;;
  esac

  # Reason: `\bupdate\(` matches `context.update(...)`, which is a dict
  # method and not query building — `\b` holds after the dot. The four
  # SQLAlchemy constructs then require that no name character comes before.
  grep -nE '((^|[^.[:alnum:]_])(select|insert|update|delete)\(|session\.(execute|scalar|scalars|add|delete|commit|rollback|refresh|flush)|\.(execute|executemany|executescript|commit|rollback)\(|["'"'"'](SELECT|INSERT|UPDATE|DELETE|WITH)[[:space:]]|create_async_engine|async_sessionmaker|(^|[^.[:alnum:]_])sessionmaker\()' "$file" 2>/dev/null |
    while IFS=: read -r line content; do
      case "$content" in *"# gate7-ok"*) continue ;; esac
      printf '%s:%s:%s (router não monta consulta nem controla transação; passe pelo service)\n' \
        "$file" "$line" "$(printf '%s' "$content" | sed 's/^[[:space:]]*//')"
    done
done

exit 0
