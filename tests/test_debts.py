from datetime import date

import pytest

from app.debts.ladder import (
    ladder,
    monthly_interest_cents,
    rebuild,
    without_rate,
)
from app.debts.simulate import simulate
from app.financings import store as financings_store
from app.settings.typed import InvalidValueError, parse_money, parse_rate

VEHICLE_BALANCE = 3917636
PAYMENT = 123533
RATE_BP = 163
TERM = 45


def step(**overrides):
    row = {
        "id": 1,
        "name": "CDC do veículo",
        "kind": "vehicle",
        "balance_cents": -VEHICLE_BALANCE,
        "monthly_rate_bp": RATE_BP,
        "term_months": TERM,
        "payment_cents": -PAYMENT,
    }
    row.update(overrides)
    return row


def test_the_present_value_of_the_remaining_instalments_is_the_balance():
    rate = RATE_BP / 10000
    present = PAYMENT * (1 - (1 + rate) ** -TERM) / rate

    assert round(present) == VEHICLE_BALANCE


def test_an_extra_payment_equal_to_the_balance_settles_the_debt():
    found = simulate(step(), VEHICLE_BALANCE)

    assert found["settles"] is True
    assert found["instalments_removed"] == TERM
    assert found["leftover_cents"] == 0


def test_an_extra_payment_larger_than_the_balance_gives_the_excess_back():
    found = simulate(step(), VEHICLE_BALANCE + 50000)

    assert found["leftover_cents"] == 50000
    assert found["instalments_removed"] == TERM
    assert found["instalments_removed"] >= 0


def test_a_debt_with_no_term_answers_in_interest_and_not_in_instalments():
    found = simulate(step(term_months=None, payment_cents=None, monthly_rate_bp=352), 100000)

    assert found["instalments_removed"] == 0
    assert found["interest_saved_cents"] == round(100000 * 352 / 10000)


def test_an_extra_payment_of_zero_is_refused():
    with pytest.raises(InvalidValueError):
        simulate(step(), 0)


def test_the_instalments_removed_come_off_the_end_of_the_schedule():
    found = simulate(step(), 1000000)

    assert 0 < found["instalments_removed"] < TERM
    assert found["interest_saved_cents"] > 0


def test_a_rate_outside_the_range_is_refused_by_name():
    with pytest.raises(InvalidValueError) as refusal:
        parse_rate("-1")

    assert "-1" in str(refusal.value)


def test_an_empty_rate_clears_the_step():
    assert parse_rate("") is None
    assert parse_rate("  ") is None


def test_a_rate_is_read_with_a_comma_and_a_percent_sign():
    assert parse_rate("3,52%") == 352


def test_an_amount_is_read_in_the_brazilian_form():
    assert parse_money("10.000,00") == 1000000


def test_the_monthly_interest_of_a_step_without_a_rate_is_zero():
    assert monthly_interest_cents(step(monthly_rate_bp=None)) == 0


def test_a_missing_contract_folder_leaves_the_load_without_those_steps(
    taxonomy_conn, tmp_path, monkeypatch
):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "vazio"))
    taxonomy_conn.execute(
        "INSERT INTO accounts (id, name, type, subtype, institution, balance_cents, updated_at) "
        "VALUES ('a', 'Conta', 'BANK', 'CHECKING_ACCOUNT', 'X', -1000, '2026-09-05')"
    )
    taxonomy_conn.commit()

    assert rebuild(taxonomy_conn, today=date(2026, 9, 5)) == 1
    assert ladder(taxonomy_conn) == []
    assert len(without_rate(taxonomy_conn)) == 1


def test_a_rate_typed_by_the_owner_survives_the_reload(taxonomy_conn, tmp_path, monkeypatch):
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(tmp_path / "vazio"))
    taxonomy_conn.execute(
        "INSERT INTO accounts (id, name, type, subtype, institution, balance_cents, updated_at) "
        "VALUES ('a', 'Conta', 'BANK', 'CHECKING_ACCOUNT', 'X', -1000, '2026-09-05')"
    )
    taxonomy_conn.commit()
    rebuild(taxonomy_conn, today=date(2026, 9, 5))
    taxonomy_conn.execute("UPDATE debts SET monthly_rate_bp = 352")
    taxonomy_conn.commit()

    rebuild(taxonomy_conn, today=date(2026, 9, 5))

    assert ladder(taxonomy_conn)[0]["monthly_rate_bp"] == 352


def test_the_vehicle_step_is_built_by_the_loader_and_not_by_the_test(
    taxonomy_conn, tmp_path, monkeypatch
):
    import json

    folder = tmp_path / "manual"
    folder.mkdir()
    (folder / financings_store.VEHICLE_FILE).write_text(
        json.dumps(
            {
                "prazo_meses": 60,
                "juros_efetivo_mensal_pct": 1.63,
                "valor_parcela": 1235.33,
                "primeiro_vencimento": "2025-06-11",
            }
        )
    )
    monkeypatch.setenv(financings_store.MANUAL_DIR, str(folder))
    rebuild(taxonomy_conn, today=date(2026, 9, 5))
    row = ladder(taxonomy_conn)[0]

    assert row["kind"] == "vehicle"
    assert row["term_months"] == TERM
    assert row["balance_cents"] == -VEHICLE_BALANCE
    assert row["monthly_rate_bp"] == RATE_BP
    assert row["payment_cents"] == -PAYMENT


def test_a_rate_written_to_a_step_that_does_not_exist_is_refused(taxonomy_conn):
    from app.debts.ladder import DebtNotFoundError, set_rate

    with pytest.raises(DebtNotFoundError):
        set_rate(taxonomy_conn, 999, "3,52")


def test_a_debt_without_a_rate_refuses_to_be_simulated():
    from app.debts.simulate import UnknownRateError

    with pytest.raises(UnknownRateError) as refusal:
        simulate(step(monthly_rate_bp=None, term_months=None, payment_cents=None), 500000)

    assert "Informe a taxa primeiro." in str(refusal.value)


def test_a_refusal_names_the_field_the_owner_touched():
    with pytest.raises(InvalidValueError) as refusal:
        parse_money("abc", "Saldo de quitação")

    assert "Saldo de quitação inválido" in str(refusal.value)
    assert "'" not in str(refusal.value)
