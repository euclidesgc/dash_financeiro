#!/usr/bin/env bash
# Portão de lint do projeto. O harness roda em modo processo-apenas e não traz
# pack de Python, então este script é o portão — e ele é chamado à mão antes de
# dar qualquer coisa por pronta, junto de `scripts/gates/gates_runner.sh`.
set -euo pipefail
cd "$(dirname "$0")/.."
exec .venv/bin/ruff check app tests
