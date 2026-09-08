#!/usr/bin/env python3
#
# Confere a normalização de descrição contra o corpus real do dono.
#
# POR QUE ISTO É SCRIPT E NÃO TESTE
# A conferência vale sobre os 1.942 lançamentos reais, medidos em 05/09/2026, e
# esse arquivo mora em `data/`, que o git não versiona de propósito. Como teste,
# ele se pulava sozinho onde o dado faltava — e a integração contínua, que roda
# sem `data/` nenhum, saía verde sem ter exercitado o normalizador uma vez. Um
# teste que se pula sozinho quando o dado falta não é um teste que passou.
#
# O que a suíte prova sempre está em `tests/test_normalize.py`, sobre amostra
# versionada e sintética. O que só o corpus do dono prova está aqui, e se roda
# quando ele quiser saber se o normalizador ainda concorda com o consolidador.
#
# Uso:
#   python3 scripts/conferir-normalizacao.py [caminho-do-corpus]
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from app.ingest.normalize import normalize_description  # noqa: E402

CORPUS = RAIZ / "data" / "processed" / "transacoes.json"
MEDIDOS = 1942


def main() -> int:
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else CORPUS
    if not caminho.exists():
        print(f"corpus não encontrado: {caminho}")
        return 2

    registros = json.loads(caminho.read_text(encoding="utf-8"))
    divergentes = [
        (r["id"], r["descricao"], r["chave"])
        for r in registros
        if normalize_description(r["descricao"]) != r["chave"]
    ]
    vazios = [r["id"] for r in registros if not normalize_description(r["descricao"])]

    print(f"registros: {len(registros)} (medidos em 05/09/2026: {MEDIDOS})")
    print(f"divergem do consolidador: {len(divergentes)}")
    print(f"normalizam para nada: {len(vazios)}")
    for identificador, descricao, chave in divergentes[:20]:
        print(f"  {identificador}: “{descricao}” → esperava “{chave}”")
    if len(divergentes) > 20:
        print(f"  … e mais {len(divergentes) - 20}")

    return 1 if divergentes or vazios else 0


if __name__ == "__main__":
    raise SystemExit(main())
