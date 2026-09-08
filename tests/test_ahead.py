from app.queries.ahead import Ahead, posted_ahead
from tests.conftest import load, transaction

AFTER = "2026-09-05"
UNTIL = "2026-09-30"


def test_ahead_is_a_frozen_pair_of_entries_and_amount():
    ahead = Ahead(2, -7000)
    assert (ahead.entries, ahead.amount_cents) == (2, -7000)


def test_the_lower_bound_is_strict_and_the_upper_bound_is_inclusive(taxonomy_conn):
    conn = load(
        taxonomy_conn,
        [
            transaction("t-before", "2026-09-04", -10.00),
            transaction("t-at-after", AFTER, -20.00),
            transaction("t-inside-first", "2026-09-06", -30.00),
            transaction("t-inside-last", UNTIL, -40.00),
            transaction("t-after-until", "2026-10-01", -50.00),
        ],
    )

    result = posted_ahead(conn, after=AFTER, until=UNTIL)

    assert (result.entries, result.amount_cents) == (2, -7000)


def test_a_transfer_between_own_accounts_and_a_refund_stay_out(taxonomy_conn):
    conn = load(
        taxonomy_conn,
        [
            transaction("t-inside", "2026-09-10", -30.00),
            transaction("t-transfer", "2026-09-11", -60.00, eh_transferencia=True),
            transaction("t-refund-debit", "2026-09-12", -70.00, estornada_por="t-refund"),
            transaction("t-refund", "2026-09-12", 70.00, eh_estorno=True),
        ],
    )

    result = posted_ahead(conn, after=AFTER, until=UNTIL)

    assert (result.entries, result.amount_cents) == (1, -3000)


def test_an_empty_interval_returns_a_zeroed_ahead(taxonomy_conn):
    conn = load(taxonomy_conn, [transaction("t-outside", "2026-09-10", -30.00)])

    result = posted_ahead(conn, after="2020-01-01", until="2020-01-31")

    assert result == Ahead(0, 0)
