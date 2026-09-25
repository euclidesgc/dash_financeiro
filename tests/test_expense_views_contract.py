import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from app.queries.expenses import View, list_expenses

# Reason: the MSW mock in src/testing/mocks/handlers.ts rewrites this split in
# TypeScript; both suites read the same case table, so a rule changed on one
# side turns the other side's test red instead of leaving the screens tested
# against a rule the API no longer has.
CONTRACT = Path(__file__).parents[1] / "src" / "testing" / "contracts" / "expense-views.json"
VIEWS: tuple[View, ...] = ("expenses", "income", "excluded")
CASES: list[dict[str, Any]] = json.loads(CONTRACT.read_text(encoding="utf-8"))["cases"]
FLAGS = {
    "own-account transfer": {"is_transfer": 1},
    "refund": {"is_refund": 1},
    "refunded outflow": {"refunded_by": "tx-refund"},
}


def _insert(conn: sqlite3.Connection, index: int, case: dict[str, Any], **flags: Any) -> None:
    row = {
        "pluggy_id": f"contract-{index}",
        "account_id": "acc-contract",
        "date": "2026-08-01",
        "description": case["name"],
        "amount_cents": case["amount_cents"],
        "not_expense_reason": case["not_expense_reason"],
        **flags,
    }
    columns = ", ".join(row)
    marks = ", ".join("?" for _ in row)
    conn.execute(f"INSERT INTO transactions ({columns}) VALUES ({marks})", tuple(row.values()))


def _placed(conn: sqlite3.Connection) -> dict[View, set[str]]:
    return {
        view: {
            item["description"]
            for item in list_expenses(conn, page=1, page_size=100, view=view).items
        }
        for view in VIEWS
    }


@pytest.fixture
def conn(taxonomy_conn: sqlite3.Connection) -> sqlite3.Connection:
    taxonomy_conn.execute(
        "INSERT INTO accounts (id, type, subtype, name, balance_cents) "
        "VALUES ('acc-contract', 'BANK', 'CHECKING_ACCOUNT', 'Conta', 0)"
    )
    return taxonomy_conn


def test_the_contract_covers_every_view_and_the_empty_split() -> None:
    placed = {view for case in CASES for view in case["views"]}
    assert placed == set(VIEWS)
    assert any(case["views"] == [] for case in CASES)


def test_the_api_places_each_contract_case_in_its_views(conn: sqlite3.Connection) -> None:
    for index, case in enumerate(CASES):
        _insert(conn, index, case)

    placed = _placed(conn)

    for case in CASES:
        found = [view for view in VIEWS if case["name"] in placed[view]]
        assert found == case["views"], case["name"]


@pytest.mark.parametrize("flags", FLAGS.values(), ids=FLAGS.keys())
def test_a_transfer_or_refund_is_in_no_view_whatever_the_case(
    conn: sqlite3.Connection, flags: dict[str, Any]
) -> None:
    for index, case in enumerate(CASES):
        _insert(conn, index, case, **flags)

    assert _placed(conn) == {view: set() for view in VIEWS}
