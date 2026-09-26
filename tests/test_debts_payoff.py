from datetime import date

import pytest

from app.debts.payoff import (
    BALANCE,
    CARD_INSTALLMENT,
    INFORMED,
    NOMINAL,
    Debt,
    InvalidSavingError,
    PastTargetError,
    list_debts,
    payoff_at,
    saving_plan,
    unnumbered,
)
from app.settings import store as settings_store
from app.settings.catalog import SETTLEMENT

TODAY = date(2026, 9, 26)
PAYMENT = -123533


def vehicle(*, settlement=None, valid_until=None):
    return Debt(
        key="debt-7",
        kind="vehicle",
        name="CDC do veículo",
        account=None,
        balance_cents=None,
        payment_cents=PAYMENT,
        first_due=date(2025, 6, 11),
        installment_total=60,
        settlement_cents=settlement,
        settlement_valid_until=valid_until,
    )


def revolving(kind="overdraft", balance=-250000):
    return Debt(
        key="debt-1",
        kind=kind,
        name="Conta",
        account=None,
        balance_cents=balance,
        payment_cents=None,
        first_due=None,
        installment_total=None,
        settlement_cents=None,
        settlement_valid_until=None,
    )


def purchase(first_due=date(2026, 7, 11), total=5, payment=-10000):
    return Debt(
        key="installment-3",
        kind=CARD_INSTALLMENT,
        name="LOJA",
        account="Cartão",
        balance_cents=None,
        payment_cents=payment,
        first_due=first_due,
        installment_total=total,
        settlement_cents=None,
        settlement_valid_until=None,
    )


def test_known_settlement_is_the_payoff_today():
    payoff = payoff_at(vehicle(settlement=3800000), TODAY, today=TODAY)

    assert payoff.basis == INFORMED
    assert payoff.payoff_cents == 3800000
    assert payoff.target_cents == 3800000
    assert payoff.nominal_cents == 44 * 123533
    assert payoff.installments_left == 44
    assert payoff.end_month == "2030-05"
    assert not payoff.missing_settlement


def test_unknown_settlement_gives_the_nominal_ceiling_and_asks_for_it():
    payoff = payoff_at(vehicle(), TODAY, today=TODAY)

    assert payoff.basis == NOMINAL
    assert payoff.payoff_cents is None
    assert payoff.target_cents == 44 * 123533
    assert payoff.missing_settlement


def test_stale_or_future_settlement_is_not_reused():
    stale = payoff_at(vehicle(settlement=3800000, valid_until="2026-09-01"), TODAY, today=TODAY)
    ahead = payoff_at(vehicle(settlement=3800000), date(2027, 3, 26), today=TODAY)

    assert stale.payoff_cents is None and stale.missing_settlement
    assert ahead.basis == NOMINAL
    assert ahead.installments_left == 38
    assert ahead.target_cents == 38 * 123533


def test_revolving_balance_is_the_payoff_on_any_date():
    today = payoff_at(revolving(), TODAY, today=TODAY)
    later = payoff_at(revolving("card", -99999), date(2027, 1, 1), today=TODAY)

    assert today.basis == BALANCE and today.payoff_cents == 250000
    assert later.target_cents == 99999 and later.nominal_cents is None


def test_instalment_purchase_settles_at_the_nominal_remainder():
    payoff = payoff_at(purchase(), TODAY, today=TODAY)

    assert payoff.basis == NOMINAL
    assert payoff.payoff_cents == 20000
    assert payoff.installments_left == 2
    assert payoff.end_month == "2026-11"
    assert not payoff.missing_settlement


def test_target_date_in_the_past_is_refused():
    with pytest.raises(PastTargetError):
        saving_plan(vehicle(), today=TODAY, target_date=date(2026, 9, 25))


def test_target_date_this_month_needs_the_whole_amount_now():
    plan = saving_plan(vehicle(settlement=3800000), today=TODAY, target_date=date(2026, 9, 30))

    assert plan.months == 0
    assert plan.monthly_cents == 3800000
    assert plan.reached_month == "2026-09"


def test_near_target_splits_the_amount_left_then_rounding_up():
    plan = saving_plan(revolving(balance=-100000), today=TODAY, target_date=date(2026, 12, 26))

    assert plan.months == 3
    assert plan.monthly_cents == 33334
    assert plan.monthly_cents * plan.months >= 100000


def test_target_counts_the_instalments_paid_until_then():
    plan = saving_plan(vehicle(), today=TODAY, target_date=date(2027, 9, 26))

    assert plan.months == 12
    assert plan.payoff.installments_left == 32
    assert plan.payoff.target_cents == 32 * 123533
    assert plan.monthly_cents == -(-(32 * 123533) // 12)


def test_far_target_after_the_last_instalment_needs_nothing():
    plan = saving_plan(purchase(), today=TODAY, target_date=date(2027, 6, 1))

    assert plan.payoff.target_cents == 0
    assert plan.monthly_cents == 0


def test_monthly_saving_finds_the_first_month_it_covers_the_payoff():
    plan = saving_plan(vehicle(), today=TODAY, monthly_saving_cents=150000)

    assert plan.reached_month == "2028-05"
    assert plan.months == 20
    assert plan.payoff.installments_left == 24
    assert 150000 * 20 >= plan.payoff.target_cents
    assert 150000 * 19 < payoff_at(vehicle(), date(2028, 4, 30), today=TODAY).target_cents


def test_zero_or_negative_saving_is_refused():
    with pytest.raises(InvalidSavingError):
        saving_plan(vehicle(), today=TODAY, monthly_saving_cents=0)
    with pytest.raises(InvalidSavingError):
        saving_plan(vehicle(), today=TODAY, monthly_saving_cents=-100)


def test_a_saving_too_small_never_reaches_a_balance():
    plan = saving_plan(revolving(balance=-10**12), today=TODAY, monthly_saving_cents=1)

    assert plan.reached_month is None
    assert plan.months is None


def test_saving_plan_needs_exactly_one_goal():
    with pytest.raises(ValueError):
        saving_plan(vehicle(), today=TODAY)
    with pytest.raises(ValueError):
        saving_plan(vehicle(), today=TODAY, target_date=TODAY, monthly_saving_cents=1)


@pytest.fixture
def conn(taxonomy_conn):
    taxonomy_conn.executemany(
        "INSERT INTO debts (id, kind, name, balance_cents, monthly_rate_bp, term_months, "
        "payment_cents, source, account_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "overdraft", "Conta corrente", -50000, None, None, None, "accounts", None),
            (2, "mortgage", "Financiamento imobiliário", -2000000, 72, 300, None, "financings", None),
            (3, "vehicle", "CDC do veículo", -3857960, 163, 44, PAYMENT, "financings", None),
        ],
    )
    taxonomy_conn.execute(
        "INSERT INTO financings (kind, monthly_rate_bp, term_months, balance_cents, "
        "payment_cents, first_due_date) VALUES ('vehicle', 163, 60, NULL, ?, '2025-06-11')",
        (PAYMENT,),
    )
    taxonomy_conn.executemany(
        "INSERT INTO commitments (kind, series_key, description, account, amount_cents, "
        "last_seen_date, last_installment, installment_total, installments_left, ends_month, "
        "dismissed) VALUES ('installment', ?, ?, 'Cartão', ?, ?, ?, ?, 0, NULL, 0)",
        [
            ("loja", "LOJA 12/12", -1390, "2027-05-06", 12, 12),
            ("fim", "ACABOU 6/6", -3654, "2026-08-29", 6, 6),
            ("sem", "SEM NUMERO", -500, "2026-09-02", None, 0),
        ],
    )
    taxonomy_conn.commit()
    return taxonomy_conn


def test_list_debts_joins_ladder_contract_and_live_purchases(conn):
    debts = {debt.key: debt for debt in list_debts(conn, today=TODAY)}

    assert set(debts) == {"debt-1", "debt-2", "debt-3", "installment-1"}
    assert debts["debt-3"].first_due == date(2025, 6, 11)
    assert debts["debt-3"].settlement_cents is None
    assert debts["debt-2"].installment_total == 300
    loja = debts["installment-1"]
    assert loja.first_due == date(2026, 6, 6)
    assert payoff_at(loja, TODAY, today=TODAY).installments_left == 8
    assert unnumbered(conn, today=TODAY) == ["SEM NUMERO"]


def test_list_debts_carries_the_settlement_the_owner_typed(conn):
    settings_store.write(conn, SETTLEMENT, "38.000,00", valid_until="2026-10-10")

    cdc = next(debt for debt in list_debts(conn, today=TODAY) if debt.key == "debt-3")

    assert cdc.settlement_cents == 3800000
    assert payoff_at(cdc, TODAY, today=TODAY).basis == INFORMED
