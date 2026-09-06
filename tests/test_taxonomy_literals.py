from pathlib import Path

import pytest

from app.taxonomy.seed import load_seed

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
EXTENSIONS = ("py", "sql", "html")
GROUPS = 10
TERMS = 3
NAMED_CATEGORIES = 76


def vocabulary(seed: dict) -> set[str]:
    return (
        {group["name"] for group in seed["groups"]}
        | set(seed["natures"])
        | set(seed["essentialities"])
        | {rule["match_value"] for rule in seed["rules"] if rule["match_kind"] == "category"}
    )


def scan(folder: Path, terms: set[str], base: Path | None = None) -> list[str]:
    root = base or folder
    found = []
    for extension in EXTENSIONS:
        for path in sorted(folder.rglob(f"*.{extension}")):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                for term in sorted(terms):
                    if term in line:
                        found.append(f"{path.relative_to(root)}:{number}: {term}")
    return found


@pytest.fixture(scope="module")
def terms():
    return vocabulary(load_seed())


def test_the_vocabulary_covers_group_nature_essentiality_and_category():
    seed = load_seed()
    assert len(seed["groups"]) == GROUPS
    assert len(seed["natures"]) == TERMS
    assert len(seed["essentialities"]) == TERMS
    assert len([rule for rule in seed["rules"] if rule["match_kind"] == "category"]) == (
        NAMED_CATEGORIES
    )


def test_no_app_file_carries_a_vocabulary_term_as_a_literal(terms):
    assert scan(APP, terms, ROOT) == []


def test_the_scanner_reports_a_planted_term(tmp_path, terms):
    planted = sorted(terms)[0]
    (tmp_path / "leak.py").write_text(
        f'QUERY = "SELECT 1 FROM t WHERE c = \'{planted}\'"\n', encoding="utf-8"
    )
    assert scan(tmp_path, terms) == [f"leak.py:1: {planted}"]


def test_the_scanner_ignores_a_file_of_data(tmp_path, terms):
    planted = sorted(terms)[0]
    (tmp_path / "leak.json").write_text(f'{{"name": "{planted}"}}\n', encoding="utf-8")
    assert scan(tmp_path, terms) == []
