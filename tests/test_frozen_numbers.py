import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
EXTENSIONS = ("py", "sql", "html")

# The measured base grows in item 006, and a total frozen inside the code would
# make the query of the following month fail by being right (invariant 28):
# these numbers live in the criteria and in the tests, never in app/.
FROZEN = (
    "10377233",
    "103772",
    "1921711",
    "19217",
    "1942",
    "732",
    "317",
    "52",
    "1242782",
    "12427",
    "37482",
    "109963",
    "224569",
    "246720",
    "14106",
    "12727",
)

# Small counts are only swept inside the files of item 003: 100 and 32 already
# live legitimately in app/routers/render.py and app/config.py, and a scanner
# that fails the innocent is switched off in the first week.
ITEM_COUNTS = ("100", "55", "32", "6")

ITEM_PATHS = (
    APP / "commitments",
    APP / "migrations" / "sql" / "004_commitments.sql",
    APP / "routers" / "commitments.py",
    APP / "templates" / "comprometido.html",
    APP / "templates" / "fragments" / "comprometido_assinaturas.html",
    APP / "templates" / "fragments" / "comprometido_parcelamentos.html",
    APP / "templates" / "fragments" / "comprometido_dispensadas.html",
    APP / "templates" / "fragments" / "comprometido_calendario.html",
)


def _expression(numbers: tuple[str, ...]) -> re.Pattern[str]:
    return re.compile(r"(?<!\d)(" + "|".join(numbers) + r")(?!\d)")


def _findings(path: Path, base: Path, expression: re.Pattern[str]) -> list[str]:
    found = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for match in expression.finditer(line):
            found.append(f"{path.relative_to(base)}:{number}: {match.group(1)}")
    return found


def scan(folder: Path, base: Path | None = None, numbers: tuple[str, ...] = FROZEN) -> list[str]:
    root = base or folder
    expression = _expression(numbers)
    found = []
    for extension in EXTENSIONS:
        for path in sorted(folder.rglob(f"*.{extension}")):
            found.extend(_findings(path, root, expression))
    return found


def scan_paths(paths, base: Path, numbers: tuple[str, ...]) -> list[str]:
    expression = _expression(numbers)
    found = []
    for path in paths:
        if path.is_dir():
            for extension in EXTENSIONS:
                for inner in sorted(path.rglob(f"*.{extension}")):
                    found.extend(_findings(inner, base, expression))
        elif path.is_file():
            found.extend(_findings(path, base, expression))
    return found


def test_no_app_file_carries_a_frozen_number():
    assert scan(APP, ROOT) == []


def test_no_file_of_the_item_carries_a_frozen_count():
    assert scan_paths(ITEM_PATHS, ROOT, ITEM_COUNTS) == []


def test_the_item_scanner_reports_a_planted_count(tmp_path):
    planted = tmp_path / "leak.py"
    planted.write_text("LIVE_INSTALLMENTS = 6\n", encoding="utf-8")
    assert scan_paths([planted], tmp_path, ITEM_COUNTS) == ["leak.py:1: 6"]


def test_the_item_scanner_reads_every_count_of_the_list(tmp_path):
    planted = tmp_path / "leak.html"
    planted.write_text(
        "".join(f"<span>{number}</span>\n" for number in ITEM_COUNTS), encoding="utf-8"
    )
    assert scan_paths([planted], tmp_path, ITEM_COUNTS) == [
        f"leak.html:{line}: {number}" for line, number in enumerate(ITEM_COUNTS, start=1)
    ]


def test_the_scanner_reports_a_planted_number(tmp_path):
    (tmp_path / "leak.py").write_text("EXPECTED_TOTAL = -10377233\n", encoding="utf-8")
    assert scan(tmp_path) == ["leak.py:1: 10377233"]


def test_the_scanner_reports_a_planted_total_of_this_item(tmp_path):
    (tmp_path / "leak.py").write_text("COMMITTED_CENTS = -1242782\n", encoding="utf-8")
    assert scan(tmp_path) == ["leak.py:1: 1242782"]


def test_the_scanner_reports_a_planted_count_inside_a_query(tmp_path):
    (tmp_path / "leak.sql").write_text("SELECT 1 FROM t LIMIT 732;\n", encoding="utf-8")
    assert scan(tmp_path) == ["leak.sql:1: 732"]


def test_the_scanner_reads_every_number_of_the_list(tmp_path):
    (tmp_path / "leak.html").write_text(
        "".join(f"<span>{number}</span>\n" for number in FROZEN), encoding="utf-8"
    )
    assert scan(tmp_path) == [
        f"leak.html:{line}: {number}" for line, number in enumerate(FROZEN, start=1)
    ]


def test_a_longer_number_that_merely_contains_one_of_them_is_not_a_finding(tmp_path):
    (tmp_path / "safe.py").write_text(
        "PORT = 8000\nHASH = 1037723399\nYEAR = 19422\nCODE = 124278299\n", encoding="utf-8"
    )
    assert scan(tmp_path) == []


def test_the_scanner_ignores_a_file_of_data(tmp_path):
    (tmp_path / "measured.json").write_text('{"total_cents": -10377233}\n', encoding="utf-8")
    assert scan(tmp_path) == []
