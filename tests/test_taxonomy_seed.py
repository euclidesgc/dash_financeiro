import pytest

from app.migrate import SQL_FOLDER
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import load_seed, message, seed_taxonomy
from tests.conftest import load, narrowed, rule, transaction
from tests.test_taxonomy_remap import build_base_transactions, install_previous_vocabulary

COUNTS = (
    "SELECT (SELECT count(*) FROM category_groups), (SELECT count(*) FROM natures), "
    "(SELECT count(*) FROM essentialities), (SELECT count(*) FROM crossings), "
    "(SELECT count(*) FROM category_rules)"
)

MISMATCHED_GROUP = (
    "SELECT count(*) FROM transactions AS t JOIN category_rules AS r ON r.id = t.rule_id "
    "WHERE t.group_id != r.group_id"
)

MIGRATION_012 = (SQL_FOLDER / "012_taxonomy_tree.sql").read_text(encoding="utf-8")


@pytest.fixture
def seeded(taxonomy_conn):
    seed_taxonomy(taxonomy_conn)
    return taxonomy_conn


def test_a_second_and_a_third_seed_leave_every_count_untouched(seeded):
    before = tuple(seeded.execute(COUNTS).fetchone())
    seed_taxonomy(seeded)
    seed_taxonomy(seeded)
    assert tuple(seeded.execute(COUNTS).fetchone()) == before


def test_the_seeded_vocabulary_keeps_the_declared_order(seeded, seed):
    groups = [
        row[0] for row in seeded.execute("SELECT name FROM category_groups ORDER BY position")
    ]
    natures = [row[0] for row in seeded.execute("SELECT value FROM natures ORDER BY position")]
    essentialities = [
        row[0] for row in seeded.execute("SELECT value FROM essentialities ORDER BY position")
    ]
    assert groups == [group["name"] for group in seed["groups"]]
    assert natures == seed["natures"]
    assert essentialities == seed["essentialities"]


def test_each_vocabulary_declares_exactly_one_fallback(seeded, seed):
    for table, column, expected in (
        (
            "category_groups",
            "name",
            [group["name"] for group in seed["groups"] if group["is_fallback"]],
        ),
        ("natures", "value", [seed["fallback_nature"]]),
        ("essentialities", "value", [seed["fallback_essentiality"]]),
    ):
        rows = [
            row[0] for row in seeded.execute(f"SELECT {column} FROM {table} WHERE is_fallback = 1")
        ]
        assert rows == expected


def test_no_seeded_rule_is_born_with_the_last_essentiality(seeded, seed):
    forbidden = seed["essentialities"][-1]
    assert (
        seeded.execute(
            "SELECT count(*) FROM category_rules WHERE essentiality = ?", (forbidden,)
        ).fetchone()[0]
        == 0
    )


def test_every_seeded_rule_points_at_a_known_term(seeded):
    assert (
        seeded.execute(
            "SELECT count(*) FROM category_rules r WHERE r.group_id NOT IN "
            "(SELECT id FROM category_groups) OR r.nature NOT IN (SELECT value FROM natures) "
            "OR r.essentiality NOT IN (SELECT value FROM essentialities)"
        ).fetchone()[0]
        == 0
    )


def test_the_seed_writes_both_kinds_of_rule(seeded):
    kinds = {row[0] for row in seeded.execute("SELECT DISTINCT match_kind FROM category_rules")}
    assert len(kinds) == 2


def test_each_crossing_pairs_a_nature_with_an_essentiality(seeded, seed):
    rows = seeded.execute(
        "SELECT slug, label, nature, essentiality FROM crossings ORDER BY position"
    ).fetchall()
    assert [tuple(row) for row in rows] == [
        (entry["slug"], entry["label"], entry["nature"], entry["essentiality"])
        for entry in seed["crossings"]
    ]


def test_the_refusal_messages_name_the_value_they_refuse(seed):
    for key in seed["messages"]:
        assert message(key, "xyz").endswith("xyz")


def test_seed_taxonomy_alone_keeps_the_base_coerente_when_a_rules_group_changes(
    taxonomy_conn, seed
):
    origin, destination = seed["groups"][0]["name"], seed["groups"][1]["name"]
    nature, essentiality = seed["natures"][0], seed["essentialities"][0]
    match_value = "Categoria que muda de grupo"
    seed_taxonomy(
        taxonomy_conn, narrowed(seed, [rule("category", match_value, origin, nature, essentiality)])
    )
    load(
        taxonomy_conn,
        [
            transaction("t-moved", "2026-03-01", -10.00, categoria=match_value),
            transaction("t-unmatched", "2026-03-02", -5.00, categoria="Categoria sem regra"),
        ],
    )
    classify_all(taxonomy_conn)
    taxonomy_conn.commit()
    unmatched_group_before = taxonomy_conn.execute(
        "SELECT group_id FROM transactions WHERE pluggy_id = 't-unmatched'"
    ).fetchone()[0]

    # Reason: the group survives the reseed (it stays declared); only the
    # rule that classifies "t-moved" is reassigned to a different, also
    # surviving group — the case an earlier "group_id NOT IN declared"
    # scope let through untouched.
    seed_taxonomy(
        taxonomy_conn,
        narrowed(seed, [rule("category", match_value, destination, nature, essentiality)]),
    )

    destination_id = taxonomy_conn.execute(
        "SELECT id FROM category_groups WHERE name = ?", (destination,)
    ).fetchone()[0]
    moved = taxonomy_conn.execute(
        "SELECT group_id FROM transactions WHERE pluggy_id = 't-moved'"
    ).fetchone()[0]
    unmatched = taxonomy_conn.execute(
        "SELECT rule_id, group_id FROM transactions WHERE pluggy_id = 't-unmatched'"
    ).fetchone()

    assert moved == destination_id
    assert taxonomy_conn.execute(MISMATCHED_GROUP).fetchone()[0] == 0
    assert unmatched["rule_id"] is None
    assert unmatched["group_id"] == unmatched_group_before
    assert classify_all(taxonomy_conn) == 0


def test_seed_taxonomy_alone_reaches_a_coerente_base_against_the_owners_previous_vocabulary(
    taxonomy_conn,
):
    install_previous_vocabulary(taxonomy_conn)
    load(taxonomy_conn, build_base_transactions())
    classify_all(taxonomy_conn)
    taxonomy_conn.commit()
    total_cents_before = taxonomy_conn.execute(
        "SELECT coalesce(sum(amount_cents), 0) FROM transactions"
    ).fetchone()[0]

    seed_taxonomy(taxonomy_conn)

    assert taxonomy_conn.execute(MISMATCHED_GROUP).fetchone()[0] == 0
    total_cents_after = taxonomy_conn.execute(
        "SELECT coalesce(sum(amount_cents), 0) FROM transactions"
    ).fetchone()[0]
    assert total_cents_after == total_cents_before
    assert classify_all(taxonomy_conn) == 0


def test_the_taxonomy_tree_migracao_drops_categories_and_only_classify_all_puts_them_back(
    taxonomy_conn,
):
    seed_taxonomy(taxonomy_conn)
    declared = load_seed()["categories"]
    load(
        taxonomy_conn,
        [
            transaction(f"t-cat-{index}", "2026-03-01", -(10.00 + index), categoria=entry["name"])
            for index, entry in enumerate(declared)
        ],
    )
    classify_all(taxonomy_conn)
    taxonomy_conn.commit()
    names_before = {row[0] for row in taxonomy_conn.execute("SELECT name FROM categories")}
    assert names_before == {entry["name"] for entry in declared}

    taxonomy_conn.executescript(MIGRATION_012)
    taxonomy_conn.commit()
    assert taxonomy_conn.execute("SELECT count(*) FROM categories").fetchone()[0] == 0

    # Reason: the control positive — without this call, the equality below
    # compares the empty table the migration left against the names it
    # dropped, and fails.
    changed = classify_all(taxonomy_conn)
    taxonomy_conn.commit()

    names_after = {row[0] for row in taxonomy_conn.execute("SELECT name FROM categories")}
    assert names_after == names_before
    assert changed == 0
