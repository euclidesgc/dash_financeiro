import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import load_seed, seed_taxonomy
from tests.conftest import load, narrowed, transaction

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
TODAY = "2026-09-05"

BEYOND_SQLITE = 2**63
FAR_BEYOND_SQLITE = 10**20
LARGEST_AMOUNT = 999_999_999_999
LAST_PAGE = (2**63 - 1) // 100

CEILING_TOO_LARGE = "O teto passa do maior valor aceito, R$ 9.999.999.999,99."
LIMIT_TOO_LARGE = "O limite passa do maior valor aceito, R$ 9.999.999.999,99."
DEBT_NOT_FOUND = "Dívida não encontrada."


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", TODAY)
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    load(conn, [transaction("t-1", "2026-09-02", -100.00, descricao="Mercado Livre")])
    seed_taxonomy(conn, narrowed(load_seed(), []))
    classify_all(conn)
    conn.commit()
    conn.close()
    # Reason: a 500 must come back as a status to assert on, not as the
    # exception the test client re-raises by default.
    with TestClient(app, follow_redirects=False, raise_server_exceptions=False) as opened:
        opened.post("/api/auth/login", json={"login": LOGIN, "password": PASSWORD})
        yield opened


def _transaction_id() -> int:
    conn = connect()
    try:
        return int(conn.execute("SELECT id FROM transactions").fetchone()[0])
    finally:
        conn.close()


@pytest.mark.parametrize("page", [BEYOND_SQLITE, FAR_BEYOND_SQLITE])
def test_a_page_whose_offset_does_not_fit_sqlite_answers_422(client, page):
    response = client.get("/api/transactions/expenses", params={"page": page})

    assert response.status_code == 422


def test_the_last_page_whose_offset_fits_sqlite_answers_empty(client):
    response = client.get(
        "/api/transactions/expenses", params={"page": LAST_PAGE, "page_size": 100}
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_the_ceiling_past_the_largest_amount_answers_422_in_portuguese(client):
    for cents in (LARGEST_AMOUNT + 1, FAR_BEYOND_SQLITE):
        response = client.put("/api/plan/ceiling", json={"monthly_ceiling_cents": cents})

        assert response.status_code == 422
        assert response.json() == {"detail": CEILING_TOO_LARGE}

    largest = client.put("/api/plan/ceiling", json={"monthly_ceiling_cents": LARGEST_AMOUNT})

    assert largest.status_code == 200
    assert largest.json() == {"monthly_ceiling_cents": LARGEST_AMOUNT}


def test_the_category_limit_past_the_largest_amount_answers_422_in_portuguese(client):
    key = client.post("/api/categories", json={"label": "Mercado"}).json()["key"]

    for cents in (LARGEST_AMOUNT + 1, FAR_BEYOND_SQLITE):
        response = client.put(f"/api/categories/{key}/limit", json={"monthly_limit_cents": cents})

        assert response.status_code == 422
        assert response.json() == {"detail": LIMIT_TOO_LARGE}

    largest = client.put(
        f"/api/categories/{key}/limit", json={"monthly_limit_cents": LARGEST_AMOUNT}
    )

    assert largest.status_code == 200
    assert largest.json()["monthly_limit_cents"] == LARGEST_AMOUNT


@pytest.mark.parametrize(
    ("method", "suffix", "body"),
    [
        ("PATCH", "category", {"mode": "auto"}),
        ("PUT", "not-expense", {"reason": "other"}),
        ("DELETE", "not-expense", None),
        ("GET", "similar", None),
        ("POST", "category/apply-to-similar", {"category": "Groceries"}),
    ],
)
@pytest.mark.parametrize("transaction_id", [BEYOND_SQLITE, FAR_BEYOND_SQLITE, -BEYOND_SQLITE - 1])
def test_a_transaction_id_that_does_not_fit_sqlite_answers_422(
    client, method, suffix, body, transaction_id
):
    response = client.request(method, f"/api/transactions/{transaction_id}/{suffix}", json=body)

    assert response.status_code == 422


@pytest.mark.parametrize("path", ["/dividas/taxa", "/dividas/simular"])
def test_a_debt_step_that_does_not_fit_sqlite_is_a_debt_not_found(client, path):
    response = client.post(
        path, data={"degrau": str(FAR_BEYOND_SQLITE), "taxa": "1", "aporte": "1,00"}
    )

    assert response.status_code == 400
    assert DEBT_NOT_FOUND in response.text


@pytest.mark.parametrize(
    "params",
    [
        {"fim": "9999-12-31"},
        {"inicio": "0001-01-01", "fim": "9999-12-31"},
        {"inicio": "9999-12-01", "fim": "9999-12-31"},
    ],
)
def test_the_spending_screen_opens_on_the_last_day_the_calendar_has(client, params):
    response = client.get("/gastos", params=params)

    assert response.status_code == 200
    assert 'value="9999-12-31"' in response.text


def test_a_correction_target_that_does_not_fit_sqlite_is_no_target(client):
    screen = client.get("/gastos", params={"corrigir": FAR_BEYOND_SQLITE})
    detail = client.get(
        "/gastos/detalhe",
        params={"eixo": "grupo", "chave": "Outros", "corrigir": FAR_BEYOND_SQLITE},
    )

    assert screen.status_code == 200
    assert 'id="correcao"' not in screen.text
    assert detail.status_code == 200
    assert 'id="correcao"' not in detail.text


def test_a_correction_group_that_does_not_fit_sqlite_reads_as_no_group(client):
    target = _transaction_id()

    def correct(group: str):
        return client.post(
            "/gastos/correcao",
            params={"eixo": "grupo", "chave": "Outros", "corrigir": target},
            data={"grupo": group, "natureza": "", "essencialidade": "", "grupo_novo": ""},
        )

    beyond = correct(str(FAR_BEYOND_SQLITE))
    not_a_number = correct("abc")

    assert beyond.status_code == not_a_number.status_code
    assert beyond.status_code < 500


def test_a_rule_group_that_does_not_fit_sqlite_is_refused_as_an_invalid_group(client):
    response = client.post(
        "/regras",
        data={
            "match_kind": "description",
            "match_value": "Mercado",
            "group_id": str(FAR_BEYOND_SQLITE),
            "nature": "",
            "essentiality": "",
        },
    )

    assert response.status_code == 400
    assert f"grupo inválido: {FAR_BEYOND_SQLITE}" in response.text


@pytest.mark.parametrize("action", ["editar", "remover"])
def test_a_rule_id_that_does_not_fit_sqlite_answers_422(client, action):
    response = client.post(
        f"/regras/{FAR_BEYOND_SQLITE}/{action}",
        data={"match_kind": "description", "match_value": "Mercado", "group_id": "1"},
    )

    assert response.status_code == 422
