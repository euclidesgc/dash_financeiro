from app.routers import rules as rules_router
from app.routers import spending as spending_router
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import load_seed, seed_labels, seed_taxonomy
from tests.conftest import load, transaction

NAMED_CATEGORIES = 76
ALL_CATEGORIES = 77
WITH_UNKNOWN = ALL_CATEGORIES + 1

ORPHAN_CATEGORIES = (
    "SELECT count(*) FROM categories WHERE group_id NOT IN (SELECT id FROM category_groups)"
)
CROSSED_PAIRS = (
    "SELECT count(*) FROM category_rules AS r JOIN categories AS c ON c.name = r.match_value "
    "WHERE r.match_kind = 'category'"
)
DISAGREEING_PAIRS = (
    "SELECT r.match_value FROM category_rules AS r JOIN categories AS c ON c.name = r.match_value "
    "WHERE r.match_kind = 'category' AND r.group_id != c.group_id"
)


def test_the_categories_seed_declares_seventy_seven_entries_inside_the_twelve_groups():
    seed = load_seed()
    categories = seed["categories"]
    declared_groups = {group["name"] for group in seed["groups"]}

    assert len(categories) == ALL_CATEGORIES
    names = [entry["name"] for entry in categories]
    assert len(set(names)) == ALL_CATEGORIES
    for entry in categories:
        assert set(entry) == {"name", "label", "group"}
        assert entry["group"] in declared_groups

    assert seed_labels() == {entry["name"]: entry["label"] for entry in categories}
    assert spending_router.LABELS == seed_labels()
    assert rules_router.LABELS == seed_labels()


def test_the_seeded_tree_covers_every_category_without_an_orphan_group(taxonomy_conn):
    seed_taxonomy(taxonomy_conn)

    total = taxonomy_conn.execute("SELECT count(*) FROM categories").fetchone()[0]
    orphans = taxonomy_conn.execute(ORPHAN_CATEGORIES).fetchone()[0]

    assert total == ALL_CATEGORIES
    assert orphans == 0


def test_the_seed_writes_the_label_of_every_category(taxonomy_conn):
    seed_taxonomy(taxonomy_conn)

    labels = {
        row["name"]: row["label"]
        for row in taxonomy_conn.execute("SELECT name, label FROM categories")
    }
    assert labels == seed_labels()
    assert (
        taxonomy_conn.execute("SELECT count(*) FROM categories WHERE is_system = 1").fetchone()[0]
        == ALL_CATEGORIES
    )


def test_every_category_rule_agrees_with_the_tree_it_points_at(taxonomy_conn):
    seed_taxonomy(taxonomy_conn)

    crossed = taxonomy_conn.execute(CROSSED_PAIRS).fetchone()[0]
    # Reason: the control positive — without it, an empty join would let the
    # absence of disagreement below pass by never comparing anything.
    assert crossed == NAMED_CATEGORIES

    disagreements = [row["match_value"] for row in taxonomy_conn.execute(DISAGREEING_PAIRS)]
    assert disagreements == []


def test_a_category_the_source_invents_lands_in_the_escape_without_breaking_classification(
    taxonomy_conn,
):
    seed_taxonomy(taxonomy_conn)
    invented = "Categoria que a fonte inventou"
    load(taxonomy_conn, [transaction("t-invented", "2026-03-01", -10.00, categoria=invented)])

    changed = classify_all(taxonomy_conn)

    assert changed == 1
    fallback_id = taxonomy_conn.execute(
        "SELECT id FROM category_groups WHERE is_fallback = 1"
    ).fetchone()[0]
    total = taxonomy_conn.execute("SELECT count(*) FROM categories").fetchone()[0]
    assert total == WITH_UNKNOWN
    row = taxonomy_conn.execute(
        "SELECT group_id FROM categories WHERE name = ?", (invented,)
    ).fetchone()
    assert row["group_id"] == fallback_id
    transaction_row = taxonomy_conn.execute(
        "SELECT rule_id, group_id FROM transactions WHERE pluggy_id = 't-invented'"
    ).fetchone()
    assert transaction_row["rule_id"] is None
    assert transaction_row["group_id"] == fallback_id


def test_a_category_demoted_to_the_escape_by_hand_is_corrected_by_the_next_seed(taxonomy_conn):
    seed_taxonomy(taxonomy_conn)
    fallback_id = taxonomy_conn.execute(
        "SELECT id FROM category_groups WHERE is_fallback = 1"
    ).fetchone()[0]
    taxonomy_conn.execute(
        "UPDATE categories SET group_id = ? WHERE name = 'Real estate financing'", (fallback_id,)
    )
    taxonomy_conn.commit()

    seed_taxonomy(taxonomy_conn)

    housing_id = taxonomy_conn.execute(
        "SELECT id FROM category_groups WHERE name = 'Moradia'"
    ).fetchone()[0]
    row = taxonomy_conn.execute(
        "SELECT group_id FROM categories WHERE name = 'Real estate financing'"
    ).fetchone()
    assert row["group_id"] == housing_id
    assert row["group_id"] != fallback_id
