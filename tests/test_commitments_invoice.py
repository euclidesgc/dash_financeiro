from datetime import date

from app.commitments.engine import recompute
from app.commitments.invoice import invoice_curve
from app.commitments.live import installments
from app.taxonomy import classify
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, transaction

REFERENCE = date(2026, 9, 5)

_AZUL_ACCOUNT = (
    "INSERT INTO accounts (id, name, type, balance_cents) "
    "VALUES ('acc-azul', 'Cartão Azul', 'CREDIT', -100000)"
)
_LOJA_AZUL = (
    "INSERT INTO commitments (kind, series_key, description, account, amount_cents, "
    "last_seen_date, installment_total, installments_left, ends_month) VALUES "
    "('installment', 'loja azul', 'Loja Azul', 'Cartão Azul', -12000, '2026-08-11', "
    "24, 3, '2026-11')"
)


def _card(result, name):
    return next(card for card in result["cards"] if card["name"] == name)


def _months(card):
    return [month["month"] for month in card["months"]]


def _totals(card):
    return [month["total_cents"] for month in card["months"]]


def test_the_same_series_moves_a_month_when_the_closing_day_moves(taxonomy_conn):
    conn = taxonomy_conn
    conn.executescript(f"{_AZUL_ACCOUNT}; {_LOJA_AZUL};")
    conn.execute("INSERT INTO cards (account_id, closing_day, due_day) VALUES ('acc-azul', 5, 25)")
    conn.commit()

    card = _card(invoice_curve(conn, today=REFERENCE), "Cartão Azul")
    assert _months(card) == ["2026-09", "2026-10", "2026-11", "2026-12"]
    assert _totals(card) == [0, -12000, -12000, -12000]

    conn.execute("UPDATE cards SET closing_day = 20 WHERE account_id = 'acc-azul'")
    conn.commit()
    card = _card(invoice_curve(conn, today=REFERENCE), "Cartão Azul")
    assert _months(card) == ["2026-09", "2026-10", "2026-11"]
    assert _totals(card) == [-12000, -12000, -12000]


def test_the_same_series_moves_a_month_when_the_due_day_moves_and_the_sum_holds(taxonomy_conn):
    conn = taxonomy_conn
    conn.executescript(f"{_AZUL_ACCOUNT}; {_LOJA_AZUL};")
    conn.execute("INSERT INTO cards (account_id, closing_day, due_day) VALUES ('acc-azul', 20, 25)")
    conn.commit()

    card = _card(invoice_curve(conn, today=REFERENCE), "Cartão Azul")
    assert _months(card) == ["2026-09", "2026-10", "2026-11"]
    assert _totals(card) == [-12000, -12000, -12000]
    assert card["remaining_cents"] == -36000

    conn.execute("UPDATE cards SET due_day = 5 WHERE account_id = 'acc-azul'")
    conn.commit()
    card = _card(invoice_curve(conn, today=REFERENCE), "Cartão Azul")
    assert _months(card) == ["2026-09", "2026-10", "2026-11", "2026-12"]
    assert _totals(card) == [0, -12000, -12000, -12000]
    assert card["remaining_cents"] == -36000


def test_the_four_states_of_known_and_unknown_days(taxonomy_conn):
    conn = taxonomy_conn
    conn.executescript(f"{_AZUL_ACCOUNT}; {_LOJA_AZUL};")
    conn.commit()

    card = _card(invoice_curve(conn, today=REFERENCE), "Cartão Azul")
    assert card["closing_day"] is None
    assert card["due_day"] is None
    assert card["assumed"] is True
    assert _months(card) == ["2026-09", "2026-10", "2026-11"]
    assert card["last_invoice"] == "2026-11"

    conn.execute(
        "INSERT INTO cards (account_id, closing_day, due_day) VALUES ('acc-azul', 5, NULL)"
    )
    conn.commit()
    card = _card(invoice_curve(conn, today=REFERENCE), "Cartão Azul")
    assert card["assumed"] is True
    assert card["last_invoice"] == "2026-12"

    conn.execute("UPDATE cards SET closing_day = NULL, due_day = 15 WHERE account_id = 'acc-azul'")
    conn.commit()
    card = _card(invoice_curve(conn, today=REFERENCE), "Cartão Azul")
    assert card["assumed"] is True
    assert card["last_invoice"] == "2026-11"

    conn.execute("UPDATE cards SET closing_day = 5, due_day = 15 WHERE account_id = 'acc-azul'")
    conn.commit()
    card = _card(invoice_curve(conn, today=REFERENCE), "Cartão Azul")
    assert card["assumed"] is False
    assert card["last_invoice"] == "2026-12"


def _two_cards_three_series(conn):
    conn.executescript(
        "INSERT INTO accounts (id, name, type, balance_cents) VALUES "
        "('acc-azul', 'Cartão Azul', 'CREDIT', -100000), "
        "('acc-roxo', 'Cartão Roxo', 'CREDIT', -50000);"
        "INSERT INTO cards (account_id, closing_day, due_day) VALUES ('acc-azul', 5, 15);"
        "INSERT INTO commitments (kind, series_key, description, account, amount_cents, "
        "last_seen_date, installment_total, installments_left, ends_month) VALUES "
        "('installment', 'loja azul', 'Loja Azul', 'Cartão Azul', -12000, '2026-08-11', "
        "24, 3, '2026-11'), "
        "('installment', 'posto azul', 'Posto Azul', 'Cartão Azul', -5000, '2026-09-02', "
        "6, 2, '2026-11'), "
        "('installment', 'loja roxa', 'Loja Roxa', 'Cartão Roxo', -20000, '2026-08-20', "
        "10, 1, '2026-09');"
    )
    conn.commit()


def test_the_sum_of_the_months_matches_what_is_left_to_pay(taxonomy_conn):
    conn = taxonomy_conn
    _two_cards_three_series(conn)

    result = invoice_curve(conn, today=REFERENCE)
    for card in result["cards"]:
        independent = conn.execute(
            "SELECT sum(amount_cents * installments_left) FROM commitments "
            "WHERE kind = 'installment' AND installments_left > 0 AND account = ?",
            (card["name"],),
        ).fetchone()[0]
        assert sum(_totals(card)) == card["remaining_cents"]
        assert card["remaining_cents"] == independent
        assert card["remaining_cents"] != 0

    azul = _card(result, "Cartão Azul")
    roxo = _card(result, "Cartão Roxo")
    assert azul["remaining_cents"] == -46000
    assert roxo["remaining_cents"] == -20000


def test_the_invoice_falls_the_month_after_a_series_dies(taxonomy_conn):
    conn = taxonomy_conn
    _two_cards_three_series(conn)

    result = invoice_curve(conn, today=REFERENCE)
    azul = _card(result, "Cartão Azul")
    series = {row["series_key"]: row for row in azul["series"]}
    assert series["loja azul"]["last_invoice"] == "2026-12"
    assert series["loja azul"]["frees_cents"] == 12000
    assert series["posto azul"]["last_invoice"] == "2026-11"
    assert series["posto azul"]["frees_cents"] == 5000

    months = dict(zip(_months(azul), _totals(azul), strict=True))
    assert months["2026-12"] - months["2026-11"] == series["posto azul"]["frees_cents"]


def test_a_card_without_a_live_instalment_shows_an_empty_series(taxonomy_conn):
    conn = taxonomy_conn
    _two_cards_three_series(conn)
    conn.executescript(
        "INSERT INTO accounts (id, name, type, balance_cents) VALUES "
        "('acc-verde', 'Cartão Verde', 'CREDIT', 0);"
        "INSERT INTO cards (account_id, closing_day) VALUES ('acc-verde', 10);"
    )
    conn.commit()

    result = invoice_curve(conn, today=REFERENCE)
    verde = _card(result, "Cartão Verde")
    assert verde["months"] == []
    assert verde["series"] == []
    assert verde["remaining_cents"] == 0

    azul = _card(result, "Cartão Azul")
    assert len(azul["months"]) == 4


def test_a_repeated_card_name_counts_as_one_card(taxonomy_conn):
    conn = taxonomy_conn
    conn.executescript(
        "INSERT INTO accounts (id, name, type, balance_cents) VALUES "
        "('acc-azul-1', 'Cartão Azul', 'CREDIT', -100000), "
        "('acc-azul-2', 'Cartão Azul', 'CREDIT', -20000);"
        "INSERT INTO cards (account_id, closing_day, due_day) VALUES ('acc-azul-1', 5, 15);"
        "INSERT INTO commitments (kind, series_key, description, account, amount_cents, "
        "last_seen_date, installment_total, installments_left, ends_month) VALUES "
        "('installment', 'loja azul', 'Loja Azul', 'Cartão Azul', -12000, '2026-08-11', "
        "24, 3, '2026-11');"
    )
    conn.commit()

    result = invoice_curve(conn, today=REFERENCE)
    assert [card["name"] for card in result["cards"]] == ["Cartão Azul"]
    card = result["cards"][0]
    assert card["closing_day"] == 5
    assert card["due_day"] == 15
    total_remaining = sum(card["remaining_cents"] for card in result["cards"])
    assert total_remaining == -36000
    assert total_remaining != -72000


def test_the_link_between_series_and_card_is_the_account_name(taxonomy_conn, seed):
    conn = taxonomy_conn
    conn.executescript(
        "INSERT INTO accounts (id, name, type, balance_cents) VALUES "
        "('acc-cartao', 'Cartão Azul', 'CREDIT', -100000);"
        "INSERT INTO cards (account_id, closing_day, due_day) VALUES ('acc-cartao', 5, 15);"
    )
    conn.commit()
    rows = [
        transaction(
            "t-cartao",
            "2026-08-11",
            -120.00,
            conta_id="acc-cartao",
            descricao="Loja Azul",
            parcela_atual=2,
            parcela_total=24,
        ),
        transaction(
            "t-corrente",
            "2026-08-20",
            -50.00,
            descricao="Carne Loja",
            parcela_atual=1,
            parcela_total=6,
        ),
    ]
    load(conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify.classify_all(conn)
    conn.commit()
    recompute(conn, today=REFERENCE)

    result = invoice_curve(conn, today=REFERENCE)
    assert len(result["cards"]) == 1
    card = result["cards"][0]
    assert card["name"] == "Cartão Azul"
    assert card["remaining_cents"] == -264000
    assert result["off_card"] == 1
    assert len(installments(conn, today=REFERENCE)) == 2
