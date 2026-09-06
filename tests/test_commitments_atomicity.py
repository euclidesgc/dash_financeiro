from datetime import date

import pytest

from app.commitments import engine, series
from app.commitments.mark import dismiss
from app.taxonomy import classify
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, narrowed, transaction

REFERENCE = date(2026, 9, 5)


def broken(conn):
    raise RuntimeError("detection broke halfway")


def snapshot(conn):
    return [
        tuple(row)
        for row in conn.execute(
            "SELECT kind, series_key, amount_cents, installments_left, ends_month, dismissed "
            "FROM commitments ORDER BY kind, series_key, installment_total, amount_cents"
        )
    ]


@pytest.fixture
def base(taxonomy_conn, seed):
    rows = [
        transaction(f"sub-{month}", f"{month}-11", -581.68, descricao="Assinatura viva")
        for month in ("2026-06", "2026-07", "2026-08")
    ]
    rows.append(
        transaction(
            "live-1", "2026-08-11", -127.27, descricao="Loja parcelada",
            parcela_atual=2, parcela_total=24,
        )
    )
    load(taxonomy_conn, rows)
    seed_taxonomy(taxonomy_conn, narrowed(seed, []))
    classify.classify_all(taxonomy_conn)
    taxonomy_conn.commit()
    engine.recompute(taxonomy_conn, today=REFERENCE)
    dismiss(taxonomy_conn, "assinatura viva")
    taxonomy_conn.commit()
    return taxonomy_conn


def test_a_failed_recompute_leaves_no_row_changed(base, monkeypatch):
    before_count = base.execute("SELECT count(*) FROM commitments").fetchone()[0]
    before_rows = snapshot(base)
    assert before_count > 0
    monkeypatch.setattr(series, "installment_series", broken)
    with pytest.raises(RuntimeError):
        engine.recompute(base, today=REFERENCE)
    assert base.execute("SELECT count(*) FROM commitments").fetchone()[0] == before_count
    assert snapshot(base) == before_rows


def test_a_failure_while_writing_leaves_no_row_changed(base, monkeypatch):
    before_rows = snapshot(base)

    def half_written(recurring, installments, window):
        recurring[0]["kind"] = None
        return recurring

    monkeypatch.setattr(engine, "recurring_after_precedence", half_written)
    with pytest.raises(Exception):
        engine.recompute(base, today=REFERENCE)
    assert snapshot(base) == before_rows
