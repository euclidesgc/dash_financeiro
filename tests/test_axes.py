import pytest

from app.ingest.normalize import normalize_description
from app.queries.axes import AXES, InvalidPeriodError, UnknownAxisError, aggregate, transactions_of
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import ACCOUNT, load, narrowed, rule, transaction

START = "2026-03-01"
END = "2026-08-31"

GROUP = "grupo"
CATEGORY = "categoria"
PAYEE = "beneficiario"
NATURE = "natureza"
ESSENTIALITY = "essencialidade"

COFFEE = "Cafeteria"
GROCER = "Mercearia"
RENT = "Aluguel"

BAKERY = "padaria central"
MARKET = "mercado do bairro"
LANDLORD = "aluguel do imovel"

TOTAL = -18000
ENTRIES = 4


@pytest.fixture
def terms(seed):
    return {
        "groups": [entry["name"] for entry in seed["groups"][:2]],
        "natures": seed["natures"][:2],
        "essentialities": seed["essentialities"][:2],
    }


@pytest.fixture
def rules(terms):
    groups, natures, essentialities = (
        terms["groups"],
        terms["natures"],
        terms["essentialities"],
    )
    return [
        rule("category", COFFEE, groups[0], natures[0], essentialities[0]),
        rule("category", GROCER, groups[1], natures[1], essentialities[1]),
        rule("category", RENT, groups[1], natures[1], essentialities[0]),
    ]


@pytest.fixture
def rows():
    return [
        transaction("t-coffee-march", "2026-03-02", -10.00, categoria=COFFEE, descricao=BAKERY),
        transaction("t-coffee-april", "2026-04-02", -20.00, categoria=COFFEE, descricao=BAKERY),
        transaction("t-grocer", "2026-05-02", -50.00, categoria=GROCER, descricao=MARKET),
        transaction("t-rent", "2026-03-05", -100.00, categoria=RENT, descricao=LANDLORD),
        transaction("t-income", "2026-03-06", 40.00, categoria=COFFEE, descricao=BAKERY),
        transaction(
            "t-internal",
            "2026-03-07",
            -80.00,
            categoria=COFFEE,
            descricao=BAKERY,
            eh_transferencia=True,
        ),
        transaction(
            "t-refund",
            "2026-03-08",
            30.00,
            categoria=COFFEE,
            descricao=BAKERY,
            eh_estorno=True,
            estornada_por="t-debit",
        ),
        transaction(
            "t-debit",
            "2026-03-08",
            -30.00,
            categoria=COFFEE,
            descricao=BAKERY,
            estornada_por="t-refund",
        ),
        transaction("t-before", "2026-01-09", -90.00, categoria=COFFEE, descricao=BAKERY),
    ]


@pytest.fixture
def conn(taxonomy_conn, seed, rules, rows):
    connection = load(taxonomy_conn, rows)
    seed_taxonomy(connection, narrowed(seed, rules))
    classify_all(connection)
    connection.commit()
    return connection


def triples(conn, axis, start=START, end=END):
    return [
        (row["key"], row["amount_cents"], row["entries"])
        for row in aggregate(conn, axis=axis, start=start, end=end)
    ]


def test_the_five_axes_are_declared_in_the_interface_language():
    assert AXES == (GROUP, CATEGORY, PAYEE, NATURE, ESSENTIALITY)


def test_the_five_axes_repartition_the_same_total(conn):
    sums = {
        (
            sum(row["amount_cents"] for row in aggregate(conn, axis=axis, start=START, end=END)),
            sum(row["entries"] for row in aggregate(conn, axis=axis, start=START, end=END)),
        )
        for axis in AXES
    }
    assert sums == {(TOTAL, ENTRIES)}


def test_the_category_axis_goes_from_the_biggest_spending_to_the_smallest(conn):
    assert triples(conn, CATEGORY) == [(RENT, -10000, 1), (GROCER, -5000, 1), (COFFEE, -3000, 2)]


def test_the_group_axis_carries_the_name_of_the_group(conn, terms):
    first, second = terms["groups"]
    assert triples(conn, GROUP) == [(second, -15000, 2), (first, -3000, 2)]


def test_the_payee_axis_groups_by_the_normalized_description(conn):
    assert triples(conn, PAYEE) == [
        (normalize_description(LANDLORD), -10000, 1),
        (normalize_description(MARKET), -5000, 1),
        (normalize_description(BAKERY), -3000, 2),
    ]


def test_the_nature_and_the_essentiality_axes_cut_the_same_total_differently(conn, terms):
    natures, essentialities = terms["natures"], terms["essentialities"]
    assert triples(conn, NATURE) == [(natures[1], -15000, 2), (natures[0], -3000, 2)]
    assert triples(conn, ESSENTIALITY) == [
        (essentialities[0], -13000, 3),
        (essentialities[1], -5000, 1),
    ]


def test_income_transfer_refund_and_refunded_debit_stay_out_of_every_axis(conn):
    for axis in AXES:
        rows = aggregate(conn, axis=axis, start=START, end=END)
        assert [row for row in rows if row["amount_cents"] >= 0] == []
        assert sum(row["amount_cents"] for row in rows) == TOTAL


def test_the_period_narrows_the_aggregate(conn):
    assert triples(conn, CATEGORY, start="2026-01-01") == [
        (COFFEE, -12000, 3),
        (RENT, -10000, 1),
        (GROCER, -5000, 1),
    ]
    assert triples(conn, CATEGORY, end="2026-03-31") == [(RENT, -10000, 1), (COFFEE, -1000, 1)]
    assert triples(conn, CATEGORY, start="2025-01-01", end="2025-12-31") == []


def test_an_axis_outside_the_five_is_refused_naming_the_accepted_ones(conn):
    with pytest.raises(UnknownAxisError) as refused:
        aggregate(conn, axis="cor", start=START, end=END)
    assert str(refused.value) == (
        "eixo inválido: cor. Eixos aceitos: grupo, categoria, beneficiario, natureza, "
        "essencialidade"
    )


def test_an_end_before_the_start_is_refused_naming_both_fields(conn):
    with pytest.raises(InvalidPeriodError) as refused:
        aggregate(conn, axis=GROUP, start=START, end="2026-01-31")
    assert str(refused.value) == "período inválido: fim (2026-01-31) anterior a inicio (2026-03-01)"


def test_a_date_that_is_not_a_date_is_refused_naming_the_field(conn):
    with pytest.raises(InvalidPeriodError) as start_refused:
        aggregate(conn, axis=GROUP, start="2026-13-01", end=END)
    assert str(start_refused.value) == "data inválida: inicio (2026-13-01)"
    with pytest.raises(InvalidPeriodError) as end_refused:
        aggregate(conn, axis=GROUP, start=START, end="ontem")
    assert str(end_refused.value) == "data inválida: fim (ontem)"


def test_the_open_list_carries_date_description_account_and_amount(conn):
    opened = transactions_of(conn, axis=CATEGORY, key=COFFEE, start=START, end=END)
    assert [
        (row["date"], row["description"], row["account"], row["amount_cents"]) for row in opened
    ] == [
        ("2026-03-02", BAKERY, ACCOUNT["name"], -1000),
        ("2026-04-02", BAKERY, ACCOUNT["name"], -2000),
    ]


def test_the_open_list_sums_the_row_it_came_from_in_every_axis(conn):
    for axis in AXES:
        for row in aggregate(conn, axis=axis, start=START, end=END):
            opened = transactions_of(conn, axis=axis, key=row["key"], start=START, end=END)
            assert len(opened) == row["entries"]
            assert sum(line["amount_cents"] for line in opened) == row["amount_cents"]


def test_the_open_list_refuses_the_same_axis_and_period_the_aggregate_refuses(conn):
    with pytest.raises(UnknownAxisError):
        transactions_of(conn, axis="cor", key=COFFEE, start=START, end=END)
    with pytest.raises(InvalidPeriodError):
        transactions_of(conn, axis=CATEGORY, key=COFFEE, start=START, end="2026-01-31")


def test_a_key_outside_the_axis_opens_an_empty_list(conn):
    assert transactions_of(conn, axis=CATEGORY, key="Inexistente", start=START, end=END) == []
