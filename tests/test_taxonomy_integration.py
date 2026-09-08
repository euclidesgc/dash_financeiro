import re

from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, transaction
from tests.test_taxonomy_remap import (
    END,
    PREVIOUS_VOCABULARY,
    RETIRED_GROUPS,
    START,
    build_base_transactions,
    install_previous_vocabulary,
    new_conn,
    read_four_numbers,
)

ALL_CATEGORIES = 77
ALL_CATEGORIES_WITH_ONE_UNMATCHED = 78

# Neither vocabulary declares a single rule in the variável x supérfluo pair:
# only the owner marks supérfluo, editing a rule on the screen. Without planting
# it on both sides, the crossing that names the cut list compares zero with zero,
# and an equality between two empty crossings proves nothing at all.
CUT_RULES = ("Account fees", "Accomodation")


def mark_as_cut(conn) -> int:
    changed = conn.execute(
        "UPDATE category_rules SET nature = 'variável', essentiality = 'supérfluo' "
        f"WHERE match_kind = 'category' AND match_value IN ({','.join('?' * len(CUT_RULES))})",
        CUT_RULES,
    ).rowcount
    conn.commit()
    return changed


LOGIN = "teste-023"
PASSWORD = "senha-teste-023-taxonomia"
SCREEN = "/gastos"
TABLE = f"{SCREEN}/tabela"

CELL_LABEL = re.compile(r'<span class="cell-label">([^<]*)</span>')
NEW_VOCABULARY_ONLY_GROUPS = (
    "Assinaturas",
    "Pessoal",
    "Financeiro",
    "Dependentes",
    "Renda",
    "Não é gasto",
)


def test_the_four_numbers_agree_with_all_migrations_applied_and_the_tree_seeded(tmp_path):
    before = new_conn(tmp_path, "integration-before")
    install_previous_vocabulary(before)
    load(before, build_base_transactions())
    assert mark_as_cut(before) == len(CUT_RULES)
    classify_all(before)
    before.commit()

    after = new_conn(tmp_path, "integration-after")
    load(after, build_base_transactions())
    seed_taxonomy(after)
    assert mark_as_cut(after) == len(CUT_RULES)
    classify_all(after)
    after.commit()

    # The control positive: without it, the digit-by-digit equality below could
    # pass by comparing a tree that was never actually seeded in this database.
    categories_total = after.execute("SELECT count(*) FROM categories").fetchone()[0]
    assert categories_total == ALL_CATEGORIES_WITH_ONE_UNMATCHED

    before_total, before_count, before_corte, before_piso = read_four_numbers(before)
    after_total, after_count, after_corte, after_piso = read_four_numbers(after)

    assert after_count > 0
    # The cut list has to carry content on both sides, or the equality below is
    # an equality between two empty crossings.
    assert len(after_corte.rows) == len(CUT_RULES)
    assert after_corte.total_cents < 0
    assert before_total == after_total
    assert before_count == after_count
    for before_crossing, after_crossing in ((before_corte, after_corte), (before_piso, after_piso)):
        assert before_crossing.total_cents == after_crossing.total_cents
        assert before_crossing.monthly_average_cents == after_crossing.monthly_average_cents
        assert [tuple(row) for row in before_crossing.rows] == [
            tuple(row) for row in after_crossing.rows
        ]


def test_seed_taxonomy_repoints_categories_off_a_retiring_group_without_a_foreign_key_error(
    tmp_path,
):
    conn = new_conn(tmp_path, "categories-retire")
    install_previous_vocabulary(conn)
    groups = {
        row["name"]: row["id"] for row in conn.execute("SELECT id, name FROM category_groups")
    }
    category_rules = [
        rule for rule in PREVIOUS_VOCABULARY["rules"] if rule["match_kind"] == "category"
    ]
    assert set(RETIRED_GROUPS) <= {rule["group"] for rule in category_rules}
    conn.executemany(
        "INSERT INTO categories (name, group_id) VALUES (?, ?)",
        [(rule["match_value"], groups[rule["group"]]) for rule in category_rules],
    )
    conn.commit()

    seed_taxonomy(conn)

    assert conn.execute("SELECT count(*) FROM category_groups").fetchone()[0] == 12
    # The control positive: without it, the absence of orphans below would pass
    # over a categories table the seed never actually repopulated.
    assert conn.execute("SELECT count(*) FROM categories").fetchone()[0] == ALL_CATEGORIES
    orphans = conn.execute(
        "SELECT count(*) FROM categories AS c LEFT JOIN category_groups AS g "
        "ON g.id = c.group_id WHERE g.id IS NULL"
    ).fetchone()[0]
    assert orphans == 0
    not_a_spend_id = conn.execute(
        "SELECT id FROM category_groups WHERE name = 'Não é gasto'"
    ).fetchone()[0]
    row = conn.execute(
        "SELECT group_id FROM categories WHERE name = 'Same person transfer'"
    ).fetchone()
    assert row["group_id"] == not_a_spend_id


def test_the_table_shows_only_the_previous_vocabulary_when_only_migrations_ran(
    tmp_path, monkeypatch
):
    db_path = str(tmp_path / "dash.sqlite")
    monkeypatch.setenv("DASH_DB_PATH", db_path)
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste-023")
    app = create_app()

    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    install_previous_vocabulary(conn)
    rows = [
        transaction("t-eating", START, -10.00, categoria="Eating out"),
        transaction("t-internet", START, -20.00, categoria="Internet"),
        transaction("t-bank-fees", START, -30.00, categoria="Bank fees"),
    ]
    load(conn, rows)
    for pluggy_id, category_name in (
        ("t-eating", "Eating out"),
        ("t-internet", "Internet"),
        ("t-bank-fees", "Bank fees"),
    ):
        rule = conn.execute(
            "SELECT id, group_id, nature, essentiality FROM category_rules "
            "WHERE match_kind = 'category' AND match_value = ?",
            (category_name,),
        ).fetchone()
        conn.execute(
            "UPDATE transactions SET rule_id = ?, group_id = ?, nature = ?, essentiality = ? "
            "WHERE pluggy_id = ?",
            (rule["id"], rule["group_id"], rule["nature"], rule["essentiality"], pluggy_id),
        )
    conn.commit()
    conn.close()

    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        response = opened.get(TABLE, params={"eixo": "grupo", "inicio": START, "fim": END})

    assert response.status_code == 200
    labels = set(CELL_LABEL.findall(response.text))
    assert {"Comer fora e lazer", "Serviços e assinaturas", "Dívidas e juros"} <= labels
    assert labels.isdisjoint(NEW_VOCABULARY_ONLY_GROUPS)
