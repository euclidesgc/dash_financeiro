import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from app.debts.ladder import ladder, rebuild, without_rate
from app.financings import store as financings_store
from app.financings.math import present_value_cents

MORTGAGE_JSON = {
    "prazo_restante_meses": 370,
    "saldo_devedor": 238585.18,
    "juros_efetivos_aa_pct": 8.9899,
}
VEHICLE_JSON = {
    "prazo_meses": 60,
    "juros_efetivo_mensal_pct": 1.63,
    "valor_parcela": 1235.33,
    "primeiro_vencimento": "2025-06-11",
}

FIELDS = ("kind", "name", "balance_cents", "monthly_rate_bp", "term_months", "payment_cents")


def _write_manual(tmp_path: Path) -> Path:
    folder = tmp_path / "manual"
    folder.mkdir()
    (folder / financings_store.MORTGAGE_FILE).write_text(json.dumps(MORTGAGE_JSON))
    (folder / financings_store.VEHICLE_FILE).write_text(json.dumps(VEHICLE_JSON))
    return folder


def _reference_paid(data: dict, today: date) -> int:
    # The oracle this item replaces: the exact arithmetic that used to live in
    # app/debts/ladder.py, kept here so the table-backed ladder is proved
    # against the file-backed one it supersedes, not against itself.
    first = date.fromisoformat(data["primeiro_vencimento"])
    year, month, paid = first.year, first.month, 0
    for _ in range(data["prazo_meses"]):
        if date(year, month, first.day) <= today:
            paid += 1
        month += 1
        if month > 12:
            month, year = 1, year + 1
    return paid


def _reference_mortgage(data: dict) -> dict:
    yearly = data["juros_efetivos_aa_pct"] / 100
    monthly = (1 + yearly) ** (1 / 12) - 1
    return {
        "kind": "mortgage",
        "name": "Financiamento imobiliário",
        "balance_cents": -round(data["saldo_devedor"] * 100),
        "monthly_rate_bp": round(monthly * 10000),
        "term_months": data["prazo_restante_meses"],
        "payment_cents": None,
    }


def _reference_vehicle(data: dict, today: date) -> dict:
    rate = data["juros_efetivo_mensal_pct"] / 100
    payment = data["valor_parcela"]
    left = data["prazo_meses"] - _reference_paid(data, today)
    return {
        "kind": "vehicle",
        "name": "CDC do veículo",
        "balance_cents": -round(payment * (1 - (1 + rate) ** -left) / rate * 100),
        "monthly_rate_bp": round(rate * 10000),
        "term_months": left,
        "payment_cents": -round(payment * 100),
    }


def test_the_table_ladder_matches_the_file_ladder_and_the_import_does_not_repeat(
    taxonomy_conn, tmp_path, monkeypatch
):
    folder = _write_manual(tmp_path)
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(folder))
    today = date(2026, 9, 5)

    assert rebuild(taxonomy_conn, today=today) == 2
    assert rebuild(taxonomy_conn, today=today) == 2

    found = ladder(taxonomy_conn)
    expected = [_reference_vehicle(VEHICLE_JSON, today), _reference_mortgage(MORTGAGE_JSON)]

    assert len(found) == 2
    for row, reference in zip(found, expected, strict=True):
        assert {field: row[field] for field in FIELDS} == reference

    assert found[0]["kind"] == "vehicle"
    assert found[0]["balance_cents"] == -3917636
    assert found[0]["monthly_rate_bp"] == 163
    assert found[0]["term_months"] == 45
    assert found[0]["payment_cents"] == -123533
    assert found[1]["kind"] == "mortgage"
    assert found[1]["balance_cents"] == -23858518
    assert found[1]["monthly_rate_bp"] == 72
    assert found[1]["term_months"] == 370
    assert found[1]["payment_cents"] is None

    count = taxonomy_conn.execute("SELECT COUNT(*) FROM financings").fetchone()[0]
    assert count == 2


def test_a_row_already_in_the_table_wins_over_the_files_on_disk(
    taxonomy_conn, tmp_path, monkeypatch
):
    folder = _write_manual(tmp_path)
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(folder))
    taxonomy_conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES ('mortgage', 1000, 12, -10000000, NULL, NULL)"
    )
    taxonomy_conn.commit()

    assert rebuild(taxonomy_conn, today=date(2026, 9, 5)) == 1

    found = ladder(taxonomy_conn)
    assert len(found) == 1
    assert found[0]["kind"] == "mortgage"
    assert found[0]["monthly_rate_bp"] == 1000
    assert found[0]["term_months"] == 12
    assert found[0]["balance_cents"] == -10000000

    count = taxonomy_conn.execute("SELECT COUNT(*) FROM financings").fetchone()[0]
    assert count == 1


def test_a_machine_without_file_or_row_still_answers(taxonomy_conn, tmp_path, monkeypatch):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "nao-existe"))
    taxonomy_conn.execute(
        "INSERT INTO accounts (id, name, type, subtype, institution, balance_cents, updated_at) "
        "VALUES ('a', 'Conta', 'BANK', 'CHECKING_ACCOUNT', 'X', -1000, '2026-09-05')"
    )
    taxonomy_conn.commit()

    assert rebuild(taxonomy_conn, today=date(2026, 9, 5)) == 1
    assert ladder(taxonomy_conn) == []
    assert len(without_rate(taxonomy_conn)) == 1

    count = taxonomy_conn.execute("SELECT COUNT(*) FROM financings").fetchone()[0]
    assert count == 0


def test_a_rate_edited_in_the_table_reaches_the_ladder_and_a_typed_account_rate_survives(
    taxonomy_conn, tmp_path, monkeypatch
):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "nao-existe"))
    taxonomy_conn.execute(
        "INSERT INTO accounts (id, name, type, subtype, institution, balance_cents, updated_at) "
        "VALUES ('a', 'Conta', 'BANK', 'CHECKING_ACCOUNT', 'X', -1000, '2026-09-05')"
    )
    taxonomy_conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES ('mortgage', 72, 370, -23858518, NULL, NULL)"
    )
    taxonomy_conn.commit()
    rebuild(taxonomy_conn, today=date(2026, 9, 5))

    taxonomy_conn.execute("UPDATE debts SET monthly_rate_bp = 352 WHERE kind = 'overdraft'")
    taxonomy_conn.execute("UPDATE financings SET monthly_rate_bp = 500 WHERE kind = 'mortgage'")
    taxonomy_conn.commit()

    rebuild(taxonomy_conn, today=date(2026, 9, 5))

    mortgage_rate = taxonomy_conn.execute(
        "SELECT monthly_rate_bp FROM debts WHERE kind = 'mortgage'"
    ).fetchone()[0]
    overdraft_rate = taxonomy_conn.execute(
        "SELECT monthly_rate_bp FROM debts WHERE kind = 'overdraft'"
    ).fetchone()[0]

    assert mortgage_rate == 500
    assert overdraft_rate == 352


def test_a_due_date_on_the_31st_crosses_february_without_raising(
    taxonomy_conn, tmp_path, monkeypatch
):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "nao-existe"))
    taxonomy_conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES ('vehicle', 163, 12, NULL, -100000, '2026-01-31')"
    )
    taxonomy_conn.commit()

    assert rebuild(taxonomy_conn, today=date(2026, 9, 5)) == 1

    row = ladder(taxonomy_conn)[0]
    assert row["term_months"] == 4
    assert row["balance_cents"] < 0


def test_the_vehicle_balance_shrinks_by_itself_between_two_rebuilds(
    taxonomy_conn, tmp_path, monkeypatch
):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "nao-existe"))
    taxonomy_conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES ('vehicle', 163, 60, NULL, -123533, '2025-06-11')"
    )
    taxonomy_conn.commit()

    rebuild(taxonomy_conn, today=date(2026, 9, 5))
    first = ladder(taxonomy_conn)[0]
    assert first["term_months"] == 45
    assert first["balance_cents"] == -3917636

    rebuild(taxonomy_conn, today=date(2026, 10, 5))
    second = ladder(taxonomy_conn)[0]
    assert second["term_months"] == 44
    assert -3917636 < second["balance_cents"] < 0


def test_a_contract_with_every_instalment_due_leaves_no_step(taxonomy_conn, tmp_path, monkeypatch):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "nao-existe"))
    taxonomy_conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES ('vehicle', 163, 12, NULL, -123533, '2020-01-10')"
    )
    taxonomy_conn.commit()

    assert rebuild(taxonomy_conn, today=date(2026, 9, 5)) == 0
    assert ladder(taxonomy_conn) == []

    count = taxonomy_conn.execute("SELECT COUNT(*) FROM financings").fetchone()[0]
    assert count == 1


def test_present_value_with_zero_rate_sums_the_remaining_instalments():
    # A vehicle contract with no interest has no annuity factor to divide by:
    # the present value of what is left is just the sum of the instalments.
    assert present_value_cents(-123533, 0, 45) == -123533 * 45


def test_a_zero_rate_vehicle_rebuilds_without_dividing_by_the_rate(
    taxonomy_conn, tmp_path, monkeypatch
):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "nao-existe"))
    taxonomy_conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES ('vehicle', 0, 60, NULL, -123533, '2025-06-11')"
    )
    taxonomy_conn.commit()

    assert rebuild(taxonomy_conn, today=date(2026, 9, 5)) == 1

    row = ladder(taxonomy_conn)[0]
    assert row["term_months"] == 45
    assert row["balance_cents"] == -123533 * 45


def test_a_vehicle_row_missing_the_payment_is_refused_by_the_schema(taxonomy_conn):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        taxonomy_conn.execute(
            "INSERT INTO financings "
            "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
            "VALUES ('vehicle', 163, 60, NULL, NULL, '2025-06-11')"
        )


def test_a_vehicle_row_missing_the_due_date_is_refused_by_the_schema(taxonomy_conn):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        taxonomy_conn.execute(
            "INSERT INTO financings "
            "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
            "VALUES ('vehicle', 163, 60, NULL, -123533, NULL)"
        )


def _debt_id(conn: sqlite3.Connection, kind: str) -> int:
    return conn.execute("SELECT id FROM debts WHERE kind = ?", (kind,)).fetchone()[0]


def test_writing_a_financing_keeps_the_debt_ids_stable(taxonomy_conn):
    # INSERT OR REPLACE deletes and reinserts the conflicting row, moving it to
    # the end of the table; ladder ids are assigned by insertion order, so a
    # screen open before a write would keep pointing at the wrong debt id.
    taxonomy_conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES ('mortgage', 72, 370, -23858518, NULL, NULL)"
    )
    taxonomy_conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES ('vehicle', 163, 60, NULL, -123533, '2025-06-11')"
    )
    taxonomy_conn.commit()
    rebuild(taxonomy_conn, today=date(2026, 9, 5))

    mortgage_id_before = _debt_id(taxonomy_conn, "mortgage")
    vehicle_id_before = _debt_id(taxonomy_conn, "vehicle")

    financings_store.write(
        taxonomy_conn, "mortgage", {"saldo": "200.000,00", "taxa": "5,00", "prazo": "300"}
    )
    rebuild(taxonomy_conn, today=date(2026, 9, 5))

    assert _debt_id(taxonomy_conn, "mortgage") == mortgage_id_before
    assert _debt_id(taxonomy_conn, "vehicle") == vehicle_id_before


def test_writing_a_financing_keeps_the_table_row_order(taxonomy_conn):
    # read_all selects every column, so a full table scan reads rowid order,
    # not the kind index order: this is the query rebuild actually runs.
    taxonomy_conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES ('mortgage', 72, 370, -23858518, NULL, NULL)"
    )
    taxonomy_conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES ('vehicle', 163, 60, NULL, -123533, '2025-06-11')"
    )
    taxonomy_conn.commit()

    before = [row["kind"] for row in financings_store.read_all(taxonomy_conn)]
    assert before == ["mortgage", "vehicle"]

    financings_store.write(
        taxonomy_conn, "mortgage", {"saldo": "200.000,00", "taxa": "5,00", "prazo": "300"}
    )

    after = [row["kind"] for row in financings_store.read_all(taxonomy_conn)]
    assert after == before
