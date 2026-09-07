from datetime import date

from app.commitments import INSTALLMENT, RECURRING
from app.commitments.engine import recompute
from app.commitments.live import live_floor, totals
from app.taxonomy import classify
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, transaction

REFERENCE = date(2026, 9, 5)
STORE = "loja parcelada"


def prepare(conn, seed, rows):
    load(conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify.classify_all(conn)
    conn.commit()
    return conn


def purchase(months, *, total=6, value=-136.43):
    return [
        transaction(
            f"p-{month}",
            f"{month}-08",
            value,
            descricao=f"Loja parcelada {step}/{total}",
            payee=STORE,
        )
        for step, month in enumerate(months, start=1)
    ]


def kinds(conn, series_key):
    return sorted(
        row[0]
        for row in conn.execute(
            "SELECT kind FROM commitments WHERE series_key = ?", (series_key,)
        )
    )


def test_a_purchase_that_just_paid_its_last_instalment_leaves_no_subscription(
    taxonomy_conn, seed
):
    months = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]
    conn = prepare(taxonomy_conn, seed, purchase(months))
    recompute(conn, today=REFERENCE)

    row = conn.execute(
        "SELECT installments_left FROM commitments WHERE kind = ?", (INSTALLMENT,)
    ).fetchone()
    assert row["installments_left"] == 0
    assert kinds(conn, STORE) == [INSTALLMENT]


def test_a_purchase_charged_before_the_window_gives_the_subscription_back(
    taxonomy_conn, seed
):
    months = ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04"]
    conn = prepare(taxonomy_conn, seed, purchase(months))
    recompute(conn, today=REFERENCE)

    assert kinds(conn, STORE) == [INSTALLMENT, RECURRING]


def test_the_live_floor_reaches_one_month_back():
    assert live_floor(date(2026, 9, 5)) == "2026-08-01"


def test_the_live_floor_crosses_the_turn_of_the_year():
    assert live_floor(date(2026, 1, 15)) == "2025-12-01"


def test_a_charge_dated_ahead_is_live(taxonomy_conn, seed):
    months = ["2026-11", "2026-12", "2027-01"]
    rows = [
        transaction(f"f-{month}", f"{month}-08", -80.0, descricao="Assinatura adiante")
        for month in months
    ]
    conn = prepare(taxonomy_conn, seed, rows)
    recompute(conn, today=REFERENCE)

    row = conn.execute("SELECT last_seen_date FROM commitments").fetchone()
    assert row["last_seen_date"] == "2027-01-08"
    assert totals(conn, today=REFERENCE)["committed_cents"] == -8000


def test_a_subscription_that_stopped_leaves_the_total_and_stays_on_the_list(
    taxonomy_conn, seed
):
    stopped = [
        transaction(f"s-{month}", f"{month}-08", -50.0, descricao="Assinatura parada")
        for month in ("2026-01", "2026-02", "2026-03")
    ]
    running = [
        transaction(f"r-{month}", f"{month}-08", -30.0, descricao="Assinatura viva")
        for month in ("2026-07", "2026-08", "2026-09")
    ]
    conn = prepare(taxonomy_conn, seed, stopped + running)
    recompute(conn, today=REFERENCE)

    assert conn.execute("SELECT count(*) FROM commitments").fetchone()[0] == 2
    assert totals(conn, today=REFERENCE)["committed_cents"] == -3000
