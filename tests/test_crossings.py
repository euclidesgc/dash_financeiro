import pytest

from app.queries.crossings import UnknownCrossingError, crossing
from app.taxonomy.classify import classify_all
from app.taxonomy.rules import update_rule
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, rule, transaction

CUT = "corte"
FLOOR = "piso"
START = "2026-03-01"
END = "2026-08-31"
MONTHS = 6
COFFEE = "Cafeteria"
GROCER = "Mercearia"
RENT = "Aluguel"
DRUGSTORE = "Farmacia"


@pytest.fixture
def crossings(seed):
    return {entry["slug"]: entry for entry in seed["crossings"]}


@pytest.fixture
def rules(seed, crossings):
    group = seed["groups"][0]["name"]
    cut, floor = crossings[CUT], crossings[FLOOR]
    return [
        rule("category", COFFEE, group, cut["nature"], cut["essentiality"]),
        rule("category", GROCER, group, cut["nature"], cut["essentiality"]),
        rule("category", RENT, group, floor["nature"], floor["essentiality"]),
        rule("category", DRUGSTORE, group, cut["nature"], seed["fallback_essentiality"]),
    ]


@pytest.fixture
def rows():
    return [
        transaction("t-coffee-march", "2026-03-02", -10.00, categoria=COFFEE),
        transaction("t-coffee-april", "2026-04-02", -20.00, categoria=COFFEE),
        transaction("t-grocer", "2026-05-02", -50.00, categoria=GROCER),
        transaction("t-rent", "2026-03-05", -100.00, categoria=RENT),
        transaction("t-drugstore", "2026-06-02", -70.00, categoria=DRUGSTORE),
        transaction("t-income", "2026-03-06", 40.00, categoria=COFFEE),
        transaction("t-internal", "2026-03-07", -80.00, categoria=COFFEE, eh_transferencia=True),
        transaction(
            "t-refund",
            "2026-03-08",
            30.00,
            categoria=COFFEE,
            eh_estorno=True,
            estornada_por="t-debit",
        ),
        transaction("t-debit", "2026-03-08", -30.00, categoria=COFFEE, estornada_por="t-refund"),
        transaction("t-before", "2026-01-09", -90.00, categoria=COFFEE),
    ]


@pytest.fixture
def conn(taxonomy_conn, seed, rules, rows):
    connection = load(taxonomy_conn, rows)
    seed_taxonomy(connection, narrowed(seed, rules))
    classify_all(connection)
    connection.commit()
    return connection


def keys(result):
    return [row["key"] for row in result.rows]


def test_the_label_comes_from_the_table(conn, crossings):
    assert crossing(conn, slug=CUT, start=START, end=END).label == crossings[CUT]["label"]
    assert crossing(conn, slug=FLOOR, start=START, end=END).label == crossings[FLOOR]["label"]


def test_only_the_pair_of_the_slug_reaches_the_rows(conn):
    assert keys(crossing(conn, slug=CUT, start=START, end=END)) == [GROCER, COFFEE]
    assert keys(crossing(conn, slug=FLOOR, start=START, end=END)) == [RENT]


def test_the_rows_group_by_category_from_the_biggest_spending_to_the_smallest(conn):
    result = crossing(conn, slug=CUT, start=START, end=END)
    assert [(row["key"], row["amount_cents"], row["entries"]) for row in result.rows] == [
        (GROCER, -5000, 1),
        (COFFEE, -3000, 2),
    ]


def test_the_total_is_the_sum_of_the_rows(conn):
    result = crossing(conn, slug=CUT, start=START, end=END)
    assert result.total_cents == sum(row["amount_cents"] for row in result.rows) == -8000


def test_the_monthly_average_divides_the_total_by_the_months_of_the_period(conn):
    result = crossing(conn, slug=CUT, start=START, end=END)
    assert result.monthly_average_cents == round(result.total_cents / MONTHS) == -1333


def test_income_transfer_refund_and_refunded_debit_stay_out(conn):
    assert crossing(conn, slug=CUT, start=START, end=END).total_cents == -8000


def test_the_period_narrows_the_crossing(conn):
    assert crossing(conn, slug=CUT, start="2026-01-01", end=END).total_cents == -17000
    assert crossing(conn, slug=CUT, start=START, end="2026-03-31").total_cents == -1000


def test_a_crossing_without_a_row_totals_zero(conn):
    result = crossing(conn, slug=CUT, start="2025-03-01", end="2025-08-31")
    assert (result.rows, result.total_cents, result.monthly_average_cents) == ([], 0, 0)


def test_an_unknown_slug_is_refused(conn):
    with pytest.raises(UnknownCrossingError):
        crossing(conn, slug="inexistente", start=START, end=END)


def test_the_essentiality_of_a_rule_moves_a_category_into_the_crossing(conn, crossings):
    assert DRUGSTORE not in keys(crossing(conn, slug=CUT, start=START, end=END))
    rule_id = conn.execute(
        "SELECT id FROM category_rules WHERE match_kind = 'category' AND match_value = ?",
        (DRUGSTORE,),
    ).fetchone()["id"]

    assert update_rule(conn, rule_id, essentiality=crossings[CUT]["essentiality"]) == 1

    result = crossing(conn, slug=CUT, start=START, end=END)
    assert (result.rows[0]["key"], result.rows[0]["amount_cents"], result.rows[0]["entries"]) == (
        DRUGSTORE,
        -7000,
        1,
    )
    assert result.total_cents == -15000
