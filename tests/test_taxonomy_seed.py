import pytest

from app.taxonomy.seed import message, seed_taxonomy

COUNTS = (
    "SELECT (SELECT count(*) FROM category_groups), (SELECT count(*) FROM natures), "
    "(SELECT count(*) FROM essentialities), (SELECT count(*) FROM crossings), "
    "(SELECT count(*) FROM category_rules)"
)


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
