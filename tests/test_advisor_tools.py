from datetime import date

import pytest

from app.advisor.provider import ToolCall
from app.advisor.tools import (
    ToolContext,
    ToolInputError,
    resolve_account,
    resolve_category,
    run_tool,
    search_transactions,
    spending_summary,
)
from app.queries.expenses import (
    list_expenses,
    monthly_totals,
    period_result,
    sum_by_category,
    sum_expenses,
)
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import load, transaction


@pytest.fixture
def conn(taxonomy_conn):
    seed_taxonomy(taxonomy_conn)
    load(
        taxonomy_conn,
        [
            transaction("p1", "2026-08-04", -100.00, descricao="Posto Sao Joao Macae"),
            transaction("p2", "2026-08-31", -85.50, descricao="Posto dos Cavaleiros"),
            transaction("p3", "2026-07-10", -40.00, descricao="Posto antigo"),
            transaction("f1", "2026-08-12", -23.45, descricao="Drogaria Raia"),
            transaction("s1", "2026-08-05", 5000.00, descricao="Salario", tipo="CREDIT"),
            transaction(
                "x1", "2026-08-06", -700.00, descricao="Posto transferencia", eh_transferencia=True
            ),
        ],
    )
    taxonomy_conn.execute(
        "UPDATE transactions SET category = 'Gas stations' WHERE pluggy_id IN ('p1', 'p2', 'p3')"
    )
    taxonomy_conn.execute("UPDATE transactions SET category = 'Pharmacy' WHERE pluggy_id = 'f1'")
    taxonomy_conn.commit()
    return taxonomy_conn


def test_category_filter_narrows_list_and_sum(conn):
    page = list_expenses(conn, page=1, page_size=10, category="Pharmacy")

    assert [item["description"] for item in page.items] == ["Drogaria Raia"]
    assert sum_expenses(conn, category="Gas stations") == -22550


def test_search_by_text_and_month_returns_count_total_and_formatted_amounts(conn):
    found = search_transactions(
        conn, {"text": "posto", "date_from": "2026-08-01", "date_to": "2026-08-31"}
    )

    assert found["count"] == 2
    assert found["total_cents"] == -18550
    assert found["total"] == "−R$ 185,50"
    assert [item["amount"] for item in found["items"]] == ["−R$ 85,50", "−R$ 100,00"]


def test_own_transfer_stays_out_of_the_total(conn):
    found = search_transactions(conn, {"text": "transferencia"})

    assert found["count"] == 0
    assert found["total_cents"] == 0


def test_category_is_resolved_by_label_without_accent_or_case(conn):
    found = search_transactions(conn, {"category": "farmacia"})

    assert found["filters"]["category"] == "Farmácia"
    assert found["total"] == "−R$ 23,45"


def test_income_kind_lists_entries(conn):
    found = search_transactions(conn, {"kind": "income"})

    assert found["count"] == 1
    assert found["total"] == "R$ 5.000,00"


def test_limit_caps_the_list_but_not_the_total(conn):
    found = search_transactions(conn, {"text": "posto", "limit": 1})

    assert found["shown"] == 1
    assert found["count"] == 3
    assert found["total_cents"] == -22550


def test_unknown_category_lists_the_known_ones(conn):
    with pytest.raises(ToolInputError, match="Categorias do painel: .*Farmácia"):
        resolve_category(conn, "Inexistente")


def test_account_is_resolved_by_name(conn):
    assert resolve_account(conn, "conta de teste").key == "acc-1"
    with pytest.raises(ToolInputError, match="não encontrada"):
        resolve_account(conn, "Banco imaginário")


@pytest.mark.parametrize(
    "arguments",
    [
        {"date_from": "08/2026"},
        {"date_from": "2026-08-31", "date_to": "2026-08-01"},
        {"text": "p"},
        {"kind": "outros"},
        {"limit": 0},
        {"limit": 51},
        {"limit": True},
        {"text": 12},
    ],
)
def test_invalid_input_is_refused(conn, arguments):
    with pytest.raises(ToolInputError):
        search_transactions(conn, arguments)


CONTEXT = ToolContext(conversation_id=1, now="2026-09-26T12:00:00+00:00", today=date(2026, 9, 26))


def test_run_tool_turns_bad_input_and_unknown_tool_into_errors(conn):
    bad = run_tool(
        conn, ToolCall(id="c1", name="search_transactions", input={"limit": 99}), CONTEXT
    )
    unknown = run_tool(conn, ToolCall(id="c2", name="apagar_tudo", input={}), CONTEXT)
    good = run_tool(
        conn, ToolCall(id="c3", name="search_transactions", input={"text": "posto"}), CONTEXT
    )

    assert bad.is_error and "limit" in bad.content["error"]
    assert unknown.is_error and "desconhecida" in unknown.content["error"]
    assert not good.is_error and good.content["count"] == 3


def test_spending_summary_gives_categories_period_and_months_as_the_panel(conn):
    window = {"date_from": "2026-07-01", "date_to": "2026-08-31"}
    found = spending_summary(conn, window)

    whole = period_result(conn, **window)
    assert (found["income_cents"], found["spending_cents"], found["balance_cents"]) == (
        whole.income_cents,
        whole.spending_cents,
        whole.balance_cents,
    )
    assert found["spending"] == "−R$ 248,95"
    assert found["income"] == "R$ 5.000,00"
    assert [(row["category"], row["total_cents"]) for row in found["by_category"]] == [
        (row.label, row.total_cents) for row in sum_by_category(conn, **window)
    ]
    assert [row["month"] for row in found["months"]] == [
        row.month for row in monthly_totals(conn, **window)
    ]
    assert found["months"][1]["spending"] == "−R$ 208,95"
    assert found["filters"] == {"date_from": "2026-07-01", "date_to": "2026-08-31", "account": None}


def test_spending_summary_by_category_leaves_the_own_transfer_out(conn):
    found = spending_summary(conn, {"date_from": "2026-08-01", "date_to": "2026-08-31"})

    assert [(row["category"], row["count"], row["total"]) for row in found["by_category"]] == [
        ("Posto de combustível", 2, "−R$ 185,50"),
        ("Farmácia", 1, "−R$ 23,45"),
    ]
    assert found["spending_cents"] == -20895


def test_spending_summary_filters_by_account_and_refuses_bad_input(conn):
    assert spending_summary(conn, {"account": "conta de teste"})["filters"]["account"]
    with pytest.raises(ToolInputError, match="não encontrada"):
        spending_summary(conn, {"account": "Banco imaginário"})
    with pytest.raises(ToolInputError, match="date_to"):
        spending_summary(conn, {"date_from": "2026-08-31", "date_to": "2026-08-01"})
    bad = run_tool(
        conn, ToolCall(id="c1", name="spending_summary", input={"date_to": "ontem"}), CONTEXT
    )
    assert bad.is_error and "AAAA-MM-DD" in bad.content["error"]


def _commitments(conn):
    conn.execute(
        "INSERT INTO commitments (kind, series_key, description, account, amount_cents, "
        "last_seen_date, last_installment, installment_total, installments_left, ends_month) "
        "VALUES ('installment', 'loja', 'LOJA 3/5', 'Cartão', -10000, '2026-09-11', 3, 5, 2, "
        "'2026-11')"
    )
    conn.execute(
        "INSERT INTO financings (kind, monthly_rate_bp, term_months, balance_cents, "
        "payment_cents, first_due_date) VALUES ('vehicle', 163, 60, NULL, -123533, '2025-06-11')"
    )
    conn.commit()


def test_commitments_by_month_formats_every_figure_and_traces_each_line(conn):
    _commitments(conn)

    result = run_tool(
        conn, ToolCall(id="c1", name="commitments_by_month", input={"months": 3}), CONTEXT
    )

    assert not result.is_error
    content = result.content
    assert [row["month"] for row in content["months"]] == ["2026-10", "2026-11", "2026-12"]
    october = content["months"][0]
    assert october["total"] == "−R$ 1.335,33"
    assert october["by_source"] == {
        "Compras parceladas": "−R$ 100,00",
        "Financiamentos": "−R$ 1.235,33",
        "Contas recorrentes e assinaturas": "R$ 0,00",
    }
    assert content["months"][1]["ending"] == ["LOJA 3/5"]
    assert content["window_total"] == "−R$ 3.905,99"
    loja = next(line for line in content["lines"] if line["description"] == "LOJA 3/5")
    assert loja["first_installment"] == "4/5"
    assert loja["last_installment_in_window"] == "5/5"
    assert loja["end_month"] == "2026-11"
    assert loja["amount"] == "−R$ 100,00"


def test_commitments_by_month_defaults_to_six_months_and_refuses_bad_windows(conn):
    default = run_tool(conn, ToolCall(id="c1", name="commitments_by_month", input={}), CONTEXT)
    too_long = run_tool(
        conn, ToolCall(id="c2", name="commitments_by_month", input={"months": 25}), CONTEXT
    )
    text = run_tool(
        conn, ToolCall(id="c3", name="commitments_by_month", input={"months": "seis"}), CONTEXT
    )

    assert len(default.content["months"]) == 6
    assert too_long.is_error and "months" in too_long.content["error"]
    assert text.is_error
