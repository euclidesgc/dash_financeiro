import pytest

from app.db import connect
from app.ingest.loader import ingest
from app.migrate import run_migrations
from app.queries.spending import date_window, total_spending_cents

ACCOUNT = {
    "id": "acc-1",
    "type": "BANK",
    "subtype": "CHECKING_ACCOUNT",
    "name": "Conta de teste",
    "balance": 100.0,
}


def transaction(pluggy_id, date, valor, **overrides):
    row = {
        "id": pluggy_id,
        "data": date,
        "conta_id": ACCOUNT["id"],
        "descricao": pluggy_id,
        "valor": valor,
        "tipo": "DEBIT",
        "eh_transferencia": False,
        "motivo_transferencia": "",
        "eh_saque": False,
        "eh_estorno": False,
        "estornada_por": "",
        "nome_fantasia": "",
        "razao_social": "",
        "cnpj": "",
        "recebedor": "",
    }
    row.update(overrides)
    return row


@pytest.fixture
def conn(tmp_path):
    path = str(tmp_path / "dash.sqlite")
    run_migrations(path)
    connection = connect(path)
    yield connection
    connection.close()


@pytest.fixture
def loaded(conn):
    ingest(
        conn,
        transactions=[
            transaction("t-compra", "2025-08-01", -10.50),
            transaction("t-mercado", "2025-09-02", -30.25),
            transaction("t-salario", "2025-09-03", 500.00),
            transaction(
                "t-transferencia",
                "2025-09-04",
                -100.00,
                eh_transferencia=True,
                motivo_transferencia="pagamento de fatura",
            ),
            transaction(
                "t-estorno", "2025-09-05", 40.00, eh_estorno=True, estornada_por="t-debito"
            ),
            transaction("t-debito", "2025-09-05", -40.00, estornada_por="t-estorno"),
        ],
        accounts=[ACCOUNT],
        source="tests",
    )
    return conn


def test_ignores_income_transfer_refund_and_refunded_debit(loaded):
    assert total_spending_cents(loaded) == -4075


def test_window_narrows_the_total(loaded):
    assert total_spending_cents(loaded, start="2025-09-01") == -3025
    assert total_spending_cents(loaded, end="2025-08-31") == -1050
    assert total_spending_cents(loaded, start="2026-01-01") == 0


def test_a_row_marked_as_not_expense_leaves_the_total(loaded):
    loaded.execute(
        "UPDATE transactions SET not_expense_reason = 'own_transfer' WHERE pluggy_id = 't-mercado'"
    )
    loaded.commit()

    assert total_spending_cents(loaded) == -1050
    assert total_spending_cents(loaded, start="2025-09-01") == 0


def test_date_window_without_dates_is_empty():
    assert date_window(None, None) == ("", [])


def test_date_window_composes_the_column_and_the_bounds_in_order():
    assert date_window("2025-09-01", None, "t.date") == (" AND t.date >= ?", ["2025-09-01"])
    assert date_window(None, "2025-09-30") == (" AND date <= ?", ["2025-09-30"])
    assert date_window("2025-09-01", "2025-09-30") == (
        " AND date >= ? AND date <= ?",
        ["2025-09-01", "2025-09-30"],
    )
