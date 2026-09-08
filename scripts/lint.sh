#!/usr/bin/env bash
# Portão de lint do projeto, chamado à mão antes de dar qualquer coisa por
# pronta, junto de `scripts/gates/gates_runner.sh`.
#
# O escopo cobre os três pacotes da aplicação. Enquanto foi só `app tests`, as
# 35 violações de `financas` e `ingestao` ficaram invisíveis por itens inteiros:
# pasta fora do escopo do portão é pasta sem portão.
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/ruff check app financas ingestao tests
.venv/bin/ruff format --check app financas ingestao tests
exec .venv/bin/mypy --strict app financas ingestao
