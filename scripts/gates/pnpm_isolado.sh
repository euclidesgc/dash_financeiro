#!/usr/bin/env bash
# Toda instalação de pnpm no CI escreve num diretório próprio do job.
#
# POR QUE ESTE PORTÃO EXISTE
# `pnpm/action-setup` grava em `~/setup-pnpm` por padrão. Num runner da nuvem
# isso é inofensivo: a máquina nasce e morre com o job. Nos runners desta casa
# não é — são quatro processos na MESMA máquina, com o MESMO `$HOME`. Dois jobs
# simultâneos instalam e apagam o mesmo diretório, e o segundo morre com
#
#   Error: ENOTEMPTY: directory not empty, rmdir '/home/<quem>/setup-pnpm'
#
# ou, quando a corrida é no outro sentido, com `ENOENT: process.cwd failed ...
# the current working directory was likely removed` — um job apagou o diretório
# de trabalho do outro no meio da execução.
#
# O que torna isto caro é o formato do sintoma: vermelho intermitente, sem
# relação nenhuma com o diff, que some ao reexecutar sozinho. Medido em
# 04/09/2026 em dois runs de `Site`, e o primeiro diagnóstico foi "transitório".
#
# A asserção é uma só: toda referência a `pnpm/action-setup` declara `dest`, e o
# valor não fica sob `~` nem sob `$HOME`. `runner.temp` é próprio de cada job, e
# o runner o limpa sozinho.
set -uo pipefail

aqui="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$aqui/medir.sh"

RAIZ="$(medir_raiz)"
exige_caminho ".github/workflows" "o diretório de fluxos do GitHub Actions"
exige_comando python3 "sem ele não há como ler o YAML dos fluxos"
exige_modulo_python yaml "sem PyYAML não há como ler o YAML dos fluxos"

python3 - "$RAIZ/.github/workflows" <<'PY'
import pathlib, sys, yaml

diretorio = pathlib.Path(sys.argv[1])
fluxos = sorted(diretorio.glob("*.yml")) + sorted(diretorio.glob("*.yaml"))
if not fluxos:
    print("::error::nenhum fluxo em .github/workflows — não há o que medir.", file=sys.stderr)
    raise SystemExit(1)

# O CASO DO VAZIO É EXPLÍCITO, E NÃO É O MESMO QUE O CASO DO ILEGÍVEL
# Um repositório pode legitimamente não usar a ação, e aí não há o que reprovar.
# O que ele não pode é passar por não ter conseguido ler o YAML.
referencias, sem_dest, sob_home = 0, [], []

for f in fluxos:
    try:
        doc = yaml.safe_load(f.read_text()) or {}
    except yaml.YAMLError as erro:
        print(f"::error::{f.name} não é YAML legível ({erro}) — não consegui medir.", file=sys.stderr)
        raise SystemExit(1)

    for nome_job, job in (doc.get("jobs") or {}).items():
        for i, passo in enumerate((job or {}).get("steps") or []):
            usa = str((passo or {}).get("uses", ""))
            if not usa.startswith("pnpm/action-setup@"):
                continue
            referencias += 1
            onde = f"{f.name}:{nome_job}[{i}]"
            destino = ((passo.get("with") or {}).get("dest"))
            if destino is None:
                sem_dest.append(onde)
            elif str(destino).lstrip().startswith(("~", "$HOME", "${HOME}")):
                sob_home.append(f"{onde} -> {destino}")

print(f"medido: {referencias} referência(s) a pnpm/action-setup em {len(fluxos)} fluxo(s), "
      f"{len(sem_dest)} sem `dest` e {len(sob_home)} apontando para dentro do HOME.")

if sem_dest:
    print("::error::pnpm/action-setup sem `dest`: " + ", ".join(sem_dest), file=sys.stderr)
    print("Sem `dest` a ação usa `~/setup-pnpm`, que é compartilhado por todos os", file=sys.stderr)
    print("runners desta máquina. Declare `dest: ${{ runner.temp }}/setup-pnpm`.", file=sys.stderr)
if sob_home:
    print("::error::`dest` dentro do HOME: " + ", ".join(sob_home), file=sys.stderr)
    print("O HOME é o que os runners compartilham — é exatamente o que este portão", file=sys.stderr)
    print("existe para impedir. Use `runner.temp`, que é próprio de cada job.", file=sys.stderr)
raise SystemExit(1 if (sem_dest or sob_home) else 0)
PY
codigo=$?
[ "$codigo" -eq 0 ] && echo "✓ pnpm isolado: nenhuma instalação de pnpm escreve no HOME compartilhado dos runners."
exit "$codigo"
