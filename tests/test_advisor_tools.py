import pytest

from app.advisor.provider import ToolCall
from app.advisor.tools import (
    ToolInputError,
    resolve_account,
    resolve_category,
    run_tool,
    search_transactions,
)
from app.queries.expenses import list_expenses, sum_expenses
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


def test_run_tool_turns_bad_input_and_unknown_tool_into_errors(conn):
    bad = run_tool(conn, ToolCall(id="c1", name="search_transactions", input={"limit": 99}))
    unknown = run_tool(conn, ToolCall(id="c2", name="apagar_tudo", input={}))
    good = run_tool(conn, ToolCall(id="c3", name="search_transactions", input={"text": "posto"}))

    assert bad.is_error and "limit" in bad.content["error"]
    assert unknown.is_error and "desconhecida" in unknown.content["error"]
    assert not good.is_error and good.content["count"] == 3
