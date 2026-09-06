import re
from pathlib import Path

import pytest

from app.design.contrast import contrast_ratio

ROOT = Path(__file__).resolve().parents[1]
LANGUAGE_DOCUMENT = ROOT / "product" / "00-linguagem-visual.md"
TOKENS_STYLESHEET = ROOT / "app" / "static" / "css" / "tokens.css"

PAIR_ROW = re.compile(
    r"^\|\s*`(--[a-z0-9-]+)`\s*\|\s*`(--[a-z0-9-]+)`\s*\|\s*([^|]+?)\s*\|\s*([0-9.]+)\s*\|\s*$"
)
DECLARATION = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);")


def _section(document: str, heading: str) -> str:
    body = document.split(f"\n## {heading}\n", 1)[1]
    return body.split("\n## ", 1)[0]


def _declared_pairs() -> list[tuple[str, str, str, float]]:
    section = _section(LANGUAGE_DOCUMENT.read_text(encoding="utf-8"), "Pares de contraste")
    pairs = []
    for line in section.splitlines():
        row = PAIR_ROW.match(line)
        if row is not None:
            front, back, role, minimum = row.groups()
            pairs.append((front, back, role, float(minimum)))
    return pairs


def _block(stylesheet: str, opener: str) -> str:
    start = stylesheet.index(opener) + len(opener)
    depth = 1
    for position in range(start, len(stylesheet)):
        if stylesheet[position] == "{":
            depth += 1
        elif stylesheet[position] == "}":
            depth -= 1
            if depth == 0:
                return stylesheet[start:position]
    raise AssertionError(f"unbalanced block after {opener!r}")


def _themes() -> dict[str, dict[str, str]]:
    stylesheet = TOKENS_STYLESHEET.read_text(encoding="utf-8")
    light = dict(DECLARATION.findall(_block(stylesheet, ":root {")))
    dark = dict(light)
    dark.update(DECLARATION.findall(_block(stylesheet, "@media (prefers-color-scheme: dark) {")))
    return {"claro": light, "escuro": dark}


def _cases() -> list[tuple[str, str, str, str, float]]:
    themes = _themes()
    return [
        (theme, front, back, role, minimum)
        for theme in themes
        for front, back, role, minimum in _declared_pairs()
    ]


def test_the_known_ratio_is_the_whole_range():
    assert contrast_ratio("#000000", "#ffffff") == 21


def test_the_instrument_fails_a_pair_that_should_fail():
    assert contrast_ratio("#777777", "#888888") < 4.5


def test_the_document_declares_pairs_to_measure():
    assert _declared_pairs()


@pytest.mark.parametrize(("theme", "front", "back", "role", "minimum"), _cases())
def test_every_declared_pair_reaches_its_minimum(theme, front, back, role, minimum):
    values = _themes()[theme]
    measured = contrast_ratio(values[front], values[back])

    assert measured >= minimum, (
        f"tema {theme}: {front} sobre {back} ({role}) mede {measured:.2f}, "
        f"minimo declarado {minimum}"
    )
