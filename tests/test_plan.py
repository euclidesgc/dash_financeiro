import re
from datetime import date

from app.commitments import engine
from app.debts.ladder import rebuild
from app.plan.objective import RESERVE_MONTHS, reserve_target_cents, survival_floor_cents
from app.plan.timeline import (
    BASE,
    CONSERVATIVE,
    OPTIMISTIC,
    every_scenario,
    expensive_debts,
    history,
    record,
    simulate,
)
from app.taxonomy import classify
from app.taxonomy.seed import load_seed, seed_taxonomy
from tests.conftest import load, transaction

REFERENCE = date(2026, 9, 5)
MONTHS = ("2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08")


def prepare(conn, rows):
    load(conn, rows)
    seed_taxonomy(conn, load_seed())
    classify.classify_all(conn)
    conn.commit()
    engine.recompute(conn, today=REFERENCE)
    rebuild(conn, today=REFERENCE)
    return conn


def salary(value):
    return [
        transaction(f"in-{month}", f"{month}-05", value, descricao="Salario", categoria="Salary")
        for month in MONTHS
    ]


def rent(value):
    return [
        transaction(f"out-{month}", f"{month}-10", value, descricao="Moradia", categoria="Housing")
        for month in MONTHS
    ]


def test_the_reserve_is_six_months_of_the_survival_floor(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-1000.0))
    floor = survival_floor_cents(conn, today=REFERENCE)

    assert floor > 0
    assert reserve_target_cents(conn, today=REFERENCE) == floor * RESERVE_MONTHS


def test_a_month_that_ends_in_the_red_never_reaches_the_objective(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(1000.0) + rent(-3000.0))
    found = simulate(conn, CONSERVATIVE, today=REFERENCE)

    assert found["monthly_result_cents"] < 0
    assert found["months_to_objective"] is None
    assert found["milestones"] == {"resultado": None, "dividas": None, "reserva": None}
    assert found["missing_cents"] == -found["monthly_result_cents"]


def test_a_month_in_the_black_reaches_the_objective_and_says_when(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(9000.0) + rent(-1000.0))
    found = simulate(conn, CONSERVATIVE, today=REFERENCE)

    assert found["monthly_result_cents"] > 0
    assert found["milestones"]["resultado"] == 0
    assert found["months_to_objective"] is not None
    assert found["missing_cents"] == 0


def test_the_mortgage_never_enters_the_expensive_ladder(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-1000.0))
    conn.execute(
        "INSERT INTO debts (kind, name, balance_cents, monthly_rate_bp, source) "
        "VALUES ('mortgage', 'Imovel', -20000000, 200, 'teste'), "
        "('card', 'Cartao', -500000, 900, 'teste')"
    )
    conn.commit()

    kinds = [row["kind"] for row in expensive_debts(conn)]

    assert "card" in kinds
    assert "mortgage" not in kinds


def test_the_three_scenarios_never_get_worse_from_left_to_right(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-1000.0))
    runs = {run["scenario"]: run["monthly_result_cents"] for run in every_scenario(conn, today=REFERENCE)}

    assert runs[CONSERVATIVE] <= runs[BASE] <= runs[OPTIMISTIC]


def test_every_reading_writes_a_point_and_the_same_day_writes_only_one(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-1000.0))
    runs = every_scenario(conn, today=REFERENCE)
    record(conn, runs, today=REFERENCE)
    record(conn, runs, today=REFERENCE)
    record(conn, runs, today=date(2026, 10, 5))

    assert [point["reference_date"] for point in history(conn)] == ["2026-09-05", "2026-10-05"]


def test_a_ladder_already_clear_was_cleared_in_month_zero(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(9000.0) + rent(-1000.0))
    conn.execute("DELETE FROM debts")
    conn.commit()
    found = simulate(conn, CONSERVATIVE, today=REFERENCE)

    assert found["milestones"]["dividas"] == 0


def test_a_month_that_goes_entirely_to_the_debt_does_not_feed_the_reserve(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(9000.0) + rent(-1000.0))
    conn.execute("DELETE FROM debts")
    conn.execute(
        "INSERT INTO debts (kind, name, balance_cents, monthly_rate_bp, source) "
        "VALUES ('card', 'Cartao', ?, 900, 'teste')",
        (-simulate(conn, CONSERVATIVE, today=REFERENCE)["monthly_result_cents"] * 100 // 109,),
    )
    conn.commit()
    found = simulate(conn, CONSERVATIVE, today=REFERENCE)

    assert found["milestones"]["dividas"] == 1
    assert found["milestones"]["reserva"] != 1


def test_the_freed_cash_arrives_when_the_instalment_ends_and_can_create_a_date(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-5100.0))
    conn.execute("DELETE FROM debts")
    conn.execute(
        "INSERT INTO commitments (kind, series_key, description, amount_cents, "
        "last_seen_date, installment_total, installments_left, ends_month, due_day) "
        "VALUES ('installment', 'loja', 'Loja', -50000, '2026-09-01', 6, 2, '2026-12', 10)"
    )
    conn.commit()
    conservative = simulate(conn, CONSERVATIVE, today=REFERENCE)
    optimistic = simulate(conn, OPTIMISTIC, today=REFERENCE)

    assert conservative["monthly_result_cents"] < optimistic["monthly_result_cents"]
    assert conservative["months_to_objective"] is None
    assert optimistic["milestones"]["resultado"] == 3


def test_an_instalment_ending_this_month_is_already_in_the_path(taxonomy_conn):
    conn = prepare(taxonomy_conn, salary(5000.0) + rent(-5000.0))
    conn.execute("DELETE FROM debts")
    conn.execute(
        "INSERT INTO commitments (kind, series_key, description, amount_cents, "
        "last_seen_date, installment_total, installments_left, ends_month, due_day) "
        "VALUES ('installment', 'loja', 'Loja', -50000, '2026-09-01', 6, 1, '2026-09', 10)"
    )
    conn.commit()
    found = simulate(conn, OPTIMISTIC, today=REFERENCE)

    assert found["monthly_result_cents"] == 50000
    assert found["milestones"]["resultado"] == 0
    assert found["months_to_objective"] is not None


def test_a_refused_date_does_not_write_a_point(taxonomy_conn, monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from app.auth.seed import seed_user
    from app.db import connect as open_db
    from app.main import create_app

    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    conn = open_db()
    seed_user(conn, "teste", "senha-teste-9k2")
    conn.close()
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": "teste", "senha": "senha-teste-9k2"})
        refused = client.get("/objetivo?data=0001-01-01")
        client.get("/objetivo?data=2026-09-05")
        client.get("/objetivo?data=2026-10-05")
        seen = client.get("/objetivo?data=2026-09-05")

    assert refused.status_code == 200
    assert 'id="recusa"' in refused.text
    assert "não gravou ponto" in refused.text
    assert re.findall(r'data-ponto="([^"]+)"', seen.text) == ["2026-09-05", "2026-10-05"]


def test_the_screen_names_the_empty_lever_lists(taxonomy_conn, monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from app.auth.seed import seed_user
    from app.db import connect as open_db
    from app.main import create_app

    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    conn = open_db()
    seed_user(conn, "teste", "senha-teste-9k2")
    conn.close()
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": "teste", "senha": "senha-teste-9k2"})
        html = client.get("/objetivo?data=2026-09-05").text

    assert 'id="alavanca-vazia"' in html
    assert "a lista de corte" in html
    assert "mesmo número do" in html


def test_the_screen_without_a_date_records_and_does_not_claim_a_refusal(
    taxonomy_conn, monkeypatch, tmp_path
):
    from fastapi.testclient import TestClient

    from app.auth.seed import seed_user
    from app.db import connect as open_db
    from app.main import create_app

    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    conn = open_db()
    seed_user(conn, "teste", "senha-teste-9k2")
    conn.close()
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": "teste", "senha": "senha-teste-9k2"})
        plain = client.get("/objetivo")
    conn = open_db()
    written = conn.execute("SELECT COUNT(*) FROM plan_snapshots").fetchone()[0]
    conn.close()

    assert plain.status_code == 200
    assert 'id="recusa"' not in plain.text
    assert written > 0


def test_one_empty_lever_does_not_claim_two_nor_claim_the_scenarios_are_equal(
    taxonomy_conn, monkeypatch, tmp_path
):
    from fastapi.testclient import TestClient

    from app.auth.seed import seed_user
    from app.db import connect as open_db
    from app.main import create_app

    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    conn = open_db()
    seed_user(conn, "teste", "senha-teste-9k2")
    conn.execute(
        "INSERT INTO commitments (kind, series_key, description, amount_cents, "
        "last_seen_date, installment_total, dismissed) "
        "VALUES ('recurring', 'x', 'Assinatura X', -246720, '2026-09-01', 0, 1)"
    )
    conn.commit()
    conn.close()
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": "teste", "senha": "senha-teste-9k2"})
        html = client.get("/objetivo?data=2026-09-05").text

    assert "Uma\n      dessas alavancas está" in html or "Uma dessas alavancas está" in html
    assert "Duas dessas alavancas" not in html
    assert "mesmo número do" not in html
