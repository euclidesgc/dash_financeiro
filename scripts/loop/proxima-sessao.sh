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

# Teto por sessão de trabalho. Generoso de propósito: uma fase real leva
# dezenas de minutos, e cortar cedo demais transforma trabalho bom em `wip`.
TETO_SESSAO="${MOTOR_TETO_SESSAO:-3600}"
# Teto para o que fala com a rede. Curto: se o GitHub não respondeu em meio
# minuto, esperar mais não muda a resposta.
TETO_REDE="${MOTOR_TETO_REDE:-30}"
# Teto para a decisão, que é uma função pura sobre o estado e devia ser
# instantânea. Passar disso é defeito, não lentidão.
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

# A VERSÃO DO PLUGIN QUE VAI RODAR A NOITE INTEIRA
#
# `compose.py --update` copia os ativos do plugin para dentro do projeto e grava
# a versão em `.harness/config.json`. Ele não decide qual plugin o Claude Code
# vai carregar: isso é o que está instalado no cache. Rodar o update a partir de
# um repositório de desenvolvimento deixa o projeto com os ativos da versão nova
# e as skills, agents e o `state.py` da antiga — e a corrida passa a noite
# inteira decidindo com um harness de duas versões atrás, sem nada acusar. Foi
# medido: um projeto em 0.7.0 com o plugin em 0.2.1, redescobrindo defeitos que
# a versão instalada já tinha corrigido.
#
# Diferença de versão é aviso quando alguém está olhando, e recusa aqui: uma
# noite não rodada custa uma noite; uma noite rodada com o harness errado custa
# a noite e o trabalho de descobrir o que nela foi decidido pelo motivo errado.
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

# O hook de início de sessão exporta CLAUDE_PLUGIN_ROOT escrevendo no arquivo
# apontado por CLAUDE_ENV_FILE, que o Claude Code carrega antes de cada Bash.
# Sem essa variável definida, a exportação não tem para onde ir e todo comando
# do prompt que use "$CLAUDE_PLUGIN_ROOT" falha com "can't open file
# '/scripts/state/state.py'" — foi o que consumiu as duas primeiras tentativas
# de cada sessão da primeira noite. Quem abre a sessão é este script, então é
# ele quem prepara o canal.
export CLAUDE_ENV_FILE="${CLAUDE_ENV_FILE:-$raiz/.harness/runtime/sessao-env.sh}"
: > "$CLAUDE_ENV_FILE"

# Vigia externo lê o progresso com `cat`, nunca com `pgrep`: o padrão do pgrep
# casa com o próprio comando que o executa, e enganou três verificações.
marca() { printf '%s %s\n' "$(date -Iseconds)" "$1" > "$batimento"; }

# O `wip` é uma rede para rodada que MORREU, e só para isso. A sujeira que ele
# encontra na PARTIDA pode ser outra coisa: alguém editando, agora, na branch em
# que parou. Comitá-la com mensagem de "rodada interrompida" apaga a autoria do
# trabalho e o enterra sob um commit que ninguém vai procurar — aconteceu com a
# correção deste mesmo arquivo, ainda não commitada, na primeira vez que o motor
# foi exercitado com a árvore de uma pessoa aberta.
#
# A rede só é armada em branch de trabalho do harness: `<nnn-slug>/fase-N-…` ou
# `<nnn-slug>/planejamento`. Em qualquer outra — inclusive uma `fix/…` ou
# `docs/…` legítima —, a árvore suja é de gente, e o motor recusa em voz alta em
# vez de decidir por ela. A lista negra anterior (`main`, `develop`, destacada)
# não bastava: ela nomeava três lugares onde não comitar, quando o certo é
# nomear os dois onde comitar.
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

# QUANTAS RODADAS A MESMA FASE PODE CONSUMIR
#
# A escalada do estado cobre a fase REPROVADA duas vezes. Não cobre a fase que
# nunca chega a ser julgada: uma fase grande demais fica `em_execucao`, a rodada
# seguinte a retoma, e a corrida gasta a noite na mesma fase sem nenhum veredicto
# — em silêncio, porque nada falhou. Medido: uma fase de 29 critérios consumiu
# duas rodadas, a segunda estourando o teto de sessão com o trabalho a meio
# caminho.
#
# Três é o teto porque a segunda retomada ainda é plausível — a primeira rodada
# pode ter morrido cedo — e a terceira já diz outra coisa: a fase não cabe numa
# sessão, e insistir é gastar a noite para descobrir isso de manhã. A causa é a
# montante, no corte do plano, como toda escalada aqui.
TETO_MESMA_FASE="${MOTOR_TETO_MESMA_FASE:-3}"

# E QUANTAS O MESMO ITEM PODE CONSUMIR SEM VEREDICTO
#
# O teto acima conta a MESMA fase, e `repair-criteria` não é `phase`: um ciclo
# `phase → repair → phase → repair` zera a contagem a cada alternância e passa
# para sempre. O reparo é progresso real — o validador recusou um critério mal
# formado e o bloco volta a quem o escreveu —, mas cinco rodadas alternando sem
# nenhum veredicto dizem a mesma coisa que três na mesma fase: a fase não cabe,
# e a causa é o corte do plano.
#
# Cinco, e não três, porque o reparo legítimo custa uma rodada e a fase seguinte
# custa outra; quem quiser um item com dois reparos ainda cabe.
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

  # A FAXINA VEM ANTES DA DECISÃO, PORQUE É ELA QUE DESTRAVA A BRANCH
  #
  # `gh stack` guarda cada pilha em `.git/gh-stack` e nada as remove quando elas
  # cumprem o papel. Uma corrida cria uma por estágio e uma por fase, então na
  # terceira o `gh stack add` da sessão recusa: "branch develop belongs to
  # multiple stacks; use an interactive terminal to select one". Não há flag que
  # escolha entre pilhas, `init` cria mais uma, e aqui não existe terminal
  # interativo — a rodada morre sem branch. E o acúmulo piora sozinho a cada
  # estágio que fecha.
  #
  # O script mede cada PR antes de largar, preserva a pilha da branch corrente e
  # mexe só no rastreamento local. Ele não decide o que a sessão faz, então uma
  # faxina que falha não para a rodada: ela avisa, e a sessão tenta assim mesmo.
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

  # O alvo é o par (item, fase): duas rodadas seguidas na mesma fase são
  # retomada; a terceira é a fase não cabendo numa sessão.
  alvo="$(printf '%s' "$decisao" | node -e 'let e="";process.stdin.on("data",d=>e+=d).on("end",()=>{const j=JSON.parse(e);process.stdout.write(j.action==="phase"?`${j.item}#${j.phase}`:"")})')"
  if [ -n "$alvo" ] && [ "$alvo" = "$alvo_anterior" ]; then
    repeticoes=$((repeticoes + 1))
  else
    repeticoes=1
  fi
  alvo_anterior="$alvo"

  # O que se conta aqui é rodada consecutiva SEM QUE A FASE AVANCE. Uma fase
  # nova é progresso de verdade — a anterior recebeu veredicto —, então zera.
  # Um `repair-criteria` não avança nem retrocede: ele mantém a contagem, e é
  # por isso que a alternância entre fase e reparo não escapa do teto.
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
    # O PR NASCE RASCUNHO, E O PORTÃO LOCAL É QUEM O PROMOVE
    #
    # `--auto` sem `--open` cria em rascunho, e é isso que se quer: nenhum job do
    # CI roda em PR rascunho — os fluxos gerados têm a guarda, e
    # `scripts/gates/rascunho.sh` a cobra —, então a iteração da noite não
    # consome runner nenhum. Medido antes: ~6 execuções por PR e 189 num dia de
    # corrida, porque cada push redisparava tudo e o run anterior seguia até o
    # fim medindo um commit que ninguém ia mergear.
    #
    # Quem promove é este passo, e só depois de os portões locais passarem. A
    # sessão já os rodou; rodar de novo aqui não é desconfiança dela — é a
    # diferença entre o motor SABER que o que empilhou passa e ACREDITAR que
    # passa. O rascunho que fica é a informação de que não passou, visível no PR.
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
