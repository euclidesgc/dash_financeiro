import os
from datetime import date

import pytest

from app.commitments import INSTALLMENT, RECURRING
from app.commitments.engine import main as recompute_command
from app.commitments.engine import recompute
from app.commitments.live import installments, released_cash, subscriptions, totals
from app.commitments.mark import DismissRefusedError, dismiss, resume
from app.config import reference_date
from app.taxonomy import classify
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, transaction

REFERENCE = date(2026, 9, 5)


def monthly(prefix, months, value, description, **extra):
    return [
        transaction(f"{prefix}-{month}", f"{month}-11", value, descricao=description, **extra)
        for month in months
    ]


def rows_of(conn):
    return [
        tuple(row)
        for row in conn.execute(
            "SELECT kind, series_key, amount_cents, installments_left, ends_month, dismissed "
            "FROM commitments ORDER BY kind, series_key, installment_total, amount_cents"
        )
    ]


def kinds_of(conn, series_key):
    return sorted(
        row[0]
        for row in conn.execute("SELECT kind FROM commitments WHERE series_key = ?", (series_key,))
    )


@pytest.fixture
def base(taxonomy_conn, seed):
    rows = [
        *monthly("sub", ["2026-06", "2026-07", "2026-08"], -581.68, "Assinatura viva"),
        *monthly("old", ["2025-10", "2025-11", "2025-12"], -109.00, "Assinatura parada"),
        transaction(
            "live-1",
            "2026-08-11",
            -127.27,
            descricao="Loja parcelada",
            parcela_atual=2,
            parcela_total=24,
        ),
        transaction(
            "dead-1",
            "2026-01-26",
            -797.13,
            descricao="IPVA parcela 1 de 3 Detran",
        ),
    ]
    load(taxonomy_conn, rows)
    seed_taxonomy(taxonomy_conn, narrowed(seed, []))
    classify.classify_all(taxonomy_conn)
    taxonomy_conn.commit()
    recompute(taxonomy_conn, today=REFERENCE)
    return taxonomy_conn


def test_the_detection_writes_both_kinds(base):
    assert len(subscriptions(base, today=REFERENCE)) == 2
    assert [row["series_key"] for row in installments(base, today=REFERENCE)] == ["loja parcelada"]


def test_a_second_recompute_changes_no_row(base):
    before = rows_of(base)
    recompute(base, today=REFERENCE)
    recompute(base, today=REFERENCE)
    assert rows_of(base) == before
    assert len(before) == base.execute("SELECT count(*) FROM commitments").fetchone()[0]


def test_the_mark_survives_the_recompute(base):
    dismiss(base, "assinatura viva")
    base.commit()
    recompute(base, today=REFERENCE)
    marked = base.execute("SELECT series_key FROM commitments WHERE dismissed = 1").fetchall()
    assert [row[0] for row in marked] == ["assinatura viva"]


def test_resuming_puts_the_series_back_in_the_total(base):
    before = totals(base, today=REFERENCE)["committed_cents"]
    dismiss(base, "assinatura viva")
    base.commit()
    after = totals(base, today=REFERENCE)
    assert after["committed_cents"] == before + 58168
    assert after["projected_savings_cents"] == 58168
    resume(base, "assinatura viva")
    base.commit()
    assert totals(base, today=REFERENCE)["committed_cents"] == before
    assert base.execute("SELECT count(*) FROM commitment_dismissals").fetchone()[0] == 0


def test_an_installment_line_refuses_the_mark(base):
    with pytest.raises(DismissRefusedError):
        dismiss(base, "loja parcelada")
    assert base.execute("SELECT count(*) FROM commitment_dismissals").fetchone()[0] == 0


def test_a_series_that_stopped_stays_listed_and_marked_as_stale(base):
    listed = {row["series_key"]: row["live"] for row in subscriptions(base, today=REFERENCE)}
    assert listed == {"assinatura viva": True, "assinatura parada": False}


def test_a_dead_installment_series_is_stored_and_left_out_of_the_live_list(base):
    stored = base.execute(
        "SELECT installments_left FROM commitments WHERE series_key = ?",
        ("ipva parcela detran",),
    ).fetchone()
    assert stored[0] == 2
    assert "ipva parcela detran" not in {
        row["series_key"] for row in installments(base, today=REFERENCE)
    }


def test_a_key_that_is_recurring_and_live_installment_counts_once(taxonomy_conn, seed):
    rows = monthly(
        "both",
        ["2026-06", "2026-07", "2026-08"],
        -100.00,
        "Loja dupla",
        parcela_atual=None,
        parcela_total=None,
    )
    rows[-1]["parcela_atual"] = 2
    rows[-1]["parcela_total"] = 24
    load(taxonomy_conn, rows)
    seed_taxonomy(taxonomy_conn, narrowed(seed, []))
    classify.classify_all(taxonomy_conn)
    taxonomy_conn.commit()
    recompute(taxonomy_conn, today=REFERENCE)
    kinds = kinds_of(taxonomy_conn, "loja dupla")
    assert kinds == [INSTALLMENT]
    assert RECURRING not in kinds


def test_the_released_cash_lands_on_the_month_the_series_ends(base):
    assert released_cash(base, today=REFERENCE) == [{"month": "2028-06", "amount_cents": 12727}]


def test_the_window_moves_with_the_reference_date(base):
    assert installments(base, today=date(2026, 11, 5)) == []
    assert [row["live"] for row in subscriptions(base, today=date(2026, 11, 5))] == [False, False]


def test_the_command_carries_the_environment_date_into_the_recompute(
    taxonomy_conn, seed, tmp_path, monkeypatch
):
    rows = monthly(
        "both",
        ["2026-06", "2026-07", "2026-08"],
        -100.00,
        "Loja dupla",
        parcela_atual=None,
        parcela_total=None,
    )
    rows[-1]["parcela_atual"] = 2
    rows[-1]["parcela_total"] = 24
    load(taxonomy_conn, rows)
    seed_taxonomy(taxonomy_conn, narrowed(seed, []))
    classify.classify_all(taxonomy_conn)
    taxonomy_conn.commit()
    monkeypatch.setenv("DASH_ENV_FILE", os.devnull)
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))

    monkeypatch.setenv("DASH_TODAY", "2027-03-01")
    assert recompute_command() == 0
    assert installments(taxonomy_conn, today=reference_date()) == []
    assert kinds_of(taxonomy_conn, "loja dupla") == sorted([INSTALLMENT, RECURRING])

    monkeypatch.setenv("DASH_TODAY", REFERENCE.isoformat())
    assert recompute_command() == 0
    assert len(installments(taxonomy_conn, today=reference_date())) == 1
    assert kinds_of(taxonomy_conn, "loja dupla") == [INSTALLMENT]
