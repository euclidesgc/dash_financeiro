#!/usr/bin/env bash
# O desenho dos fluxos: nada roda em rascunho, e a nuvem confirma o que a casa
# aprovou.
#
# POR QUE ESTE PORTÃO EXISTE
# O desenho é: o PR nasce rascunho, a iteração acontece na máquina de quem
# trabalha, e o runner remoto é chamado uma vez — quando o trabalho fica pronto
# para revisão. Ele vale nada se um job novo esquecer a guarda: basta um para
# que todo push volte a acender o runner, e ninguém percebe, porque o sintoma é
# a conta no fim do mês.
#
# Duas asserções, e a segunda é a que se esquece:
#   1. todo job de fluxo com `pull_request` tem a guarda de rascunho;
#   2. todo fluxo com `pull_request` declara `ready_for_review` nos `types`.
#
# Sem a segunda, sair do rascunho não dispara evento nenhum e o PR fica pronto e
# sem CI para sempre — que é trocar "roda demais" por "não roda nunca".
#
# `!= true` e não `== false`: em evento de `push` não existe `pull_request`, o
# campo vem nulo, e nulo não é rascunho.
set -uo pipefail

aqui="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$aqui/medir.sh"

RAIZ="$(medir_raiz)"
exige_caminho ".github/workflows" "o diretório de fluxos do GitHub Actions"
DIR="$RAIZ/.github/workflows"
exige_comando python3 "sem ele não há como ler o YAML dos fluxos"
exige_modulo_python yaml "sem PyYAML não há como ler o YAML dos fluxos"

python3 - "$DIR" <<'PY'
import pathlib, sys, yaml

diretorio = pathlib.Path(sys.argv[1])
fluxos = sorted(diretorio.glob("*.yml")) + sorted(diretorio.glob("*.yaml"))
if not fluxos:
    print("::error::nenhum fluxo em .github/workflows — não há o que medir.", file=sys.stderr)
    raise SystemExit(1)

sem_guarda, sem_ready, sem_ordem, medidos, estagios = [], [], [], 0, 0
for f in fluxos:
    try:
        doc = yaml.safe_load(f.read_text()) or {}
    except yaml.YAMLError as erro:
        print(f"::error::{f.name} não é YAML legível ({erro}) — não consegui medir.", file=sys.stderr)
        raise SystemExit(1)

    # `on:` vira booleano True no YAML 1.1, que é como o PyYAML o lê.
    gatilhos = doc.get("on", doc.get(True)) or {}
    if not isinstance(gatilhos, dict) or "pull_request" not in gatilhos:
        continue

    medidos += 1
    pr = gatilhos.get("pull_request") or {}
    tipos = (pr.get("types") if isinstance(pr, dict) else None) or []
    if "ready_for_review" not in tipos:
        sem_ready.append(f.name)

    jobs = doc.get("jobs") or {}
    for nome, job in jobs.items():
        if "github.event.pull_request.draft" not in str((job or {}).get("if", "")):
            sem_guarda.append(f"{f.name}:{nome}")

    # O DESENHO DE DOIS ESTÁGIOS
    #
    # O fluxo que delega para uma suíte reutilizável a chama duas vezes: em casa
    # primeiro, na nuvem depois, e a segunda depende da primeira. Sem o `needs`,
    # as duas rodam em paralelo e a nuvem deixa de ser confirmação para virar
    # cópia — o dobro do custo pelo mesmo veredicto. Sem a ordem, o filtro barato
    # deixa de filtrar.
    casa = {n: j for n, j in jobs.items() if str((j or {}).get("with", {}).get("runner", "")) == "self-hosted"}
    nuvem = {n: j for n, j in jobs.items() if str((j or {}).get("with", {}).get("runner", "")) == "ubuntu-latest"}
    if casa and nuvem:
        estagios += 1
        for n, j in nuvem.items():
            precisa = j.get("needs") or []
            precisa = [precisa] if isinstance(precisa, str) else list(precisa)
            if not any(d in casa for d in precisa):
                sem_ordem.append(f"{f.name}:{n}")
    elif nuvem and not casa:
        sem_ordem.append(f"{f.name}: chama a nuvem sem chamar esta máquina antes")

print(f"medido: {medidos} fluxo(s) com gatilho de pull_request, "
      f"{len(sem_guarda)} job(s) sem a guarda de rascunho, "
      f"{estagios} em dois estágios.")

if sem_guarda:
    print("::error::job sem a guarda de rascunho — ele roda em PR rascunho e "
          "acende o runner a cada push: " + ", ".join(sem_guarda), file=sys.stderr)
    print("Acrescente `if: github.event.pull_request.draft != true` ao job.", file=sys.stderr)
if sem_ready:
    print("::error::fluxo sem `ready_for_review` nos types: " + ", ".join(sem_ready),
          file=sys.stderr)
    print("Sem ele, sair do rascunho não dispara nada e o PR fica pronto e sem CI.",
          file=sys.stderr)
if sem_ordem:
    print("::error::a nuvem não espera esta máquina: " + ", ".join(sem_ordem), file=sys.stderr)
    print("O estágio de nuvem precisa de `needs:` no de casa. Sem isso os dois rodam"
          " em paralelo, e a nuvem deixa de confirmar para virar cópia paga.",
          file=sys.stderr)
raise SystemExit(1 if (sem_guarda or sem_ready or sem_ordem) else 0)
PY
codigo=$?
[ "$codigo" -eq 0 ] && echo "✓ fluxos: nada roda em rascunho, e a nuvem só confirma o que esta máquina aprovou."
exit "$codigo"
