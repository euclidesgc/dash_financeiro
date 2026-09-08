#!/usr/bin/env bash
# O motor da corrida autônoma. Casca fina: a decisão mora em
# scripts/loop/decide-next-action.mjs, que é uma função pura sobre o estado.
#
# Não acrescente decisão aqui.
#
#   proxima-sessao.sh            uma rodada: decide, invoca a sessão, empilha o PR
#   proxima-sessao.sh --dry-run  imprime a decisão e sai, sem invocar nada
#   proxima-sessao.sh --ate N    no máximo N rodadas encadeadas (padrão: 1)
#
# O QUE ELE NUNCA FAZ: mergear PR, e empurrar com --force. A pilha existe para
# o merge ser uma decisão do dev, tomada de uma vez, acordado — e é
# scripts/merge-se-liberado.sh quem mergeia, quando o dev mandar.
#
# CADA RODADA É UMA SESSÃO NOVA. `claude -p` abre processo novo e o prompt é a
# única entrada — é daí que vem a economia de contexto.
#
# ⚠️ A sessão roda com --dangerously-skip-permissions, porque não há ninguém
# acordado para aprovar cada escrita. Os hooks do harness continuam valendo
# (escopo de agent, documento aprovado, comando destrutivo); o que deixa de
# existir é a pergunta ao humano. Reveja antes da primeira noite.
#
# gate3-ok: o bloco abaixo é o registro de por que o motor sobrevive a uma
# rodada ruim, e não a mecânica de como.
#
# POR QUE ELE SE RECUPERA
# Na primeira noite real uma rodada morreu às 07:13. A árvore ficou suja, o
# motor recusou partir — que era o comportamento projetado — e a corrida parou
# por cinco horas com o dono dormindo. Duas mudanças saíram daí:
#   1. rodada que falha é tentada mais UMA vez, não a noite inteira;
#   2. trabalho a meio caminho vira commit `wip` na branch da própria fase, em
#      vez de bloquear tudo. Não é validado nem mergeado: só deixa de ser refém
#      da árvore suja, e a rodada seguinte retoma a fase de onde parou.
#
# POR QUE TUDO TEM TETO DE TEMPO
# Sobreviver a uma rodada que MORRE não é o mesmo que sobreviver a uma que
# PENDURA. Uma sessão parada — esperando uma rede que não volta, um comando que
# nunca retorna — não sai com erro: ela simplesmente não termina, e as duas
# tentativas nunca chegam a contar. O motor fica vivo, o batimento congela na
# mesma linha e a noite passa inteira numa rodada só, sem nada acusar.
#
# Espera sem teto não é espera, é travamento. Toda invocação aqui tem teto, e
# estourar o teto conta como tentativa falha: entra na recuperação que já
# existe, em vez de inventar um segundo caminho.
set -uo pipefail

# Reason: ceiling per work session. Generous on purpose — a real phase takes
# tens of minutes, and cutting off too early turns good work into `wip`.
TETO_SESSAO="${MOTOR_TETO_SESSAO:-3600}"
# Reason: ceiling for whatever talks to the network. Short — if GitHub has
# not answered in half a minute, waiting longer will not change the answer.
TETO_REDE="${MOTOR_TETO_REDE:-30}"
# Reason: ceiling for the decision, which is a pure function over the state
# and should be instantaneous. Going past this is a defect, not slowness.
TETO_DECISAO="${MOTOR_TETO_DECISAO:-60}"

raiz="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$raiz" || exit 2

seco=0
ate=1
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) seco=1 ;;
    --ate) shift; ate="${1:-1}" ;;
    *) printf 'argumento desconhecido: %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done

for ferramenta in node claude gh git timeout; do
  command -v "$ferramenta" >/dev/null 2>&1 || {
    printf 'motor: %s não encontrado no PATH; nada foi decidido.\n' "$ferramenta" >&2
    exit 2
  }
done

# Reason: the plugin version that runs all night has to match the project's
# own. `compose.py --update` copies the plugin's assets into the project and
# records the version in `.harness/config.json` — it does not decide which
# plugin Claude Code loads; that is whatever is installed in the cache.
# Running the update from a development repository leaves the project with
# the new version's assets and the previous skills, agents and `state.py` —
# and the run spends the whole night deciding with a harness two versions
# behind, with nothing to flag it. Measured: a project on 0.7.0 with the
# plugin on 0.2.1, rediscovering defects the installed version had already
# fixed. A version mismatch is a warning when someone is watching, and a
# refusal here: a night not run costs one night; a night run with the wrong
# harness costs the night plus the work of discovering what in it was decided
# for the wrong reason.
config="$raiz/.harness/config.json"
if [ -f "$config" ] && [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/.claude-plugin/plugin.json" ]; then
  versao_projeto="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("harness_version",""))' "$config" 2>/dev/null)"
  versao_plugin="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("version",""))' "$CLAUDE_PLUGIN_ROOT/.claude-plugin/plugin.json" 2>/dev/null)"
  if [ -n "$versao_projeto" ] && [ -n "$versao_plugin" ] && [ "$versao_projeto" != "$versao_plugin" ]; then
    printf 'motor: o projeto está instalado com o harness %s e o plugin carregado é %s.\n' "$versao_projeto" "$versao_plugin" >&2
    printf 'motor: recuso partir. A noite rodaria com skills, agents e state.py de uma versão,\n' >&2
    printf '       e os ativos do projeto de outra — e nada acusaria durante a corrida.\n' >&2
    printf '       Reinstale o plugin na versão do projeto, ou rode:\n' >&2
    printf '       python3 "$CLAUDE_PLUGIN_ROOT/scripts/init/compose.py" --root . --update --dry-run\n' >&2
    exit 2
  fi
fi

batimento="$raiz/.harness/runtime/motor-batimento"
mkdir -p "$(dirname "$batimento")"

# Reason: the session-start hook exports CLAUDE_PLUGIN_ROOT by writing to the
# file CLAUDE_ENV_FILE points at, which Claude Code loads before every Bash
# call. Without this variable set, the export has nowhere to go and every
# prompt command using "$CLAUDE_PLUGIN_ROOT" fails with "can't open file
# '/scripts/state/state.py'" — that is what consumed the first two attempts
# of every session on the first night. This script is what opens the
# session, so it is the one that prepares the channel.
export CLAUDE_ENV_FILE="${CLAUDE_ENV_FILE:-$raiz/.harness/runtime/sessao-env.sh}"
: > "$CLAUDE_ENV_FILE"

# Reason: an external watcher reads progress with `cat`, never with `pgrep` —
# pgrep's pattern matches the very command that runs it, and fooled three checks.
marca() { printf '%s %s\n' "$(date -Iseconds)" "$1" > "$batimento"; }

# Reason: `wip` is a safety net for a round that DIED, and only for that. The
# mess it finds at STARTUP can be something else — someone editing, right
# now, the branch where it stopped. Committing it with an "interrupted round"
# message erases the authorship of that work and buries it under a commit
# nobody will go looking for — it happened with the fix to this very file,
# not yet committed, the first time the engine was run against a person's
# open tree. The net is only armed on a harness work branch —
# `<nnn-slug>/fase-N-…` or `<nnn-slug>/planejamento`. On any other — including
# a legitimate `fix/…` or `docs/…` — the dirty tree belongs to a person, and
# the engine refuses out loud instead of deciding for them. The previous
# blocklist (`main`, `develop`, detached) was not enough: it named three
# places not to commit, when the right approach is to name the two places
# where committing is allowed.
salva_meio_caminho() {
  [ -n "$(git status --porcelain)" ] || return 0
  local branch; branch="$(git branch --show-current)"
  case "$branch" in
    [0-9][0-9][0-9]-*/fase-[0-9]*|[0-9][0-9][0-9]-*/planejamento) ;;
    *)
      printf 'motor: árvore suja em %s, que não é branch de fase nem de planejamento.\n' "${branch:-detached}" >&2
      printf 'motor: não comito wip aqui — a sujeira pode ser trabalho de gente. Comite ou guarde à mão.\n' >&2
      return 1 ;;
  esac
  git add -A
  git commit --quiet -m "wip(${branch}): interrupted round, not reviewed nor validated

The round that produced this died before finishing. Committed so the tree stops
blocking the next round; the phase resumes from here and the blind validator
judges the branch tip, not this commit." || return 1
  printf 'motor: trabalho a meio caminho salvo como wip em %s.\n' "$branch" >&2
}

if [ "$seco" -eq 0 ] && [ -n "$(git status --porcelain)" ]; then
  printf 'motor: árvore suja ao partir — provavelmente sobra de rodada anterior.\n' >&2
  salva_meio_caminho || {
    printf 'motor: não consegui limpar a árvore com segurança. Comite ou guarde à mão.\n' >&2
    git status --short >&2
    exit 2
  }
fi

# Reason: how many rounds the same phase can consume. State escalation covers
# the phase FAILED twice. It does not cover the phase that never gets judged
# at all: a phase too big stays `em_execucao`, the next round resumes it, and
# the run spends the night on the same phase with no verdict at all — silently,
# because nothing failed. Measured: a phase of 29 criteria consumed two
# rounds, the second blowing the session ceiling with work left half-done.
# Three is the ceiling because a second resumption is still plausible — the
# first round may have died early — and a third already says something else:
# the phase does not fit a session, and insisting spends the night to find
# that out in the morning. The cause is upstream, in how the plan was cut, as
# with every escalation here.
TETO_MESMA_FASE="${MOTOR_TETO_MESMA_FASE:-3}"

# Reason: and how many the same item can consume with no verdict. The
# ceiling above counts the SAME phase, and `repair-criteria` is not `phase` —
# a `phase → repair → phase → repair` cycle zeroes the count on every
# alternation and runs forever. The repair is real progress — the validator
# rejected a malformed criterion and the block goes back to whoever wrote it
# — but five rounds alternating with no verdict at all say the same thing as
# three on the same phase: the phase does not fit, and the cause is how the
# plan was cut. Five, not three, because a legitimate repair costs one round
# and the following phase costs another; an item wanting two repairs still fits.
TETO_MESMO_ITEM="${MOTOR_TETO_MESMO_ITEM:-5}"
alvo_anterior=""
repeticoes=0
item_anterior=""
rodadas_do_item=0
alvo_anterior_do_item=""

rodada=0
while [ "$rodada" -lt "$ate" ]; do
  rodada=$((rodada + 1))
  printf '\n═══ rodada %s de %s ═══\n' "$rodada" "$ate"
  marca "rodada $rodada: decidindo"

  # Reason: the cleanup runs before the decision, because it is what unblocks
  # the branch. `gh stack` keeps each stack in `.git/gh-stack` and nothing
  # removes them once they have served their purpose. A run creates one per
  # stage and one per phase, so by the third the session's `gh stack add`
  # refuses: "branch develop belongs to multiple stacks; use an interactive
  # terminal to select one". There is no flag to choose between stacks, `init`
  # creates yet another, and there is no interactive terminal here — the round
  # dies with no branch. And the buildup gets worse on its own with every
  # stage that closes. The script measures each PR before letting go,
  # preserves the current branch's stack, and only touches local tracking. It
  # does not decide what the session does, so a cleanup that fails does not
  # stop the round: it warns, and the session tries anyway.
  if [ -f scripts/loop/larga-pilhas-mortas.mjs ]; then
    timeout "$TETO_REDE" node scripts/loop/larga-pilhas-mortas.mjs \
      || printf 'motor: a faxina de pilhas não concluiu; sigo, e `gh stack add` pode recusar por ambiguidade.\n' >&2
  fi

  decisao="$(timeout "$TETO_DECISAO" node scripts/loop/decide-next-action.mjs)"
  codigo=$?
  [ "$codigo" -eq 124 ] && {
    marca "parado: a decisão não respondeu em ${TETO_DECISAO}s"
    printf '\nmotor: decide-next-action.mjs pendurou por mais de %ss. É função pura sobre o estado: passar disso é defeito, não lentidão.\n' "$TETO_DECISAO" >&2
    exit 2
  }
  printf '%s\n' "$decisao"

  if [ "$codigo" -ne 0 ]; then
    marca "parado: a decisão mandou parar"
    printf '\nmotor: parando na rodada %s.\n' "$rodada"
    exit 0
  fi

  # Reason: the target is the (item, phase) pair — two rounds in a row on the
  # same phase are resumption; the third is the phase not fitting a session.
  alvo="$(printf '%s' "$decisao" | node -e 'let e="";process.stdin.on("data",d=>e+=d).on("end",()=>{const j=JSON.parse(e);process.stdout.write(j.action==="phase"?`${j.item}#${j.phase}`:"")})')"
  if [ -n "$alvo" ] && [ "$alvo" = "$alvo_anterior" ]; then
    repeticoes=$((repeticoes + 1))
  else
    repeticoes=1
  fi
  alvo_anterior="$alvo"

  # Reason: what gets counted here is a consecutive round WITH NO PHASE
  # ADVANCING. A new phase is real progress — the previous one got a verdict
  # — so it resets. A `repair-criteria` neither advances nor retreats: it
  # holds the count, which is why alternating between phase and repair does
  # not escape the ceiling.
  item_em_curso="$(printf '%s' "$decisao" | node -e 'let e="";process.stdin.on("data",d=>e+=d).on("end",()=>{const j=JSON.parse(e);process.stdout.write(["phase","repair-criteria"].includes(j.action)?(j.item??""):"")})')"
  if [ -z "$item_em_curso" ] || [ "$item_em_curso" != "$item_anterior" ]; then
    rodadas_do_item=1
  elif [ -n "$alvo" ] && [ "$alvo" != "$alvo_anterior_do_item" ]; then
    rodadas_do_item=1   # a fase mudou: a anterior fechou
  else
    rodadas_do_item=$((rodadas_do_item + 1))
  fi
  item_anterior="$item_em_curso"
  [ -n "$alvo" ] && alvo_anterior_do_item="$alvo"

  if [ -n "$item_em_curso" ] && [ "$rodadas_do_item" -ge "$TETO_MESMO_ITEM" ]; then
    marca "parado: $item_em_curso consumiu $rodadas_do_item rodadas sem veredicto"
    printf '\nmotor: %s consumiu %s rodadas seguidas entre execução e reparo de critério,\n' "$item_em_curso" "$rodadas_do_item" >&2
    printf '       e nenhuma produziu veredicto.\n' >&2
    printf 'motor: paro aqui. Alternar entre fase e reparo não é progresso que valha uma\n' >&2
    printf '       noite: se o critério precisa de reparo repetido, o problema é o corte.\n' >&2
    exit 2
  fi

  if [ -n "$alvo" ] && [ "$repeticoes" -ge "$TETO_MESMA_FASE" ]; then
    marca "parado: $alvo consumiu $repeticoes rodadas sem veredicto"
    printf '\nmotor: %s consumiu %s rodadas seguidas e nenhuma produziu veredicto.\n' "$alvo" "$repeticoes" >&2
    printf 'motor: paro aqui. Uma fase que não fecha em três sessões não é uma fase lenta —\n' >&2
    printf '       é duas fases escritas como uma, e a causa é o corte do plano.\n' >&2
    printf '       Conte os critérios da fase: acima de uma dúzia, ela não cabe numa sessão.\n' >&2
    exit 2
  fi

  prompt="$(printf '%s' "$decisao" | node -e 'let e="";process.stdin.on("data",d=>e+=d).on("end",()=>process.stdout.write(JSON.parse(e).prompt??""))')"

  if [ "$seco" -eq 1 ]; then
    printf '\nmotor: --dry-run, nada foi invocado.\n'
    exit 0
  fi

  [ -f "$prompt" ] || { printf 'motor: %s não existe.\n' "$prompt" >&2; exit 2; }

  tentativa=0
  ok=0
  while [ "$tentativa" -lt 2 ]; do
    tentativa=$((tentativa + 1))
    marca "rodada $rodada: sessão viva (tentativa $tentativa)"
    : > "$CLAUDE_ENV_FILE"
    timeout --signal=TERM --kill-after=30 "$TETO_SESSAO" \
      claude -p "$(cat "$prompt")" --dangerously-skip-permissions
    saida_sessao=$?
    if [ "$saida_sessao" -eq 0 ]; then
      ok=1
      break
    fi
    if [ "$saida_sessao" -eq 124 ]; then
      marca "rodada $rodada: sessão pendurada, cortada em ${TETO_SESSAO}s (tentativa $tentativa)"
      printf '\nmotor: a sessão da rodada %s pendurou e foi cortada em %ss (tentativa %s de 2).\n' "$rodada" "$TETO_SESSAO" "$tentativa" >&2
    else
      printf '\nmotor: a sessão da rodada %s saiu com erro (tentativa %s de 2).\n' "$rodada" "$tentativa" >&2
    fi
    salva_meio_caminho || true
  done

  if [ "$ok" -eq 0 ]; then
    marca "parado: duas tentativas falharam na rodada $rodada"
    printf 'motor: duas tentativas seguidas falharam. Parando — a causa é a montante.\n' >&2
    exit 2
  fi

  marca "rodada $rodada: empilhando o PR"
  if timeout "$TETO_REDE" gh stack view >/dev/null 2>&1; then
    # Reason: the PR is born a draft, and the local gate is what promotes it.
    # `--auto` with no `--open` creates it as a draft, which is what is
    # wanted: no CI job runs on a draft PR — the generated workflows carry the
    # guard, and `scripts/gates/rascunho.sh` charges it — so the night's
    # iteration burns no runner at all. Measured before: ~6 runs per PR and
    # 189 in one run night, because every push re-triggered everything and
    # the previous run kept going to the end measuring a commit nobody was
    # going to merge. This step is what promotes it, and only after the local
    # gates pass. The session already ran them; running them again here is
    # not distrust of it — it is the difference between the engine KNOWING
    # what it stacked passes and BELIEVING it passes. The draft that remains
    # is the information that it did not pass, visible on the PR.
    if timeout "$TETO_REDE" gh stack submit --auto; then
      marca "rodada $rodada: medindo os portões antes de promover"
      if bash scripts/gates/gates_runner.sh --sem-artefatos >/dev/null 2>&1; then
        promovidos=0
        for numero in $(timeout "$TETO_REDE" gh pr list --state open --draft \
              --json number --jq '.[].number' 2>/dev/null); do
          timeout "$TETO_REDE" gh pr ready "$numero" >/dev/null 2>&1 \
            && promovidos=$((promovidos + 1))
        done
        printf 'motor: portões locais limpos; %s PR(s) promovido(s) de rascunho a pronto.\n' "$promovidos"
      else
        printf 'motor: os portões locais reprovaram. O PR fica em RASCUNHO — que é o\n' >&2
        printf '       estado certo para trabalho que não passa, e o CI remoto não é\n' >&2
        printf '       gasto medindo o que já se sabe vermelho.\n' >&2
      fi
    else
      printf 'motor: gh stack submit falhou ou não respondeu em %ss; os commits continuam locais.\n' "$TETO_REDE" >&2
    fi
  else
    printf 'motor: a branch corrente não está numa pilha; os commits continuam locais. `gh stack init --base develop <branch>` adota o que existe.\n' >&2
  fi
done

marca "concluído: $rodada rodada(s)"
printf '\nmotor: %s rodada(s) concluída(s).\n' "$rodada"
