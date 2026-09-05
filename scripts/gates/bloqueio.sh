#!/usr/bin/env bash
#
# Um rótulo `blocked-on-*` reprova o merge.
#
# A CAUSA RAIZ QUE ISTO EXISTE PARA MATAR
#
# A verificação morava embutida no YAML e lia os rótulos assim:
#
#   printf '%s' "$ROTULOS" | tr -d '[]"' | tr ',' '\n' | grep '^blocked-on-'
#
# O `toJSON` do GitHub entrega JSON **indentado**, em várias linhas:
#
#   [
#     "blocked-on-D-011"
#   ]
#
# Depois do `tr`, a linha é `  blocked-on-D-011`, com dois espaços na frente, e
# a âncora `^` do grep não casa. O predicado respondeu "nenhum bloqueio" para um
# PR rotulado, e respondeu isso desde o primeiro dia: a trava que o protocolo de
# divergência anunciava nunca existiu. É o mesmo defeito que `medir.sh` persegue
# — não conseguir medir e não achar produziram a mesma resposta.
#
# A leitura passa a ser de um analisador de JSON de verdade, e a ausência da
# variável reprova em vez de aprovar: um PR cujos rótulos não chegaram é um PR
# que ninguém mediu.
#
# Lê os rótulos de `ROTULOS` (JSON, como `toJSON(...labels.*.name)` entrega).
# Sai 0 quando não há bloqueio, 1 quando há ou quando não conseguiu medir.

set -uo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/medir.sh"

exige_comando python3

if [ -z "${ROTULOS+definida}" ]; then
  _reprova "a variável ROTULOS não chegou — sem ela não há como saber se o PR está travado"
fi

rotulos="$(printf '%s' "$ROTULOS" | python3 -c '
import json
import sys

try:
    nomes = json.load(sys.stdin)
except (ValueError, TypeError):
    sys.exit(2)
if not isinstance(nomes, list) or any(not isinstance(n, str) for n in nomes):
    sys.exit(2)
print(len(nomes))
for nome in nomes:
    if nome.strip().startswith("blocked-on-"):
        print(nome.strip())
')" || _reprova "ROTULOS não é uma lista JSON de nomes: $(printf '%s' "$ROTULOS" | tr '\n' ' ')"

total="$(printf '%s' "$rotulos" | head -n 1)"
bloqueios="$(printf '%s' "$rotulos" | tail -n +2)"

printf 'medido: %s rótulo(s) no PR\n' "$total"

if [ -z "$bloqueios" ]; then
  echo "Nenhum bloqueio pendente."
  exit 0
fi

printf '::error::Este PR está travado por: %s\n' "$(printf '%s' "$bloqueios" | tr '\n' ' ')"
echo ""
echo "A trava sai quando a pendência for resolvida de fato — não quando alguém"
echo "tirar o rótulo. Se a solução vem no futuro, ela precisa de item no roadmap,"
echo "na posição de precedência certa, e o merge espera esse item entregar."
exit 1
