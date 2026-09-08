#!/usr/bin/env bash
#
# Dispatcher dos gates arquiteturais.
#
# Lê `.harness/gates.json` (escrito pelo init a partir dos manifestos de pack),
# roda cada gate declarado e decide o veredicto conforme o modo do projeto:
#
#   greenfield  — tolerância zero: qualquer violação reprova.
#   brownfield  — avalia só o diff, e compara com a baseline de dívida: uma
#                 violação que já existia não reprova; uma nova, sim.
#
# A razão do modo brownfield é simples: um projeto existente tem dívida que o
# harness não criou, e reprovar o repositório inteiro no dia um leva o dev a
# desligar os gates — o que é pior que não tê-los, porque some com o sinal.
#
# Cada gate é um script independente que recebe a lista de arquivos por stdin
# e imprime uma linha por violação, no formato `arquivo:linha:trecho`.
#
# Modos:
#   gates_runner.sh                roda os gates e reprova conforme o modo
#   gates_runner.sh --diff-only    força avaliação apenas do diff
#   gates_runner.sh --all          força avaliação da árvore inteira
#   gates_runner.sh --count-json   imprime a contagem por gate/arquivo (baseline)
#   gates_runner.sh --baseline     grava a contagem atual como nova baseline

set -uo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" || exit 0

GATES_CONFIG="$ROOT/.harness/gates.json"
CONFIG="$ROOT/.harness/config.json"

[ -f "$GATES_CONFIG" ] || { echo "sem .harness/gates.json — nada a cobrar"; exit 0; }

MODE="auto"
for arg in "$@"; do
  case "$arg" in
    --diff-only) MODE="diff" ;;
    --all) MODE="all" ;;
    --count-json) MODE="count" ;;
    --baseline) MODE="baseline" ;;
  esac
done

python3 - "$ROOT" "$MODE" <<'PYTHON'
import json
import os
import subprocess
import sys

root, mode = sys.argv[1], sys.argv[2]

def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError, ValueError):
        return default

gates = read_json(os.path.join(root, ".harness", "gates.json"), {}).get("gates") or []
config = read_json(os.path.join(root, ".harness", "config.json"), {})
brownfield = (config.get("brownfield") or {})
baseline_rel = brownfield.get("baseline_file") or ".harness/gate-baseline.json"
baseline_path = os.path.join(root, baseline_rel)
baseline = read_json(baseline_path, {})
is_brownfield = config.get("route") == "brownfield" and os.path.isfile(baseline_path)


def fnmatch_any(path, patterns):
    import fnmatch
    for pattern in patterns or []:
        if fnmatch.fnmatch(path, pattern):
            return True
        if pattern.endswith("/**") and (path == pattern[:-3] or path.startswith(pattern[:-3] + "/")):
            return True
    return False


def tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True)
    # Reason: outside a repository the command exits non-zero and the list
    # comes back empty. An empty universe walked every gate finding nothing
    # and printed "0 file(s) considered" with exit code 0: the gate did not
    # measure and said it was clean. A gate that failed to measure fails,
    # never passes.
    if out.returncode != 0:
        return None
    return [line for line in out.stdout.splitlines() if line]


def configured_branches():
    """Os nomes que o projeto declarou, não os que o harness supunha.

    `origin/develop` e `origin/main` eram literais aqui. Num repositório com
    outra nomenclatura os dois falham, a cascata cai em `HEAD~1`, e o gate passa
    a cobrar o diff contra o commit anterior em vez do ponto de partida da fase.
    Ele continua verde, e é por isso que ninguém percebe.
    """
    nomes = [(config.get("branches") or {}).get(papel) for papel in ("integracao", "producao")]
    return [n for n in dict.fromkeys(n for n in nomes if n)]


def linhas_acrescentadas(base):
    # Reason: a diff-mode gate that judges the whole file fails every old
    # comment of any file someone so much as touches — and a gate that
    # accuses what the change did not do is a gate that gets switched off.
    # The cutout is by new line.
    saida = subprocess.run(
        ["git", "diff", "--unified=0", "--diff-filter=ACMR", f"{base}...HEAD"],
        cwd=root, capture_output=True, text=True,
    )
    if saida.returncode != 0:
        return None
    por_arquivo, atual = {}, None
    for linha in saida.stdout.splitlines():
        if linha.startswith("+++ b/"):
            atual = linha[6:]
            por_arquivo.setdefault(atual, set())
        elif linha.startswith("@@") and atual is not None:
            cabeca = linha.split("+", 1)[1].split("@@")[0].strip()
            inicio, _, quantas = cabeca.partition(",")
            inicio, quantas = int(inicio), int(quantas or 1)
            por_arquivo[atual].update(range(inicio, inicio + quantas))
    return por_arquivo


def mudancas_desde(base):
    saida = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"],
        cwd=root, capture_output=True, text=True,
    )
    if saida.returncode != 0:
        return changed_files() or []
    return [linha for linha in saida.stdout.splitlines() if linha]


def changed_files():
    base = os.environ.get("HARNESS_DIFF_BASE", "")
    if base:
        ranges = [base]
    else:
        # Reason: the local branch comes before the remote one — in a
        # repository with no remote, `origin/develop` does not resolve, the
        # cascade falls to `HEAD~1`, and a merge of the integration branch
        # makes the diff accuse everything it brought in — another phase's
        # work judged as if it were this one's.
        declaradas = [
            faixa
            for nome in configured_branches()
            for faixa in (f"origin/{nome}...HEAD", f"{nome}...HEAD")
        ]
        # Reason: the old cascade stays at the end as a last resort, so a
        # project that has not declared anything yet keeps working the way it
        # used to.
        ranges = declaradas + ["origin/develop...HEAD", "origin/main...HEAD", "HEAD~1"]
    for candidate in ranges:
        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", candidate],
            cwd=root, capture_output=True, text=True,
        )
        if out.returncode == 0:
            files = [line for line in out.stdout.splitlines() if line]
            if files:
                return files
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
        cwd=root, capture_output=True, text=True,
    )
    return [line for line in out.stdout.splitlines() if line]


def exige_medicao(arquivos, motivo):
    if arquivos is None:
        print(
            f"✗ gates: não foi possível medir — {motivo}. "
            "Portão que não conseguiu medir reprova, nunca aprova.",
            file=sys.stderr,
        )
        sys.exit(1)
    return arquivos


use_diff = mode == "diff" or (mode == "auto" and is_brownfield)
universe = changed_files() if use_diff else exige_medicao(
    tracked_files(), "`git ls-files` falhou: isto não é um repositório git"
)
if mode in ("count", "baseline"):
    universe = exige_medicao(
        tracked_files(), "`git ls-files` falhou: isto não é um repositório git"
    )
if not use_diff and not universe:
    print(
        "✗ gates: não foi possível medir — o repositório não tem arquivo rastreado. "
        "Portão que não conseguiu medir reprova, nunca aprova.",
        file=sys.stderr,
    )
    sys.exit(1)

resultados = {}
falhou = False
linhas_saida = []

nao_mediu = []

for gate in gates:
    gate_id = gate.get("id") or "?"
    script = gate.get("script") or ""
    script_path = script if os.path.isabs(script) else os.path.join(root, script)
    if not os.path.isfile(script_path):
        linhas_saida.append(f"  [{gate_id}] script ausente: {script} — gate não cobrado")
        continue

    # Reason: a gate can declare `"modo": "diff"` to cover only what the
    # change touched. It serves the rule that is born after the code: the
    # project adopts the convention from here on and schedules retroactive
    # adoption as an item, instead of failing fifteen already-shipped items or
    # switching the gate off.
    escopo_gate = universe
    recorte_linhas = None
    if gate.get("modo") == "diff" and not use_diff:
        # Reason: `desde` fixes the boundary of a rule born after the code —
        # what was written before it is a roadmap item, not debt for whoever
        # writes now. Without it, the integration branch compares against
        # production and charges the convention against everything already
        # there.
        desde = gate.get("desde")
        if desde:
            escopo_gate = mudancas_desde(desde)
            recorte_linhas = linhas_acrescentadas(desde)
        else:
            escopo_gate = changed_files() or []
    alvos = [
        f for f in escopo_gate
        if fnmatch_any(f, gate.get("applies_to") or ["**"])
        and not fnmatch_any(f, gate.get("exempt") or [])
        and os.path.isfile(os.path.join(root, f))
    ]
    if not alvos and gate.get("modo") == "diff":
        linhas_saida.append(f"  [{gate_id}] modo diff: a mudança não tocou arquivo que ele cobra")
        continue
    if not alvos:
        # Reason: a gate with no target is a gate that did not measure, and it
        # used to leave quietly with the round's green verdict — that is how
        # G3, G4 and G7 once passed whole items pointing at a folder this
        # project does not have.
        linhas_saida.append(
            f"  [{gate_id}] nenhum arquivo casou applies_to={gate.get('applies_to')} "
            f"sobre {len(universe)} arquivo(s) — o portão não mediu"
        )
        nao_mediu.append(gate_id)
        continue

    proc = subprocess.run(
        ["bash", script_path],
        cwd=root,
        input="\n".join(alvos) + "\n",
        capture_output=True,
        text=True,
    )
    violacoes = [line for line in proc.stdout.splitlines() if line.strip()]
    if recorte_linhas is not None:
        mantidas = []
        for violacao in violacoes:
            arquivo, _, resto = violacao.partition(":")
            numero, _, _ = resto.partition(":")
            arquivo = arquivo.strip()
            if not numero.isdigit() or int(numero) in recorte_linhas.get(arquivo, set()):
                mantidas.append(violacao)
        violacoes = mantidas

    por_arquivo = {}
    for violacao in violacoes:
        arquivo = violacao.split(":", 1)[0]
        por_arquivo[arquivo] = por_arquivo.get(arquivo, 0) + 1
    if por_arquivo:
        # Reason: different packs share a gate identifier (G3 and G4 apply to
        # all three). Overwriting here would erase the debt tolerated by the
        # other front, and the dev would see hundreds of violations nobody
        # introduced. The file sets are disjoint: each gate only ever sees its
        # own front's path.
        acumulado = resultados.setdefault(gate_id, {})
        for arquivo, contagem in por_arquivo.items():
            acumulado[arquivo] = max(acumulado.get(arquivo, 0), contagem)

    if mode in ("count", "baseline"):
        continue

    tolerado_gate = baseline.get(gate_id) or {} if is_brownfield else {}
    for violacao in violacoes:
        arquivo = violacao.split(":", 1)[0]
        if por_arquivo.get(arquivo, 0) <= tolerado_gate.get(arquivo, 0):
            continue
        linhas_saida.append(f"  [{gate_id}] {violacao}")
        falhou = True

if mode == "count":
    print(json.dumps(resultados, indent=2, ensure_ascii=False))
    sys.exit(0)

if mode == "baseline":
    resultados["generated_at"] = subprocess.run(
        ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True
    ).stdout.strip()
    os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
    with open(baseline_path, "w", encoding="utf-8") as handle:
        json.dump(resultados, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    total = sum(len(v) for k, v in resultados.items() if isinstance(v, dict))
    print(f"✓ baseline gravada em {baseline_rel}: {total} arquivo(s) com dívida tolerada")
    sys.exit(0)

escopo = "diff" if use_diff else "árvore completa"
if falhou:
    print("\n".join(linhas_saida))
    print("")
    print(f"✗ gates: violação(ões) acima ({escopo}).")
    print("  Corrija, ou justifique na própria linha com o escape do gate")
    print("  (`gateN-ok: <motivo>` no comentário da linguagem) — escape sem motivo")
    print("  real é achado de revisão.")
    sys.exit(1)

if linhas_saida:
    print("\n".join(linhas_saida))
if nao_mediu:
    print("\n".join(linhas_saida))
    print(
        f"✗ gates: {', '.join(nao_mediu)} não mediu arquivo nenhum ({escopo}). "
        "Portão que não conseguiu medir reprova, nunca aprova."
    )
    raise SystemExit(1)
print(f"✓ gates: limpos ({escopo}, {len(universe)} arquivo(s) considerados).")
sys.exit(0)
PYTHON
