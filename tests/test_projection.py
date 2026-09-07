from datetime import date

from app.commitments.engine import recompute
from app.commitments.live import totals as committed_totals
from app.projection.forecast import forecast
from app.projection.monthly import median, monthly
from app.projection.position import positions
from app.taxonomy import classify
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import ACCOUNT, load, narrowed, transaction

REFERENCE = date(2026, 9, 5)
DAYS = 46


def prepare(conn, seed, rows):
    load(conn, rows)
    seed_taxonomy(conn, narrowed(seed, []))
    classify.classify_all(conn)
    conn.commit()
    return conn


def balance(conn, cents):
    conn.execute("UPDATE accounts SET balance_cents = ?", (cents,))
    conn.commit()
    return conn


def test_the_consolidated_position_is_the_sum_of_the_two(taxonomy_conn, seed):
    conn = balance(prepare(taxonomy_conn, seed, []), -50000)
    found = positions(conn)

    assert found["cash_cents"] == -50000
    assert found["card_cents"] == 0
    assert found["consolidated_cents"] == -50000


def test_the_median_of_an_even_count_is_the_average_of_the_two_middle():
    assert median([-400, -100, -300, -200]) == -250


def test_the_median_ignores_one_atypical_month():
    assert median([1000, 1100, 1200, 1300, 90000]) == 1200


def test_a_base_with_no_movement_projects_a_flat_line(taxonomy_conn, seed):
    conn = balance(prepare(taxonomy_conn, seed, []), -12345)
    found = forecast(conn, today=REFERENCE)

    assert len(found["days"]) == DAYS
    assert {day["balance_cents"] for day in found["days"]} == {-12345}
    assert found["delta_cents"] == 0
    assert found["worst"]["balance_cents"] == -12345


def test_every_day_of_the_line_is_the_day_before_plus_its_three_parts(
    taxonomy_conn, seed
):
    rows = [
        transaction(f"in-{month}", f"{month}-14", 5000.0, descricao="Salario")
        for month in ("2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08")
    ]
    rows += [
        transaction(f"out-{month}", f"{month}-20", -300.0, descricao="Assinatura X")
        for month in ("2026-06", "2026-07", "2026-08", "2026-09")
    ]
    conn = balance(prepare(taxonomy_conn, seed, rows), -100000)
    found = forecast(conn, today=REFERENCE)

    for earlier, later in zip(found["days"], found["days"][1:]):
        parts = later["income_cents"] + later["due_cents"] + later["variable_cents"]
        assert later["balance_cents"] == earlier["balance_cents"] + parts
    assert found["days"][0]["balance_cents"] == -100000


def test_the_variable_share_is_what_the_dated_commitment_does_not_cover(
    taxonomy_conn, seed
):
    rows = [
        transaction(f"out-{month}", f"{month}-20", -300.0, descricao="Assinatura X")
        for month in ("2026-06", "2026-07", "2026-08", "2026-09")
    ]
    conn = balance(prepare(taxonomy_conn, seed, rows), 0)
    recompute(conn, today=REFERENCE)
    found = forecast(conn, today=REFERENCE)
    month = monthly(conn, today=REFERENCE)
    committed = committed_totals(conn, today=REFERENCE)["committed_cents"]

    assert committed == -30000
    assert found["variable_cents"] == month["spending_cents"] - committed
    assert found["income_day"] is None


def test_the_worst_point_is_not_the_last_day_when_the_income_comes_after_it(
    taxonomy_conn, seed
):
    rows = [
        transaction(f"in-{month}", f"{month}-28", 900.0, descricao="Salario")
        for month in ("2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08")
    ]
    conn = balance(prepare(taxonomy_conn, seed, rows), 0)
    found = forecast(conn, today=REFERENCE)

    assert found["worst"]["date"] < found["days"][-1]["date"]
    assert found["worst"]["balance_cents"] <= found["days"][-1]["balance_cents"]


def test_the_months_used_are_the_six_complete_ones_before_the_reference(
    taxonomy_conn, seed
):
    rows = [
        transaction(f"x-{month}", f"{month}-10", -10.0, descricao="Compra")
        for month in (
            "2026-01", "2026-02", "2026-03", "2026-04",
            "2026-05", "2026-06", "2026-07", "2026-08", "2026-09",
        )
    ]
    conn = prepare(taxonomy_conn, seed, rows)

    assert monthly(conn, today=REFERENCE)["months"] == [
        "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08",
    ]
