#!/usr/bin/env bash
#
# G7 — o router não monta consulta nem controla transação.
#
# Motivo: `router.py` traduz HTTP; `service.py` decide; a consulta e o commit
# vivem abaixo dele. Quando o router monta o `select` e dá o `commit`, a regra
# de negócio passa a morar junto do código de status, e deixa de ser exercitável
# sem levantar a aplicação inteira — então ninguém escreve o teste da borda.
#
# Limitação deliberada: receber a sessão por dependência (`db: AsyncSession =
# Depends(...)`) e repassá-la ao serviço PASSA. Isso é idioma corrente de
# FastAPI e a fonte primária não o proíbe; o que este portão cobra é a
# construção da consulta e o controle da transação, que são de outra camada.
#
# Escape: `# gate7-ok` na mesma linha, com a razão escrita ao lado.
#
# Recebe a lista de arquivos por stdin. Imprime arquivo:linha:trecho.

set -uo pipefail

while IFS= read -r file || [ -n "$file" ]; do
  [ -f "$file" ] || continue
  case "$file" in
    *_test.py|test_*.py|*/tests/*) continue ;;
    */router.py|*/routers/*.py|*/api.py) ;;
    *) continue ;;
  esac

  # `\bupdate\(` casa `context.update(...)`, que é método de dicionário e não
  # construção de consulta: `\b` vale depois do ponto. As quatro construções do
  # SQLAlchemy passam a exigir que nada de nome venha antes.
  grep -nE '((^|[^.[:alnum:]_])(select|insert|update|delete)\(|session\.(execute|scalar|scalars|add|delete|commit|rollback|refresh|flush)|create_async_engine|async_sessionmaker|(^|[^.[:alnum:]_])sessionmaker\()' "$file" 2>/dev/null |
    while IFS=: read -r line content; do
      case "$content" in *"# gate7-ok"*) continue ;; esac
      printf '%s:%s:%s (router não monta consulta nem controla transação; passe pelo service)\n' \
        "$file" "$line" "$(printf '%s' "$content" | sed 's/^[[:space:]]*//')"
    done
done

exit 0
