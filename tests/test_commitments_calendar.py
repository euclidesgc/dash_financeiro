from datetime import date

import pytest

from app.commitments.calendar import WINDOW_DAYS, calendar, window
from app.commitments.engine import recompute
from app.commitments.mark import dismiss
from app.taxonomy import classify
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, transaction

REFERENCE = date(2026, 9, 5)
LAST = date(2026, 10, 20)

LIVE = "Assinatura viva"
LIVE_KEY = "assinatura viva"
LIVE_AMOUNT = -100.0
STOPPED = "Assinatura parada"
STOPPED_KEY = "assinatura parada"
STOPPED_AMOUNT = -50.0
LATE = "Assinatura do fim do mes"
LATE_KEY = "assinatura do fim do mes"
LATE_AMOUNT = -200.0
PURCHASE = "Loja parcelada"
PURCHASE_KEY = "loja parcelada"
PURCHASE_AMOUNT = -120.0
PURCHASE_PAID = 2
PURCHASE_TOTAL = 24

CHARGED = "Assinatura ja lancada"
CHARGED_KEY = "assinatura ja lancada"
CHARGED_AMOUNT = -100.0
RECORDED_AMOUNT = -90.0
RECORDED_DAY = "2026-09-10"
RECORDED_CENTS = -9000


def _prepared(conn, seed, rows):
    load(conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify.classify_all(conn)
    conn.commit()
    recompute(conn, today=REFERENCE)
    return conn


def _monthly(prefix, days, value, description, **extra):
    return [
        transaction(f"{prefix}-{when}", when, value, descricao=description, **extra)
        for when in days
    ]


def _day(days, when):
    found = [entry for entry in days if entry["date"] == when]
    assert found, f"{when} not in {[entry['date'] for entry in days]}"
    return found[0]


def _keys(days):
    return {entry["series_key"] for day in days for entry in day["entries"]}


@pytest.fixture
def base(taxonomy_conn, seed):
    return _prepared(
        taxonomy_conn,
        seed,
        [
            *_monthly("live", ["2026-06-11", "2026-07-11", "2026-08-11"], LIVE_AMOUNT, LIVE),
            *_monthly(
                "old", ["2025-10-11", "2025-11-11", "2025-12-11"], STOPPED_AMOUNT, STOPPED
            ),
            *_monthly("late", ["2026-06-30", "2026-07-31", "2026-08-31"], LATE_AMOUNT, LATE),
            transaction(
                "buy-1",
                "2026-08-11",
                PURCHASE_AMOUNT,
                descricao=PURCHASE,
                parcela_atual=PURCHASE_PAID,
                parcela_total=PURCHASE_TOTAL,
            ),
        ],
    )


@pytest.fixture
def recorded(taxonomy_conn, seed):
    return _prepared(
        taxonomy_conn,
        seed,
        [
            *_monthly(
                "charged",
                ["2026-06-10", "2026-07-10", "2026-08-10"],
                CHARGED_AMOUNT,
                CHARGED,
            ),
            transaction("charged-2026-09", RECORDED_DAY, RECORDED_AMOUNT, descricao=CHARGED),
        ],
    )


def test_the_window_opens_on_the_reference_date_and_closes_forty_five_days_later():
    first, last = window(REFERENCE)

    assert (first, last) == (REFERENCE, LAST)
    assert (last - first).days == WINDOW_DAYS


def test_no_day_of_the_calendar_falls_outside_the_window(base):
    dates = [day["date"] for day in calendar(base, today=REFERENCE)]

    assert dates
    assert dates == sorted(set(dates))
    assert dates[0] >= REFERENCE.isoformat()
    assert dates[-1] <= LAST.isoformat()


def test_the_same_base_read_later_moves_the_window_with_it(base):
    moved = date(2026, 9, 20)
    later = [day["date"] for day in calendar(base, today=moved)]

    assert later
    assert later[0] >= moved.isoformat()
    assert "2026-09-11" in [day["date"] for day in calendar(base, today=REFERENCE)]


def test_every_day_adds_up_the_entries_it_shows(base):
    days = calendar(base, today=REFERENCE)
    shared = _day(days, "2026-09-11")

    assert all(
        day["total_cents"] == sum(entry["amount_cents"] for entry in day["entries"])
        for day in days
    )
    assert {entry["series_key"] for entry in shared["entries"]} == {LIVE_KEY, PURCHASE_KEY}
    assert shared["total_cents"] == int((LIVE_AMOUNT + PURCHASE_AMOUNT) * 100)


def test_an_entry_already_recorded_replaces_the_prediction(recorded):
    day = _day(calendar(recorded, today=REFERENCE), RECORDED_DAY)

    assert len(day["entries"]) == 1
    assert day["entries"][0]["series_key"] == CHARGED_KEY
    assert day["entries"][0]["amount_cents"] == RECORDED_CENTS
    assert day["entries"][0]["predicted"] is False
    assert day["total_cents"] == RECORDED_CENTS


def test_the_month_the_recorded_charge_covers_is_not_predicted_again(recorded):
    days = calendar(recorded, today=REFERENCE)
    september = [day for day in days if day["date"][:7] == "2026-09"]

    october = [entry for day in days if day["date"][:7] == "2026-10" for entry in day["entries"]]

    assert [day["date"] for day in september] == [RECORDED_DAY]
    assert [entry["predicted"] for entry in october] == [True]


def test_a_series_without_a_recent_charge_stays_out_of_the_calendar(base):
    assert STOPPED_KEY not in _keys(calendar(base, today=REFERENCE))


def test_a_dismissed_subscription_leaves_the_calendar(base):
    before = _keys(calendar(base, today=REFERENCE))
    dismiss(base, LIVE_KEY)
    base.commit()

    assert LIVE_KEY in before
    assert LIVE_KEY not in _keys(calendar(base, today=REFERENCE))


def test_a_predicted_day_the_month_does_not_have_falls_on_its_last(base):
    day = _day(calendar(base, today=REFERENCE), "2026-09-30")
    entry = [item for item in day["entries"] if item["series_key"] == LATE_KEY][0]

    assert entry["predicted"] is True
    assert entry["amount_cents"] == int(LATE_AMOUNT * 100)


def test_an_instalment_is_predicted_only_while_it_still_owes(base):
    days = calendar(base, today=REFERENCE)
    owed = [
        day["date"]
        for day in days
        for entry in day["entries"]
        if entry["series_key"] == PURCHASE_KEY
    ]

    assert owed == ["2026-09-11", "2026-10-11"]


def test_a_base_without_a_commitment_answers_with_an_empty_calendar(taxonomy_conn):
    assert calendar(taxonomy_conn, today=REFERENCE) == []
