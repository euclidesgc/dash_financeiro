import json
import sqlite3
from pathlib import Path

from app.db import connect
from app.migrate import run_migrations
from app.queries.axes import AXES, aggregate
from app.queries.crossings import crossing
from app.queries.spending import SPENDING, total_spending_cents
from app.taxonomy.classify import classify_all
from app.taxonomy.rules import create_rule
from app.taxonomy.seed import load_seed, seed_taxonomy
from tests.conftest import load, transaction

DATA_PATH = Path(__file__).resolve().parent / "data" / "vocabulario_anterior.json"
PREVIOUS_VOCABULARY = json.loads(DATA_PATH.read_text(encoding="utf-8"))
RETIRED_GROUPS = (
    "Comer fora e lazer",
    "Serviços e assinaturas",
    "Dívidas e juros",
    "Transferências",
)
START, END = "2026-03-01", "2026-03-31"


def new_conn(tmp_path: Path, name: str) -> sqlite3.Connection:
    path = str(tmp_path / name / "dash.sqlite")
    run_migrations(path)
    return connect(path)


def install_previous_vocabulary(conn: sqlite3.Connection, data: dict = PREVIOUS_VOCABULARY) -> None:
    # Reason: a guard that shares code with the thing it guards passes in
    # green the day that code breaks — the "before" state is written by INSERT
    # of its own, never through app.taxonomy.seed.seed_taxonomy.
    conn.executemany(
        "INSERT INTO category_groups (name, position, is_fallback) VALUES (?, ?, ?)",
        [
            (group["name"], group["position"], int(bool(group["is_fallback"])))
            for group in data["groups"]
        ],
    )
    conn.executemany(
        "INSERT INTO natures (value, position, is_fallback) VALUES (?, ?, ?)",
        [
            (value, index + 1, int(value == data["fallback_nature"]))
            for index, value in enumerate(data["natures"])
        ],
    )
    conn.executemany(
        "INSERT INTO essentialities (value, position, is_fallback) VALUES (?, ?, ?)",
        [
            (value, index + 1, int(value == data["fallback_essentiality"]))
            for index, value in enumerate(data["essentialities"])
        ],
    )
    conn.executemany(
        "INSERT INTO crossings (slug, label, nature, essentiality, position) VALUES (?, ?, ?, ?, ?)",
        [
            (
                entry["slug"],
                entry["label"],
                entry["nature"],
                entry["essentiality"],
                entry["position"],
            )
            for entry in data["crossings"]
        ],
    )
    groups = {
        row["name"]: row["id"] for row in conn.execute("SELECT id, name FROM category_groups")
    }
    conn.executemany(
        "INSERT INTO category_rules (match_kind, match_value, group_id, nature, essentiality) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            (
                rule["match_kind"],
                rule["match_value"],
                groups[rule["group"]],
                rule["nature"],
                rule["essentiality"],
            )
            for rule in data["rules"]
        ],
    )
    conn.commit()


def build_base_transactions(data: dict = PREVIOUS_VOCABULARY) -> list[dict]:
    category_rules = [rule for rule in data["rules"] if rule["match_kind"] == "category"]
    rows = [
        transaction(f"t-cat-{index}", "2026-03-01", -(10.00 + index), categoria=rule["match_value"])
        for index, rule in enumerate(category_rules)
    ]
    rows.append(
        transaction(
            "t-transfer",
            "2026-03-02",
            -25.00,
            categoria="Transfer - Internal",
            eh_transferencia=True,
        )
    )
    rows.append(
        transaction("t-refund", "2026-03-03", -30.00, categoria="Groceries", eh_estorno=True)
    )
    rows.append(transaction("t-income", "2026-03-04", 500.00, categoria="Salary"))
    rows.append(transaction("t-unmatched", "2026-03-05", -15.00, categoria="Categoria sem regra"))
    return rows


def read_four_numbers(conn: sqlite3.Connection, *, start: str = START, end: str = END) -> tuple:
    total = total_spending_cents(conn, start, end)
    count = conn.execute(
        f"SELECT count(*) FROM transactions WHERE {SPENDING} AND date >= ? AND date <= ?",
        (start, end),
    ).fetchone()[0]
    corte = crossing(conn, slug="corte", start=start, end=end)
    piso = crossing(conn, slug="piso", start=start, end=end)
    return total, count, corte, piso


def test_the_seed_reconciles_a_database_seeded_with_the_previous_vocabulary(tmp_path):
    conn = new_conn(tmp_path, "reconcile")
    install_previous_vocabulary(conn)
    load(conn, build_base_transactions())
    classify_all(conn)
    conn.commit()

    seed_taxonomy(conn)
    classify_all(conn)
    conn.commit()

    assert conn.execute("SELECT count(*) FROM category_groups").fetchone()[0] == 12
    names = [row[0] for row in conn.execute("SELECT name FROM category_groups ORDER BY position")]
    assert names == [
        "Moradia",
        "Transporte",
        "Alimentação",
        "Saúde",
        "Educação",
        "Assinaturas",
        "Pessoal",
        "Financeiro",
        "Dependentes",
        "Renda",
        "Não é gasto",
        "Outros",
    ]
    assert conn.execute("SELECT count(*) FROM category_rules").fetchone()[0] == 80
    assert (
        conn.execute("SELECT count(*) FROM transactions WHERE rule_id IS NOT NULL").fetchone()[0]
        > 0
    )
    orphans = conn.execute(
        "SELECT count(*) FROM category_rules AS r LEFT JOIN category_groups AS g "
        "ON g.id = r.group_id WHERE g.id IS NULL"
    ).fetchone()[0]
    assert orphans == 0
    mismatch = conn.execute(
        "SELECT count(*) FROM transactions AS t JOIN category_rules AS r ON r.id = t.rule_id "
        "WHERE t.group_id != r.group_id"
    ).fetchone()[0]
    assert mismatch == 0
    assert classify_all(conn) == 0


def test_an_owner_written_rule_that_loses_its_group_falls_into_the_escape(tmp_path):
    conn = new_conn(tmp_path, "escape")
    install_previous_vocabulary(conn)
    load(conn, [transaction("t-1", "2026-03-01", -10.00, categoria="Categoria do dono")])
    retired_id = conn.execute(
        "SELECT id FROM category_groups WHERE name = 'Transferências'"
    ).fetchone()[0]
    create_rule(
        conn,
        match_kind="category",
        match_value="Categoria do dono",
        group_id=retired_id,
        nature="variável",
        essentiality="importante",
    )
    rule_id = conn.execute(
        "SELECT id FROM category_rules WHERE match_value = 'Categoria do dono'"
    ).fetchone()[0]
    conn.commit()

    seed_taxonomy(conn)

    row = conn.execute(
        "SELECT match_kind, match_value, group_id, nature, essentiality FROM category_rules WHERE id = ?",
        (rule_id,),
    ).fetchone()
    fallback_id = conn.execute("SELECT id FROM category_groups WHERE is_fallback = 1").fetchone()[0]
    assert (row["match_kind"], row["match_value"]) == ("category", "Categoria do dono")
    assert (row["nature"], row["essentiality"]) == ("variável", "importante")
    assert row["group_id"] == fallback_id
    transaction_group_id = conn.execute(
        "SELECT group_id FROM transactions WHERE pluggy_id = 't-1'"
    ).fetchone()[0]
    assert transaction_group_id == fallback_id
    assert classify_all(conn) == 0


def test_the_eighty_rule_tuples_are_identical_and_in_the_same_order():
    current = load_seed()
    old_rules = PREVIOUS_VOCABULARY["rules"]
    new_rules = current["rules"]
    assert len(old_rules) == 80
    assert len(new_rules) == 80
    old_tuples = [
        (rule["match_kind"], rule["match_value"], rule["nature"], rule["essentiality"])
        for rule in old_rules
    ]
    new_tuples = [
        (rule["match_kind"], rule["match_value"], rule["nature"], rule["essentiality"])
        for rule in new_rules
    ]
    assert old_tuples == new_tuples
    declared_names = {group["name"] for group in current["groups"]}
    assert {rule["group"] for rule in new_rules} <= declared_names


def test_the_four_numbers_are_identical_before_and_after(tmp_path):
    before = new_conn(tmp_path, "before")
    install_previous_vocabulary(before)
    load(before, build_base_transactions())
    classify_all(before)
    before.commit()

    after = new_conn(tmp_path, "after")
    load(after, build_base_transactions())
    seed_taxonomy(after)
    classify_all(after)
    after.commit()

    before_total, before_count, before_corte, before_piso = read_four_numbers(before)
    after_total, after_count, after_corte, after_piso = read_four_numbers(after)

    assert before_count > 0
    assert after_count > 0
    assert before_total == after_total
    assert before_count == after_count
    for before_crossing, after_crossing in ((before_corte, after_corte), (before_piso, after_piso)):
        assert before_crossing.total_cents == after_crossing.total_cents
        assert before_crossing.monthly_average_cents == after_crossing.monthly_average_cents
        assert [tuple(row) for row in before_crossing.rows] == [
            tuple(row) for row in after_crossing.rows
        ]

    ledger = (
        "SELECT t.pluggy_id, r.match_value, t.nature, t.essentiality FROM transactions AS t "
        "LEFT JOIN category_rules AS r ON r.id = t.rule_id ORDER BY t.pluggy_id"
    )
    assert [tuple(row) for row in before.execute(ledger)] == [
        tuple(row) for row in after.execute(ledger)
    ]


def test_the_three_own_account_transfer_categories_land_in_not_a_spend(tmp_path):
    conn = new_conn(tmp_path, "not-a-spend")
    seed_taxonomy(conn)

    rows = conn.execute(
        "SELECT r.match_value, g.name FROM category_rules AS r JOIN category_groups AS g "
        "ON g.id = r.group_id WHERE r.match_kind = 'category' AND r.match_value IN "
        "('Same person transfer', 'Same person transfer - CASH', 'Transfer - Internal')"
    ).fetchall()
    assert len(rows) == 3
    assert {row["name"] for row in rows} == {"Não é gasto"}


def test_the_group_axis_shows_only_the_new_vocabulary_after_the_seed_runs(tmp_path):
    before = new_conn(tmp_path, "axis-before")
    install_previous_vocabulary(before)
    load(before, build_base_transactions())
    classify_all(before)
    before.commit()

    after = new_conn(tmp_path, "axis-after")
    load(after, build_base_transactions())
    seed_taxonomy(after)
    classify_all(after)
    after.commit()

    before_rows = aggregate(before, axis=AXES[0], start=START, end=END)
    after_rows = aggregate(after, axis=AXES[0], start=START, end=END)

    assert len(before_rows) >= 1
    assert len(after_rows) >= 1
    before_entries = sum(row["entries"] for row in before_rows)
    after_entries = sum(row["entries"] for row in after_rows)
    assert before_entries > 0
    assert before_entries == after_entries
    assert sum(row["amount_cents"] for row in before_rows) == sum(
        row["amount_cents"] for row in after_rows
    )
    after_keys = {row["key"] for row in after_rows}
    assert after_keys.isdisjoint(RETIRED_GROUPS)
    declared_names = {group["name"] for group in load_seed()["groups"]}
    assert after_keys <= declared_names
    before_keys = {row["key"] for row in before_rows}
    assert before_keys & set(RETIRED_GROUPS)
