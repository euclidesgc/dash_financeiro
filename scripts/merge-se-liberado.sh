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
# Teto de espera por verificação pendente. Separado do teto de rede: aquele mede
# se o GitHub responde, este mede quanto se espera por um CI que ainda roda.
ESPERA="${MERGE_ESPERA_SEGUNDOS:-1200}"
# De quanto em quanto se relê. Separado do teto para o teste poder medir o
# veredicto sem esperar o intervalo de produção.
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

# O resultado sai em `$MEDIDO`, e não pelo stdout, porque `mede` precisa poder
# encerrar o script quando não mede. Um `exit` dentro de `$( )` encerra só o
# subshell da substituição: o script seguiria adiante com a variável vazia, que
# é exatamente a leitura de vazio como resposta que esta reescrita existe para
# acabar. Chamada direta, o `exit` vale.
MEDIDO=""

# mede <descrição> <comando...>
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

# `gh pr checks` sai 1 quando há check vermelho e 8 quando há pendente: os dois
# são medição bem-sucedida, e tratá-los como falha travaria todo PR legítimo.
# Já 2 (PR inexistente) e qualquer erro de transporte são falta de medição.
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

# POR QUE PENDENTE NÃO É VERDE
# A primeira versão recusava só o check `fail`. Um PR cujas verificações ainda
# rodam não tem nenhuma `fail` — tem quatro `pending` —, então ele passava, e o
# merge acontecia antes de o CI dizer qualquer coisa. É a mesma forma de falha
# que o cabeçalho deste arquivo descreve: a ausência de vermelho lida como
# verde, quando o certo era ler como *ainda não medido*. Numa noite de trinta
# merges, isso é trinta merges sem CI.
#
# Espera até $ESPERA segundos e recusa o que continuar pendente. Recusar de
# imediato travaria todo PR legítimo, porque o CI sempre começa pendente.
# VAZIO E PENDENTE SÃO A MESMA COISA: NÃO TERMINOU DE MEDIR
#
# A lista vazia tem duas leituras — "este repositório não tem CI" e "as suítes
# ainda não apareceram" —, e logo depois de um push é sempre a segunda: o GitHub
# leva segundos para registrar os checks. Recusar na primeira leitura vazia é
# recusar todo PR recém-empurrado, o que aconteceu com um force-push desta
# madrugada, seis segundos antes de as quatro suítes aparecerem.
#
# As duas esperam pelo mesmo motivo e pelo mesmo tempo. O que as separa é o que
# a espera revela: quem tinha CI mostra as suítes, quem não tinha continua vazio
# até o teto — e aí a recusa é sobre um fato, não sobre um instante.
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
      # A lista vazia depois do teto é julgada fora daqui, junto com a saída de
      # `MERGE_SEM_CI`: aqui só se decide que a espera acabou.
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

# A CAUSA MAIS COMUM DE "NENHUMA VERIFICAÇÃO" NUMA PILHA
#
# Um fluxo de `pull_request` roda sobre o **merge commit** que o GitHub calcula
# entre o head e a base. Quando esse merge não é calculável, o `refs/pull/N/merge`
# não existe e **nenhum run nasce** — nem falha, nem fica pendente: não é criado.
# `mergeable` fica `UNKNOWN` para sempre e o PR parece só "ainda sem CI".
#
# Numa pilha isso acontece sem ninguém tocar no PR de cima: basta a **base**
# entrar em conflito — o trunk andou, e o PR de baixo ficou `DIRTY`. O topo perde
# o CI em silêncio, o veredicto cego reprova o critério que depende do CI por não
# conseguir medir, e a escalada aponta para o critério, que não tem culpa.
#
# Medido duas vezes na mesma corrida, em 04/09/2026, com a mesma forma.
#
# Esta função não decide nada: ela só diz o que mediu, quando a recusa já
# aconteceu. Diagnóstico é barato; achar a causa a montante às três da manhã não.
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
# NENHUMA VERIFICAÇÃO NÃO É VERIFICAÇÃO VERDE
#
# `gh pr checks` devolve vazio quando o PR não tem suíte nenhuma, e a leitura
# ingênua disso é "nenhum check vermelho". É a forma mais pura do defeito que
# este script inteiro existe para matar. Aconteceu num projeto real: o Actions
# parou de executar por cota, dois PRs foram para o encerramento sem nenhuma
# suíte de `github-actions`, e nada no processo perguntou — o veredicto cego
# mede critério, o `check` mede coerência, e a DoD global é "do CI", que é
# justamente a parte que ninguém confere ter acontecido.
#
# `MERGE_SEM_CI=1` existe para o repositório que legitimamente não tem CI, e é
# deliberado: quem o usa está declarando que sabe.
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

# POR QUE AS PRÉ-CONDIÇÕES SÃO MEDIDAS JUNTAS
# `mergeStateStatus` responde o que o GitHub pensa da **branch** — conflito,
# proteção, verificação. Ele diz `CLEAN` de um PR em rascunho e de um PR já
# fechado, e o merge dos dois é recusado assim mesmo. Cada pré-condição que
# ficasse de fora daqui custaria a mesma noite: a tranca imprime "liberado", o
# `gh` responde `Pull Request is still a draft` e ninguém está lendo às três da
# manhã. Elas são medidas juntas, numa chamada só, e cada recusa é nominal.
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

# PR que pertence a uma pilha não mergeia por `gh pr merge`: o GitHub exige a
# via da pilha. `gh stack merge` é atômico — tudo até o PR escolhido entra
# junto, ou nada entra —, e é por isso que a checagem acima precisa valer para
# toda a pilha abaixo, não só para este PR.
#
# Um `gh stack view` que falha aqui significa "esta branch não está numa
# pilha", e não "não consegui perguntar": as três medições acima já provaram
# que o GitHub responde. Sem elas, esta linha seria o desvio silencioso para o
# merge que não verifica a pilha.
#
# POR QUE ESTAR NUMA PILHA LOCAL NÃO BASTA
# `gh stack view` responde pela pilha **local**, que existe a partir de uma
# branch. A pilha do GitHub, que é quem o `gh stack merge` procura pelo número,
# só nasce com dois PRs: o primeiro item de um roadmap, ou qualquer estágio de
# documento sozinho, produz um PR único que o `gh stack merge` recusa dizendo
# que ele "is not a stack number or a stacked pull request". A tranca então
# media a coisa errada — perguntava "esta branch está numa pilha aqui?" quando
# a decisão depende de "essa pilha existe lá?" — e o merge liberado não saía.
# A contagem abaixo é a pergunta certa, e ela é impressa.
if timeout "$TETO" gh stack view --json >/dev/null 2>&1; then
  command -v jq >/dev/null 2>&1 || nao_mediu "a pilha respondeu, mas sem jq não há como contar os PRs abertos dela."
  mede "a pilha da branch atual" gh stack view --json
  abertos="$(printf '%s' "$MEDIDO" | jq '[.branches[] | select(.pr != null and .pr.state == "OPEN")] | length' 2>/dev/null)"
  case "$abertos" in
    ''|*[!0-9]*) nao_mediu "a pilha da branch atual: o \`gh stack view --json\` respondeu, mas sem contagem de PR aberto." ;;
  esac

  # A PILHA MEDIDA É A DA BRANCH CORRENTE, E O PR PODE NÃO SER DELA
  # `gh stack view` só sabe responder pela branch em que se está. Quem mergeia
  # um PR de fora da própria pilha — o caso de quem acompanha uma corrida e
  # fecha um PR próprio sem sair da branch em que estava — mediria uma pilha
  # que não tem nada a ver com o alvo, e iria pela via atômica sobre uma
  # corrente que não o contém. Deu certo por acaso uma vez, com a contagem em
  # 1; com a contagem em 2 o `gh stack merge` teria levado junto PRs que
  # ninguém mandou mergear. A pergunta que faltava é se o alvo está na pilha.
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
