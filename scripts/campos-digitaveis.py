#!/usr/bin/env python3
"""Medidor de RF-01/RF-02: todo campo de digitação declara o que aceita.

Varre app/templates/**/*.html, ignora type="submit" e type="hidden" — não são
campos que o dono digita — e acusa todo campo restante sem maxlength, mais
todo campo de dinheiro, taxa ou prazo sem inputmode. Sai 0 sem acusação,
diferente de 0 com pelo menos uma.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_ROOT = ROOT / "app" / "templates"

_INPUT_TAG = re.compile(r"<input\b[^>]*>", re.IGNORECASE)
_ATTRIBUTE = re.compile(r'([\w-]+)\s*=\s*"([^"]*)"')

_IGNORED_TYPES = {"submit", "hidden"}
# Motivo: type="date" tem medida e teto próprios do navegador — nenhum aceita
# maxlength no widget de data, e não há forma de declarar um sem que o
# navegador o ignore. Ele conta como campo digitável (RF-01/RF-02 falam de
# todo campo), mas nunca é acusado por não ter maxlength.
_DATE_TYPE = "date"

_NUMERIC_INPUTMODES = {"decimal", "numeric"}
# Motivo: o teto de um campo de dinheiro, taxa ou prazo vem sempre de um
# destes quatro nomes em app/settings/limits.py (RF-03) — nunca de um número
# solto no template. Reconhecer o campo pelo nome do teto que ele declara é
# mais firme do que adivinhar pelo `name` do campo, e continua valendo
# quando um campo novo nascer com um `name` diferente destes.
_FINANCIAL_MAXLENGTH_MARKERS = (
    "limits.MONEY_FIELD_MAXLENGTH",
    "limits.RATE_FIELD_MAXLENGTH",
    "limits.MAX_DIGITS",
    "limits.DAY_FIELD_MAXLENGTH",
)


def _attributes(tag: str) -> dict[str, str]:
    return {name.lower(): value for name, value in _ATTRIBUTE.findall(tag)}


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _accusations(path: Path) -> tuple[int, list[str]]:
    text = path.read_text(encoding="utf-8")
    digitable = 0
    problems: list[str] = []
    for match in _INPUT_TAG.finditer(text):
        tag = match.group(0)
        attrs = _attributes(tag)
        field_type = attrs.get("type", "").lower()
        if field_type in _IGNORED_TYPES:
            continue
        digitable += 1
        location = f"{path.relative_to(ROOT)}:{_line_of(text, match.start())}"
        if field_type == _DATE_TYPE:
            continue
        maxlength = attrs.get("maxlength")
        if not maxlength:
            problems.append(f"{location}: campo sem maxlength — {' '.join(tag.split())}")
            continue
        is_financial = any(marker in maxlength for marker in _FINANCIAL_MAXLENGTH_MARKERS)
        if is_financial and attrs.get("inputmode") not in _NUMERIC_INPUTMODES:
            problems.append(
                f"{location}: campo de dinheiro, taxa ou prazo sem inputmode — "
                f"{' '.join(tag.split())}"
            )
    return digitable, problems


def main() -> int:
    total_digitable = 0
    all_problems: list[str] = []
    for path in sorted(TEMPLATES_ROOT.rglob("*.html")):
        digitable, problems = _accusations(path)
        total_digitable += digitable
        all_problems.extend(problems)
    for problem in all_problems:
        print(problem)
    print(f"campos digitáveis: {total_digitable}; sem declaração completa: {len(all_problems)}")
    return 0 if not all_problems else 1


if __name__ == "__main__":
    sys.exit(main())
