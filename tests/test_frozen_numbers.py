import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
EXTENSIONS = ("py", "sql", "html")

# The measured base grows in item 006, and a total frozen inside the code would
# make the query of the following month fail by being right (invariant 28):
# these numbers live in the criteria and in the tests, never in app/.
FROZEN = ("10377233", "103772", "1921711", "19217", "1942", "732", "317", "52")

_ISOLATED = re.compile(r"(?<!\d)(" + "|".join(FROZEN) + r")(?!\d)")


def scan(folder: Path, base: Path | None = None) -> list[str]:
    root = base or folder
    found = []
    for extension in EXTENSIONS:
        for path in sorted(folder.rglob(f"*.{extension}")):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                for match in _ISOLATED.finditer(line):
                    found.append(f"{path.relative_to(root)}:{number}: {match.group(1)}")
    return found


def test_no_app_file_carries_a_frozen_number():
    assert scan(APP, ROOT) == []


def test_the_scanner_reports_a_planted_number(tmp_path):
    (tmp_path / "leak.py").write_text("EXPECTED_TOTAL = -10377233\n", encoding="utf-8")
    assert scan(tmp_path) == ["leak.py:1: 10377233"]


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
    (tmp_path / "safe.py").write_text("PORT = 8000\nHASH = 1037723399\nYEAR = 19422\n", encoding="utf-8")
    assert scan(tmp_path) == []


def test_the_scanner_ignores_a_file_of_data(tmp_path):
    (tmp_path / "measured.json").write_text('{"total_cents": -10377233}\n', encoding="utf-8")
    assert scan(tmp_path) == []
