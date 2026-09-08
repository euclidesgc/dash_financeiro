#!/usr/bin/env bash
# Recusa mergear um PR que tenha bloqueio pendente, verificação vermelha — ou
# cuja situação este script não tenha conseguido medir.
#
#   merge-se-liberado.sh <numero-do-pr> [--squash|--merge|--rebase]
#
# gate3-ok: os dois parágrafos abaixo são o porquê de o script existir, não a
# mecânica.
#
# POR QUE ELE EXISTE
# O rótulo `blocked-on-*` deveria ser tranca, e o workflow `harness.yml` o faz
# reprovar. Mas verificação obrigatória exige plano pago em repositório
# privado, e sem isso o botão de merge continua clicável com a verificação
# vermelha. A tranca então mora aqui: no ator que mergeia. Vale para quem roda
# à mão e para o motor autônomo, que é quem mergeia de madrugada.
#
# POR QUE ELE MEDE ANTES DE DECIDIR
# A primeira versão lia cada resposta do `gh` com `2>/dev/null` e decidia pela
# saída. Numa rede fora do ar a saída vem vazia, e vazio dizia "sem rótulo de
# bloqueio", "sem check vermelho" e "a pilha inteira está limpa" — a tranca
# aprovava justamente quando tinha menos informação para aprovar. É o mesmo
# defeito que `medir.sh` existe para matar, dentro do script que é a última
# linha de defesa antes do merge. A regra aqui é a mesma: **não conseguir
# medir é recusa, nunca liberação.**
#
# Toda chamada de rede tem teto de tempo. Espera sem teto não é espera, é
# travamento — e um motor autônomo travado às três da manhã perde a noite sem
# que nada acuse.
set -uo pipefail

TETO="${MERGE_TETO_SEGUNDOS:-30}"
# Reason: ceiling for waiting on a pending check. Separate from the network
# ceiling — that one measures whether GitHub answers, this one measures how
# long to wait for a CI that is still running.
ESPERA="${MERGE_ESPERA_SEGUNDOS:-1200}"
# Reason: how often it re-reads. Separate from the ceiling so the test can
# measure the verdict without waiting for the production interval.
INTERVALO="${MERGE_INTERVALO_SEGUNDOS:-20}"

pr="${1:-}"
metodo="${2:---squash}"
[ -n "$pr" ] || { printf 'uso: merge-se-liberado.sh <numero-do-pr> [--squash|--merge|--rebase]\n' >&2; exit 2; }
case "$pr" in ''|*[!0-9]*) printf 'RECUSADO: "%s" não é número de PR.\n' "$pr" >&2; exit 2 ;; esac

command -v gh >/dev/null 2>&1 || { printf 'gh não encontrado.\n' >&2; exit 2; }
command -v timeout >/dev/null 2>&1 || { printf 'timeout não encontrado: sem ele não há teto de tempo, e sem teto não há tranca.\n' >&2; exit 2; }

nao_mediu() {
  printf 'RECUSADO por impossibilidade de medição, não por resultado.\n' >&2
  printf '  %s\n' "$1" >&2
  printf 'Uma tranca que libera quando não consegue medir não é tranca. Verifique a\n' >&2
  printf 'conexão e a autenticação do gh, e rode de novo.\n' >&2
  exit 1
}

# Reason: the result comes out through `$MEDIDO`, not stdout, because `mede`
# needs to be able to end the script when it fails to measure. An `exit`
# inside `$( )` only ends the substitution's subshell — the script would
# carry on with the variable empty, which is exactly the reading of empty as
# an answer this rewrite exists to end. Called directly, the `exit` holds.
MEDIDO=""

mede() {
  local desc="$1"; shift
  local err saida rc detalhe
  err="$(mktemp)"
  saida="$(timeout "$TETO" "$@" 2>"$err")"; rc=$?
  detalhe="$(head -c 300 "$err" | tr '\n' ' ')"
  rm -f "$err"
  [ "$rc" -eq 124 ] && nao_mediu "$desc: nada respondeu em ${TETO}s."
  [ "$rc" -eq 0 ] || nao_mediu "$desc: o comando saiu $rc. ${detalhe:-sem detalhe}"
  MEDIDO="$saida"
}

# Reason: `gh pr checks` exits 1 when there is a red check and 8 when there
# is a pending one — both are a successful measurement, and treating them as
# failure would lock out every legitimate PR. 2 (PR does not exist) and any
# transport error are a failed measurement instead.
mede_checks() {
  local err saida rc detalhe
  err="$(mktemp)"
  saida="$(timeout "$TETO" gh pr checks "$1" 2>"$err")"; rc=$?
  detalhe="$(head -c 300 "$err" | tr '\n' ' ')"
  rm -f "$err"
  case "$rc" in
    0|1|8) ;;
    124) nao_mediu "checks do PR #$1: nada respondeu em ${TETO}s." ;;
    *) nao_mediu "checks do PR #$1: o comando saiu $rc. ${detalhe:-sem detalhe}" ;;
  esac
  MEDIDO="$saida"
}

# Reason: pending is not green, because the first version only refused a
# `fail` check. A PR whose checks are still running has no `fail` at all — it
# has four `pending` — so it passed, and the merge happened before CI said
# anything at all. It is the same shape of failure this file's header
# describes: the absence of red read as green, when the right reading was
# *not yet measured*. On a night of thirty merges, that is thirty merges with
# no CI. It waits up to $ESPERA seconds and refuses whatever is still
# pending. Refusing immediately would lock out every legitimate PR, because
# CI always starts pending. Empty and pending are the same thing: measurement
# did not finish. The empty list has two readings — "this repository has no
# CI" and "the suites have not shown up yet" — and right after a push it is
# always the second: GitHub takes seconds to register the checks. Refusing on
# the first empty reading refuses every freshly pushed PR, which happened
# with a force-push this very morning, six seconds before the four suites
# appeared. Both wait for the same reason and the same length of time. What
# tells them apart is what the wait reveals: whoever had CI shows the suites,
# whoever did not stays empty until the ceiling — and then the refusal is
# about a fact, not about a moment.
espera_checks() {
  local alvo="$1" inicio agora pendentes vazio
  inicio="$(date +%s)"
  while :; do
    mede_checks "$alvo"
    vazio=0
    [ -z "$(printf '%s' "$MEDIDO" | tr -d '[:space:]')" ] && vazio=1
    pendentes="$(printf '%s\n' "$MEDIDO" | awk -F'\t' '$2=="pending"{print $1}')"
    [ "$vazio" -eq 0 ] && [ -z "$pendentes" ] && return 0

    agora="$(date +%s)"
    if [ "$((agora - inicio))" -ge "$ESPERA" ]; then
      # Reason: the empty list after the ceiling is judged outside here,
      # together with the `MERGE_SEM_CI` output — here it only decides that
      # the wait is over.
      [ "$vazio" -eq 1 ] && return 0
      printf 'RECUSADO: o PR #%s ainda tem verificação pendente depois de %ss:\n' "$alvo" "$ESPERA" >&2
      printf '%s\n' "$pendentes" | sed 's/^/  /' >&2
      printf 'Pendente não é verde. Espere o CI terminar, ou aumente MERGE_ESPERA_SEGUNDOS\n' >&2
      printf 'quando souber por que aquela suite demora.\n' >&2
      exit 1
    fi

    if [ "$vazio" -eq 1 ]; then
      printf 'aguardando as verificações do PR #%s aparecerem...\n' "$alvo" >&2
    else
      printf 'aguardando %s verificação(ões) do PR #%s...\n' "$(printf '%s\n' "$pendentes" | wc -l | tr -d ' ')" "$alvo" >&2
    fi
    sleep "$INTERVALO"
  done
}

mede "rótulos do PR #$pr" gh pr view "$pr" --json labels --jq '.labels[].name'
rotulos="$MEDIDO"
bloqueios="$(printf '%s\n' "$rotulos" | grep '^blocked-on-' || true)"
if [ -n "$bloqueios" ]; then
  printf 'RECUSADO: o PR #%s está travado por: %s\n' "$pr" "$(printf '%s' "$bloqueios" | tr '\n' ' ')" >&2
  printf 'A trava sai quando a divergência for ratificada por um humano, nunca quando alguém tirar o rótulo.\n' >&2
  exit 1
fi

# Reason: this is the most common cause of "no checks" on a stack. A
# `pull_request` workflow runs on the **merge commit** GitHub computes
# between head and base. When that merge cannot be computed,
# `refs/pull/N/merge` does not exist and **no run is ever created** — it
# neither fails nor stays pending: it is simply not created. `mergeable`
# stays `UNKNOWN` forever and the PR just looks "still without CI". On a
# stack this happens without anyone touching the PR on top: it only takes
# the **base** going into conflict — the trunk moved, and the PR below went
# `DIRTY`. The top silently loses its CI, the blind verdict fails the
# criterion that depends on CI for failing to measure, and the escalation
# points at the criterion, which is not at fault. Measured twice in the same
# run, on 2026-09-04, in the same shape. This function decides nothing: it
# only reports what it measured, once the refusal has already happened.
# Diagnosis is cheap; finding the upstream cause at three in the morning is
# not.
diagnostica_merge_ref() {
  local alvo="$1" base estado mergeavel linha
  linha="$(gh pr view "$alvo" --json baseRefName,mergeable,mergeStateStatus \
    --jq '[.baseRefName, .mergeable, .mergeStateStatus] | @tsv' 2>/dev/null || true)"
  [ -n "$linha" ] || return 0
  IFS="$(printf '\t')" read -r base mergeavel estado <<DIAG
$linha
DIAG
  [ "$mergeavel" = "UNKNOWN" ] || [ "$mergeavel" = "CONFLICTING" ] || return 0

  printf '\ndiagnóstico: o PR #%s está com mergeable=%s (estado %s), e um fluxo de\n' \
    "$alvo" "$mergeavel" "$estado" >&2
  printf '  pull_request roda sobre o merge commit — sem ele, nenhum run é criado.\n' >&2
  printf '  A base dele é `%s`.\n' "$base" >&2

  local base_pr base_estado
  base_pr="$(gh pr list --head "$base" --state open --json number --jq '.[0].number' 2>/dev/null || true)"
  if [ -n "$base_pr" ] && [ "$base_pr" != "null" ]; then
    base_estado="$(gh pr view "$base_pr" --json mergeStateStatus --jq .mergeStateStatus 2>/dev/null || true)"
    printf '  A base é o PR #%s, em estado %s.\n' "$base_pr" "$base_estado" >&2
    if [ "$base_estado" = "DIRTY" ]; then
      printf '  É ISTO: resolva o conflito do PR #%s com o trunk, e o CI do #%s volta\n' \
        "$base_pr" "$alvo" >&2
      printf '  sozinho. O critério que depende do CI não tem defeito nenhum.\n' >&2
      return 0
    fi
  fi
  printf '  Confira se a base ainda existe e se o merge com ela é calculável.\n' >&2
}

espera_checks "$pr"
# Reason: no check is not a green check. `gh pr checks` returns empty when
# the PR has no suite at all, and the naive reading of that is "no red
# check". It is the purest form of the defect this whole script exists to
# kill. It happened on a real project: Actions stopped running because of a
# quota, two PRs went to closing with no `github-actions` suite at all, and
# nothing in the process asked — the blind verdict measures the criterion,
# `check` measures coherence, and the global DoD is "from CI", which is
# exactly the part nobody checks actually happened. `MERGE_SEM_CI=1` exists
# for the repository that legitimately has no CI, and it is deliberate:
# whoever uses it is declaring that they know.
if [ -z "$(printf '%s' "$MEDIDO" | tr -d '[:space:]')" ]; then
  if [ "${MERGE_SEM_CI:-0}" = "1" ]; then
    printf 'aviso: o PR #%s não tem verificação nenhuma, e MERGE_SEM_CI=1 mandou seguir.\n' "$pr" >&2
  else
    printf 'RECUSADO: o PR #%s não tem verificação nenhuma depois de %ss de espera.\n' "$pr" "$ESPERA" >&2
    printf 'Nenhum check não é o mesmo que nenhum check vermelho: pode ser CI que não\n' >&2
    printf 'disparou, cota esgotada, fluxo desabilitado ou filtro de caminho. Veja a aba\n' >&2
    printf 'Actions antes de decidir. Se este repositório realmente não tem CI, declare\n' >&2
    printf 'com MERGE_SEM_CI=1.\n' >&2
    diagnostica_merge_ref "$pr"
    exit 1
  fi
fi

vermelhos="$(printf '%s\n' "$MEDIDO" | awk -F'\t' '$2=="fail"{print $1}')"
if [ -n "$vermelhos" ]; then
  printf 'RECUSADO: o PR #%s tem verificação vermelha:\n' "$pr" >&2
  printf '%s\n' "$vermelhos" | sed 's/^/  /' >&2
  exit 1
fi

# Reason: the preconditions are measured together because `mergeStateStatus`
# answers what GitHub thinks of the **branch** — conflict, protection,
# checks. It says `CLEAN` for a draft PR and for one already closed, and the
# merge of either is refused all the same. Any precondition left out here
# would cost the same night: the lock prints "released", `gh` answers `Pull
# Request is still a draft`, and nobody is reading at three in the morning.
# They are measured together, in a single call, and each refusal is named.
mede "pré-condições de merge do PR #$pr" \
  gh pr view "$pr" --json isDraft,state,mergeStateStatus --jq '[.isDraft, .state, .mergeStateStatus] | @tsv'
IFS="$(printf '\t')" read -r rascunho situacao estado <<PRECOND
$MEDIDO
PRECOND

case "$rascunho" in
  true|false) ;;
  *) nao_mediu "pré-condições do PR #$pr: o GitHub respondeu, mas sem dizer se ele é rascunho." ;;
esac
[ -n "$situacao" ] || nao_mediu "pré-condições do PR #$pr: o GitHub respondeu, mas sem a situação do PR."
[ -n "$estado" ] || nao_mediu "pré-condições do PR #$pr: o GitHub respondeu, mas sem estado de merge."

printf 'medido: PR #%s situação %s, rascunho %s, estado de merge %s.\n' "$pr" "$situacao" "$rascunho" "$estado"

if [ "$situacao" != "OPEN" ]; then
  printf 'RECUSADO: o PR #%s não está aberto — situação %s.\n' "$pr" "$situacao" >&2
  exit 1
fi

if [ "$rascunho" = "true" ]; then
  printf 'RECUSADO: o PR #%s está em rascunho, e rascunho não mergeia.\n' "$pr" >&2
  printf '`gh stack submit` cria o PR como rascunho quando o terminal não é interativo.\n' >&2
  printf 'Submeta com `gh stack submit --open`, ou marque este com `gh pr ready %s`.\n' "$pr" >&2
  exit 1
fi

case "$estado" in
  CLEAN|UNSTABLE|HAS_HOOKS) ;;
  *) printf 'RECUSADO: o PR #%s está em estado %s.\n' "$pr" "$estado" >&2; exit 1 ;;
esac

printf 'PR #%s liberado: sem bloqueio, nenhuma verificação vermelha nem pendente, aberto, fora de rascunho, estado %s.\n' "$pr" "$estado"

# Reason: a PR belonging to a stack does not merge through `gh pr merge` —
# GitHub requires the stack path. `gh stack merge` is atomic — everything up
# to the chosen PR goes in together, or nothing does — which is why the
# check above needs to hold for the whole stack below, not just this PR. A
# `gh stack view` that fails here means "this branch is not on a stack", not
# "could not ask": the three measurements above already proved GitHub
# answers. Without them, this line would be the silent bypass to a merge
# that does not verify the stack.
#
# Reason: being on a local stack is not enough, because `gh stack view`
# answers for the **local** stack, which exists starting from a branch.
# GitHub's stack, which is what `gh stack merge` looks up by number, is only
# born with two PRs: the first item of a roadmap, or any lone document stage,
# produces a single PR that `gh stack merge` refuses, saying it "is not a
# stack number or a stacked pull request". The lock was then measuring the
# wrong thing — asking "is this branch on a stack here?" when the decision
# depends on "does that stack exist there?" — and the released merge never
# went through. The count below is the right question, and it gets printed.
if timeout "$TETO" gh stack view --json >/dev/null 2>&1; then
  command -v jq >/dev/null 2>&1 || nao_mediu "a pilha respondeu, mas sem jq não há como contar os PRs abertos dela."
  mede "a pilha da branch atual" gh stack view --json
  abertos="$(printf '%s' "$MEDIDO" | jq '[.branches[] | select(.pr != null and .pr.state == "OPEN")] | length' 2>/dev/null)"
  case "$abertos" in
    ''|*[!0-9]*) nao_mediu "a pilha da branch atual: o \`gh stack view --json\` respondeu, mas sem contagem de PR aberto." ;;
  esac

  # Reason: the stack measured is the current branch's, and the PR might not
  # belong to it. `gh stack view` only knows how to answer for the branch you
  # are on. Whoever merges a PR from outside their own stack — the case of
  # someone following a run and closing their own PR without leaving the
  # branch they were on — would measure a stack that has nothing to do with
  # the target, and take the atomic path over a chain that does not contain
  # it. It worked once by accident, with the count at 1; with the count at 2
  # `gh stack merge` would have taken along PRs nobody asked to merge. The
  # missing question was whether the target is on the stack.
  no_alvo="$(printf '%s' "$MEDIDO" | jq --arg pr "$pr" \
    '[.branches[] | select(.pr != null and (.pr.number|tostring) == $pr)] | length' 2>/dev/null)"
  case "$no_alvo" in
    ''|*[!0-9]*) nao_mediu "a pilha da branch atual: não deu para dizer se o PR #$pr pertence a ela." ;;
  esac
  if [ "$no_alvo" -eq 0 ]; then
    printf 'medido: o PR #%s não pertence à pilha da branch atual — merge pela via do PR.\n' "$pr"
    abertos=1
  else
    printf 'medido: a pilha da branch atual tem %s PR(s) aberto(s), e o #%s está nela.\n' "$abertos" "$pr"
  fi
fi

if [ "${abertos:-0}" -ge 2 ]; then
  mede "a lista de PRs abertos" gh pr list --state open --json number --jq '.[].number'
  abaixo_de_todos="$MEDIDO"
  for abaixo in $(printf '%s\n' "$abaixo_de_todos" | sort -n); do
    [ "$abaixo" -le "$pr" ] || continue
    mede "rótulos do PR #$abaixo" gh pr view "$abaixo" --json labels --jq '.labels[].name'
    r="$(printf '%s\n' "$MEDIDO" | grep '^blocked-on-' || true)"
    [ -z "$r" ] || { printf 'RECUSADO: o PR #%s, abaixo na pilha, está travado por %s.\n' "$abaixo" "$r" >&2; exit 1; }
    espera_checks "$abaixo"
    v="$(printf '%s\n' "$MEDIDO" | awk -F'\t' '$2=="fail"{print $1}')"
    [ -z "$v" ] || { printf 'RECUSADO: o PR #%s, abaixo na pilha, tem check vermelho.\n' "$abaixo" >&2; exit 1; }
  done
  printf 'A pilha inteira até o #%s está limpa. Merge atômico.\n' "$pr"
  timeout "$TETO" gh stack merge "$pr" --yes --merge-method "${metodo#--}"
else
  timeout "$TETO" gh pr merge "$pr" "$metodo"
fi
