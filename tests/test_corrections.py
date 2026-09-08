import pytest

from app.queries.reach import holders, payee_reach
from app.taxonomy import classify as classify_module
from app.taxonomy.classify import classify_all
from app.taxonomy.rules import RuleError, correct_payee, expression_for
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, rule, transaction

CATEGORY = "Categoria da fonte"
FINANCEIRO = "Financeiro"
PESSOAL = "Pessoal"
ASSINATURAS = "Assinaturas"


def group_id(conn, name):
    return conn.execute("SELECT id FROM category_groups WHERE name = ?", (name,)).fetchone()[0]


def snapshot(conn):
    return [
        tuple(row)
        for row in conn.execute(
            "SELECT id, rule_id, group_id, nature, essentiality FROM transactions ORDER BY id"
        )
    ]


@pytest.fixture
def rows():
    return [
        transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria=CATEGORY),
        transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria=CATEGORY),
        transaction(
            "t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria=CATEGORY
        ),
    ]


@pytest.fixture
def base(taxonomy_conn, seed, rows):
    conn = load(taxonomy_conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify_all(conn)
    conn.commit()
    return conn


def test_a_fresh_correction_reaches_exactly_what_the_preview_promised(base):
    before = payee_reach(base, "mercado livre")

    result = correct_payee(
        base,
        payee="mercado livre",
        group_id=group_id(base, PESSOAL),
        nature="variável",
        essentiality="supérfluo",
    )

    assert (result.entries, result.amount_cents) == (before["entries"], before["amount_cents"])
    assert (result.entries, result.amount_cents) == (2, -15000)
    assert expression_for("mercado livre").startswith("^")
    assert expression_for("mercado livre").endswith("$")
    written = base.execute(
        "SELECT match_value FROM category_rules WHERE match_kind = 'description'"
    ).fetchall()
    assert [row["match_value"] for row in written] == [expression_for("mercado livre")]
    reclassified_rule = base.execute(
        "SELECT count(*) FROM transactions WHERE rule_id = "
        "(SELECT id FROM category_rules WHERE match_kind = 'description')"
    ).fetchone()[0]
    assert reclassified_rule == 2
    sibling = base.execute("SELECT rule_id FROM transactions WHERE pluggy_id = 't-mlp'").fetchone()
    assert sibling["rule_id"] is None


def test_a_rule_of_lower_precedence_already_holding_the_payee_reaches_zero(
    taxonomy_conn, seed, rows
):
    conn = load(taxonomy_conn, rows)
    seed_taxonomy(
        conn, narrowed(seed, [rule("description", "^mercado", FINANCEIRO, "fixa", "essencial")])
    )
    classify_all(conn)
    conn.commit()

    result = correct_payee(
        conn,
        payee="mercado livre",
        group_id=group_id(conn, PESSOAL),
        nature="variável",
        essentiality="supérfluo",
    )

    assert result.entries == 0
    assert conn.execute("SELECT count(*) FROM category_rules").fetchone()[0] == 2
    written = conn.execute(
        "SELECT match_kind FROM category_rules WHERE id = ?", (result.rule_id,)
    ).fetchone()
    assert written["match_kind"] == "description"
    still = payee_reach(conn, "mercado livre")
    assert still["entries"] == 2
    found = holders(conn, payee="mercado livre", rule_id=result.rule_id)
    assert [row["match_value"] for row in found] == ["^mercado"]


def test_correcting_the_same_payee_twice_updates_instead_of_creating(base):
    before = base.execute("SELECT count(*) FROM category_rules").fetchone()[0]

    first = correct_payee(
        base,
        payee="mercado livre",
        group_id=group_id(base, PESSOAL),
        nature="variável",
        essentiality="supérfluo",
    )
    assert base.execute("SELECT count(*) FROM category_rules").fetchone()[0] == before + 1
    assert first.created is True

    second = correct_payee(
        base,
        payee="mercado livre",
        group_id=group_id(base, ASSINATURAS),
        nature="variável",
        essentiality="supérfluo",
    )
    assert base.execute("SELECT count(*) FROM category_rules").fetchone()[0] == before + 1
    assert second.created is False

    named = base.execute(
        "SELECT g.name FROM category_rules AS r JOIN category_groups AS g ON g.id = r.group_id "
        "WHERE r.match_kind = 'description'"
    ).fetchall()
    assert [row["name"] for row in named] == [ASSINATURAS]


def test_a_new_group_is_created_at_the_top_of_the_tree_and_carries_the_payee(base):
    top = base.execute("SELECT max(position) FROM category_groups").fetchone()[0]

    correct_payee(
        base,
        payee="mercado livre",
        group_id=None,
        new_group="Educação do filho",
        nature="variável",
        essentiality="supérfluo",
    )

    created = base.execute(
        "SELECT position, is_fallback FROM category_groups WHERE name = 'Educação do filho'"
    ).fetchone()
    assert (created["position"], created["is_fallback"]) == (top + 1, 0)
    carried = base.execute(
        "SELECT count(*) FROM transactions WHERE group_id = "
        "(SELECT id FROM category_groups WHERE name = 'Educação do filho')"
    ).fetchone()[0]
    assert carried == 2


def test_the_two_refusals_leave_no_rule_and_no_group_beside_the_positive_control(base):
    groups_before = base.execute("SELECT count(*) FROM category_groups").fetchone()[0]

    with pytest.raises(RuleError) as invalid_group:
        correct_payee(
            base,
            payee="mercado livre",
            group_id=9999,
            nature="variável",
            essentiality="supérfluo",
        )
    assert str(invalid_group.value) == "grupo inválido: 9999"

    with pytest.raises(RuleError) as unknown_payee:
        correct_payee(
            base,
            payee="beneficiario que nao existe",
            group_id=group_id(base, PESSOAL),
            nature="variável",
            essentiality="supérfluo",
        )
    assert str(unknown_payee.value) == "beneficiário desconhecido: beneficiario que nao existe"

    assert (
        base.execute(
            "SELECT count(*) FROM category_rules WHERE match_kind = 'description'"
        ).fetchone()[0]
        == 0
    )
    assert base.execute("SELECT count(*) FROM category_groups").fetchone()[0] == groups_before

    correct_payee(
        base,
        payee="mercado livre",
        group_id=group_id(base, PESSOAL),
        nature="variável",
        essentiality="supérfluo",
    )
    assert (
        base.execute(
            "SELECT count(*) FROM category_rules WHERE match_kind = 'description'"
        ).fetchone()[0]
        == 1
    )


def test_a_broken_reclassification_leaves_the_rule_the_group_and_every_row_untouched(
    base, monkeypatch
):
    rules_before = base.execute("SELECT count(*) FROM category_rules").fetchone()[0]
    groups_before = base.execute("SELECT count(*) FROM category_groups").fetchone()[0]
    rows_before = snapshot(base)

    def half_written_then_broken(conn):
        conn.execute(
            "UPDATE transactions SET rule_id = NULL, group_id = NULL, nature = NULL, "
            "essentiality = NULL WHERE id = (SELECT min(id) FROM transactions)"
        )
        raise RuntimeError("reclassification broke halfway")

    monkeypatch.setattr(classify_module, "classify_all", half_written_then_broken)

    with pytest.raises(RuntimeError):
        correct_payee(
            base,
            payee="mercado livre",
            group_id=None,
            new_group="Educação do filho",
            nature="variável",
            essentiality="supérfluo",
        )

    assert base.execute("SELECT count(*) FROM category_rules").fetchone()[0] == rules_before
    assert base.execute("SELECT count(*) FROM category_groups").fetchone()[0] == groups_before
    assert (
        base.execute(
            "SELECT count(*) FROM category_groups WHERE name = 'Educação do filho'"
        ).fetchone()[0]
        == 0
    )
    assert snapshot(base) == rows_before
