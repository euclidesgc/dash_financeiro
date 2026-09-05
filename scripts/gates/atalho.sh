#!/usr/bin/env bash
#
# Item 14 da DoD: todo marcador `atalho:` traz teto, troca e item de roadmap —
# e o item citado existe de verdade na fila.
#
# A CAUSA RAIZ QUE ISTO EXISTE PARA MATAR
#
# O item 11 já obriga a dívida deliberada a virar item de roadmap antes de a
# fase fechar. Ele anda num sentido só: do código para a fila. Quem abre o
# arquivo meses depois, corrigindo outra coisa, não lê o corpo do PR nem o
# roadmap — e por isso não descobre que aquela função tem teto. É assim que uma
# trava provisória vira permanente: não por decisão, mas por ninguém que passou
# por ali saber que era provisória.
#
# O marcador fecha o sentido de volta, e este portão é quem o cobra. Sem ele o
# marcador seria convenção, e convenção sem cobrança degrada para lembrete
# sem prazo: o
# primeiro sem gatilho não é notado, o segundo vira precedente, e no terceiro
# ninguém mais escreve o gatilho.
#
# A FORMA
#
#   <prefixo de comentário> atalho: <o que foi simplificado>.
#       teto: <o limite concreto>. troca: <o gatilho>. item: <nnn-slug>
#
# Os três rótulos são obrigatórios, em qualquer ordem, na mesma linha do
# `atalho:`. Rótulo é o que torna isto verificável por texto sem heurística —
# adivinhar qual metade da prosa é o teto produziria portão que erra nos dois
# sentidos, e portão que erra é pior que portão nenhum.
#
# O QUE ELE NÃO OLHA
#
# Arquivos `.md` e `.txt` ficam fora. Marcador vive em código; o que aparece em
# documentação é a convenção sendo *explicada*, e contá-la reprovaria o texto
# que ensina a regra — o portão morderia a própria documentação.
#
# `scripts/gates/` também fica fora, e pelo mesmo motivo levado a sério: o teste
# deste portão carrega marcadores incompletos de propósito, para provar que a
# recusa morde. Contá-los reprovaria todo projeto no dia da instalação.

set -uo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/medir.sh"

exige_comando python3
exige_comando git

RAIZ="$(medir_raiz)"
export RAIZ

# Fora de um repositório git não há universo a varrer, e varrer o que não se
# conhece responde "nenhum marcador" para o caso em que nem se olhou.
git -C "$RAIZ" rev-parse --git-dir >/dev/null 2>&1 ||
  _reprova "$RAIZ não é um repositório git — sem a lista de arquivos versionados não há universo para varrer, e varrer nada responde 'nenhum marcador'"

python3 - <<'PY'
import os
import re
import subprocess
import sys

raiz = os.environ["RAIZ"]

IGNORA_EXT = {".md", ".txt"}
IGNORA_DIR = {
    ".git", "node_modules", "build", "dist", "coverage", "vendor",
    ".dart_tool", ".next", "__pycache__", ".venv", ".gradle",
}

# Os portões são ativos que o harness entrega, não código do produto — e o
# teste deste portão precisa carregar marcadores de exemplo deliberadamente
# incompletos para provar que a recusa morde. Sem esta exclusão, o portão conta
# os próprios exemplos e reprova todo projeto no dia da instalação, por um
# defeito que não é do projeto. Medido na primeira execução do teste em layout
# instalado, que foi exatamente assim que apareceu.
IGNORA_PREFIXO = ("scripts/gates/",)

MARCADOR = re.compile(r"(?:#|//|--|/\*|\*)\s*atalho:\s*(?P<corpo>.*)$", re.IGNORECASE)
ITEM = re.compile(r"\b(\d{3}-[a-z0-9][a-z0-9-]*)\b")
ROTULOS = ("teto", "troca", "item")


def rotulo(corpo, nome):
    """Devolve o valor do rótulo, ou None se ele não está na linha.

    O valor vai até o próximo rótulo, o ponto final ou o fim da linha — quem
    escreve o marcador não deve ter de pensar em ordem nem em separador.
    """
    m = re.search(
        r"\b" + nome + r"\s*:\s*(?P<valor>.+?)"
        r"(?=\s*\b(?:teto|troca|item)\s*:|\s*\.\s*$|$)",
        corpo,
        re.IGNORECASE,
    )
    if not m:
        return None
    valor = m.group("valor").strip().rstrip(".;,").strip()
    return valor or None


def versionados():
    saida = subprocess.run(
        ["git", "-C", raiz, "ls-files", "-z"],
        capture_output=True, text=True, check=False,
    )
    if saida.returncode != 0:
        return None
    return [c for c in saida.stdout.split("\0") if c]


def interessa(rel):
    if os.path.splitext(rel)[1].lower() in IGNORA_EXT:
        return False
    if rel.startswith(IGNORA_PREFIXO):
        return False
    return not any(parte in IGNORA_DIR for parte in rel.split("/"))


def reprova_por_nao_medir(motivo):
    print("::error::portão não conseguiu medir: %s" % motivo, file=sys.stderr)
    print("REPROVADO por impossibilidade de medição, não por resultado.", file=sys.stderr)
    sys.exit(1)


arquivos = versionados()
if arquivos is None:
    reprova_por_nao_medir("`git ls-files` falhou em %s" % raiz)

alvos = [rel for rel in arquivos if interessa(rel)]
if not alvos:
    reprova_por_nao_medir(
        "nenhum arquivo versionado sobrou para varrer sob %s — "
        "um universo vazio responde 'nenhum marcador' sem ter olhado" % raiz
    )

marcadores = []
for rel in alvos:
    caminho = os.path.join(raiz, rel)
    try:
        with open(caminho, "r", encoding="utf-8", errors="strict") as fh:
            for numero, linha in enumerate(fh, start=1):
                m = MARCADOR.search(linha)
                if m:
                    marcadores.append((rel, numero, m.group("corpo").strip()))
    except (UnicodeDecodeError, OSError):
        # Binário ou ilegível não carrega comentário; não é falha de medição.
        continue

print("medido: %d arquivo(s) versionados varridos, %d marcador(es) atalho:"
      % (len(alvos), len(marcadores)))

if not marcadores:
    print("Nenhum atalho deliberado marcado.")
    sys.exit(0)

# O roadmap só é exigido quando há marcador — projeto sem atalho nenhum não
# precisa ter a fila montada para este portão aprovar.
roadmap_rel = "product/roadmap.md"
roadmap = os.path.join(raiz, roadmap_rel)
if not os.path.isfile(roadmap):
    reprova_por_nao_medir(
        "%s não existe, e há %d marcador(es) citando item de roadmap — "
        "sem a fila não há como conferir se o item existe" % (roadmap_rel, len(marcadores))
    )

with open(roadmap, "r", encoding="utf-8", errors="replace") as fh:
    conteudo_roadmap = fh.read()
itens_na_fila = set(ITEM.findall(conteudo_roadmap))
if not itens_na_fila:
    reprova_por_nao_medir(
        "%s não contém nenhum id `nnn-slug` — um roadmap sem itens reprovaria "
        "todo marcador por um defeito que não é do marcador" % roadmap_rel
    )
print("medido: %d item(ns) no roadmap" % len(itens_na_fila))

faltas = []
for rel, numero, corpo in marcadores:
    ausentes = [nome for nome in ROTULOS if rotulo(corpo, nome) is None]
    if ausentes:
        faltas.append((rel, numero, "não declara " + ", ".join(ausentes)))
        continue
    citado = rotulo(corpo, "item")
    achado = ITEM.search(citado or "")
    if not achado:
        faltas.append((rel, numero, "o item '%s' não tem a forma nnn-slug" % citado))
        continue
    if achado.group(1) not in itens_na_fila:
        faltas.append((rel, numero,
                       "o item '%s' não existe em %s" % (achado.group(1), roadmap_rel)))

if not faltas:
    print("Todos os %d marcador(es) declaram teto, troca e item existente."
          % len(marcadores))
    sys.exit(0)

for rel, numero, motivo in faltas:
    print("::error file=%s,line=%d::atalho incompleto: %s" % (rel, numero, motivo))

print("")
print("%d de %d marcador(es) reprovam." % (len(faltas), len(marcadores)))
print("A forma é: atalho: <o que foi simplificado>. teto: <o limite>. "
      "troca: <o gatilho>. item: <nnn-slug>")
print("Sem gatilho, o marcador é um lembrete sem prazo. Sem item na fila, a")
print("dívida existe no código e não existe no roadmap — que é o item 11 da DoD.")
sys.exit(1)
PY
