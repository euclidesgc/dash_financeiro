from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect, fold
from app.ingest.loader import ingest
from app.ingest.source import load_accounts
from app.ingest.trigger import COMMAND
from app.main import create_app
from app.queries.categories import category_labels
from app.taxonomy.seed import UNCATEGORISED, pickable_categories, seed_taxonomy

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
DATA = Path(__file__).parent / "data"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TRANSACTIONS_PATH", str(DATA / "sync_transactions.json"))
    monkeypatch.setenv("DASH_ACCOUNTS_GLOB", str(DATA / "sync_accounts.json"))
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    seed_taxonomy(conn)
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        yield opened


def _sign_in(client):
    client.post("/api/auth/login", json={"login": LOGIN, "password": PASSWORD})


def _transaction(id: str, date: str, amount: float, **overrides: Any) -> dict[str, Any]:
    row = {
        "id": id,
        "data": date,
        "conta_id": "sync-acc-1",
        "descricao": f"GASTO {id}",
        "valor": amount,
        "tipo": "DEBIT",
        "categoria_pluggy": "",
        "categoria": "",
        "parcela_atual": None,
        "parcela_total": None,
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


def _load(rows: list[dict[str, Any]], accounts: list[dict[str, Any]] | None = None) -> None:
    conn = connect()
    ingest(
        conn,
        transactions=rows,
        accounts=[*load_accounts(str(DATA / "sync_accounts.json")), *(accounts or [])],
        source="teste",
        trigger=COMMAND,
    )
    conn.close()


def test_categories_without_session_answers_401(client):
    response = client.get("/api/categories")

    assert response.status_code == 401
    assert response.json() == {"detail": "nao autenticado"}


def test_categories_lists_the_pickable_seed_in_label_order(client):
    _sign_in(client)
    conn = connect()
    try:
        expected = [
            {"key": c.key, "label": c.label, "is_system": True, "usage_count": 0}
            for c in pickable_categories(conn)
        ]
    finally:
        conn.close()

    expected = [{**item, "monthly_limit_cents": None} for item in expected]

    response = client.get("/api/categories")

    assert response.status_code == 200
    assert response.json()["categories"] == expected
    assert {
        "key": "Groceries",
        "label": "Supermercado",
        "is_system": True,
        "usage_count": 0,
        "monthly_limit_cents": None,
    } in expected


def test_categories_never_contains_the_uncategorised_key(client):
    _sign_in(client)

    response = client.get("/api/categories")

    categories = response.json()["categories"]
    assert all(item["key"] != UNCATEGORISED for item in categories)
    assert all(item["label"] != "Sem categoria" for item in categories)


def test_usage_count_counts_the_transactions_with_the_key(client):
    _sign_in(client)
    _load(
        [
            _transaction("g1", "2026-09-01", -10.0, categoria="Groceries"),
            _transaction("g2", "2026-09-02", -20.0, categoria="Groceries"),
        ]
    )

    response = client.get("/api/categories")

    categories = {item["key"]: item["usage_count"] for item in response.json()["categories"]}
    assert categories["Groceries"] == 2
    assert all(count == 0 for key, count in categories.items() if key != "Groceries")


def test_categories_are_ordered_by_folded_label(client):
    _sign_in(client)

    response = client.get("/api/categories")

    labels = [item["label"] for item in response.json()["categories"]]
    assert [fold(label) for label in labels] == sorted(fold(label) for label in labels)
    assert labels.index("Água") < labels.index("Casa")


def test_the_openapi_lists_categories(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    assert "get" in response.json()["paths"]["/api/categories"]


def _post(client, label: str):
    return client.post("/api/categories", json={"label": label})


def _patch(client, key: str, label: str):
    return client.patch(f"/api/categories/{key}", json={"label": label})


def _delete(client, key: str):
    return client.delete(f"/api/categories/{key}")


def _keys(client) -> list[str]:
    return [item["key"] for item in client.get("/api/categories").json()["categories"]]


def _put_limit(client, key: str, cents: int | None):
    return client.put(f"/api/categories/{key}/limit", json={"monthly_limit_cents": cents})


def _limit_of(client, key: str):
    return next(
        item["monthly_limit_cents"] for item in _list_categories(client) if item["key"] == key
    )


def test_post_creates_the_category_and_it_is_pickable_for_an_expense(client):
    _sign_in(client)
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries")])
    expense_id = client.get("/api/transactions/expenses").json()["items"][0]["id"]

    response = _post(client, "Pet shop")

    assert response.status_code == 201
    assert response.json() == {
        "key": "pet-shop",
        "label": "Pet shop",
        "is_system": False,
        "usage_count": 0,
        "monthly_limit_cents": None,
    }
    assert "pet-shop" in _keys(client)

    manual = client.patch(
        f"/api/transactions/{expense_id}/category",
        json={"mode": "manual", "category": "pet-shop"},
    )
    assert manual.status_code == 200
    assert manual.json()["category"] == "Pet shop"
    assert manual.json()["category_key"] == "pet-shop"

    categories = {item["key"]: item["usage_count"] for item in _list_categories(client)}
    assert categories["pet-shop"] == 1


def _list_categories(client):
    return client.get("/api/categories").json()["categories"]


def test_post_refuses_an_empty_label_with_422(client):
    _sign_in(client)

    response = _post(client, "   ")

    assert response.status_code == 422
    assert response.json() == {"detail": "Informe o nome da categoria."}


def test_post_refuses_a_duplicate_label_ignoring_case_and_accents_with_422(client):
    _sign_in(client)

    response = _post(client, "supermercádo")

    assert response.status_code == 422
    assert response.json() == {"detail": "Já existe uma categoria com esse nome."}


def test_post_without_label_answers_422_from_pydantic(client):
    _sign_in(client)

    response = client.post("/api/categories", json={})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_patch_renames_and_the_expenses_show_the_new_label(client):
    _sign_in(client)
    _load([_transaction("g1", "2026-09-01", -60.0, categoria="Groceries")])

    response = _patch(client, "Groceries", "Mercado")

    assert response.status_code == 200
    assert response.json()["label"] == "Mercado"
    assert response.json()["is_system"] is True
    assert response.json()["usage_count"] == 1

    expenses = client.get("/api/transactions/expenses").json()["items"]
    assert expenses[0]["category"] == "Mercado"


def test_patch_refuses_a_duplicate_label_with_422(client):
    _sign_in(client)

    response = _patch(client, "Groceries", "Casa")

    assert response.status_code == 422
    assert response.json() == {"detail": "Já existe uma categoria com esse nome."}


def test_patch_accepts_the_own_label_in_another_case(client):
    _sign_in(client)

    response = _patch(client, "Groceries", "SUPERMERCADO")

    assert response.status_code == 200


def test_patch_an_unknown_key_and_the_uncategorised_key_answer_404(client):
    _sign_in(client)

    unknown = _patch(client, "nao-existe", "Novo")
    uncategorised = _patch(client, "Não classificado", "Novo")

    assert unknown.status_code == 404
    assert unknown.json() == {"detail": "Categoria não encontrada."}
    assert uncategorised.status_code == 404
    assert uncategorised.json() == {"detail": "Categoria não encontrada."}


def test_delete_removes_a_free_category_and_it_leaves_the_list(client):
    _sign_in(client)
    _post(client, "Pet shop")

    response = _delete(client, "pet-shop")

    assert response.status_code == 204
    assert response.content == b""
    assert "pet-shop" not in _keys(client)


def test_delete_refuses_a_system_category_with_403(client):
    _sign_in(client)

    response = _delete(client, "Groceries")

    assert response.status_code == 403
    assert response.json() == {"detail": "Categoria do sistema não pode ser apagada."}


def test_delete_refuses_a_category_in_use_with_409(client):
    _sign_in(client)
    _load(
        [
            _transaction("g1", "2026-09-01", -10.0),
            _transaction("g2", "2026-09-02", -20.0),
        ]
    )
    ids = [item["id"] for item in client.get("/api/transactions/expenses").json()["items"]]
    _post(client, "Pet shop")
    for expense_id in ids:
        client.patch(
            f"/api/transactions/{expense_id}/category",
            json={"mode": "manual", "category": "pet-shop"},
        )

    response = _delete(client, "pet-shop")

    assert response.status_code == 409
    assert response.json() == {"detail": "Esta categoria está em uso por 2 gastos."}

    client.patch(f"/api/transactions/{ids[0]}/category", json={"mode": "manual", "category": None})
    single = _delete(client, "pet-shop")
    assert single.status_code == 409
    assert single.json() == {"detail": "Esta categoria está em uso por 1 gasto."}


def test_delete_an_unknown_key_answers_404(client):
    _sign_in(client)

    response = _delete(client, "nao-existe")

    assert response.status_code == 404
    assert response.json() == {"detail": "Categoria não encontrada."}


def test_write_routes_without_session_answer_401(client):
    post_response = _post(client, "Pet shop")
    patch_response = _patch(client, "Groceries", "Mercado")
    delete_response = _delete(client, "Groceries")

    assert post_response.status_code == 401
    assert patch_response.status_code == 401
    assert delete_response.status_code == 401


def test_the_openapi_lists_the_write_routes(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    paths = response.json()["paths"]
    assert "post" in paths["/api/categories"]
    assert "patch" in paths["/api/categories/{key}"]
    assert "delete" in paths["/api/categories/{key}"]


def test_categories_carry_a_null_limit_after_the_seed(client):
    _sign_in(client)

    response = client.get("/api/categories")

    categories = response.json()["categories"]
    assert categories
    for item in categories:
        assert "monthly_limit_cents" in item
        assert item["monthly_limit_cents"] is None


def test_put_limit_writes_the_cents_and_the_list_reflects_it(client):
    _sign_in(client)

    response = _put_limit(client, "Shopping", 150000)

    assert response.status_code == 200
    body = response.json()
    assert body["key"] == "Shopping"
    assert body["monthly_limit_cents"] == 150000
    assert {"label", "is_system", "usage_count"}.issubset(body.keys())
    assert _limit_of(client, "Shopping") == 150000


def test_put_limit_with_null_clears_it(client):
    _sign_in(client)
    _put_limit(client, "Shopping", 150000)

    response = _put_limit(client, "Shopping", None)

    assert response.status_code == 200
    assert response.json()["monthly_limit_cents"] is None
    assert _limit_of(client, "Shopping") is None


def test_put_limit_refuses_zero_and_negative_with_422_and_keeps_the_previous_value(client):
    _sign_in(client)
    _put_limit(client, "Shopping", 150000)

    zero = _put_limit(client, "Shopping", 0)
    negative = _put_limit(client, "Shopping", -5)

    assert zero.status_code == 422
    assert zero.json() == {"detail": "O limite precisa ser maior que zero."}
    assert negative.status_code == 422
    assert negative.json() == {"detail": "O limite precisa ser maior que zero."}
    assert _limit_of(client, "Shopping") == 150000


def test_put_limit_without_the_field_answers_422_from_pydantic(client):
    _sign_in(client)

    without_field = client.put("/api/categories/Shopping/limit", json={})
    assert without_field.status_code == 422
    assert isinstance(without_field.json()["detail"], list)

    not_an_integer = client.put(
        "/api/categories/Shopping/limit", json={"monthly_limit_cents": 12.5}
    )
    assert not_an_integer.status_code == 422


def test_put_limit_an_unknown_key_and_the_uncategorised_key_answer_404(client):
    _sign_in(client)

    unknown = _put_limit(client, "Inexistente", 100)
    uncategorised = _put_limit(client, "Não classificado", 100)

    assert unknown.status_code == 404
    assert unknown.json() == {"detail": "Categoria não encontrada."}
    assert uncategorised.status_code == 404
    assert uncategorised.json() == {"detail": "Categoria não encontrada."}


def test_put_limit_accepts_a_system_category(client):
    _sign_in(client)
    groceries = next(item for item in _list_categories(client) if item["key"] == "Groceries")
    assert groceries["is_system"] is True

    response = _put_limit(client, "Groceries", 5000)

    assert response.status_code == 200


def test_put_limit_without_session_answers_401(client):
    response = _put_limit(client, "Shopping", 150000)

    assert response.status_code == 401


def test_the_openapi_lists_the_limit_route(client):
    _sign_in(client)

    response = client.get("/openapi.json")

    assert "put" in response.json()["paths"]["/api/categories/{key}/limit"]


def test_category_labels_reads_every_row_of_categories(client):
    conn = connect()
    try:
        conn.execute(
            "UPDATE categories SET label = 'Rótulo do dono' WHERE name = ?", (UNCATEGORISED,)
        )
        conn.commit()
        rows = conn.execute("SELECT name, label FROM categories").fetchall()
        labels = category_labels(conn)
    finally:
        conn.close()

    assert labels == {row["name"]: row["label"] for row in rows}
    assert labels[UNCATEGORISED] == "Rótulo do dono"
