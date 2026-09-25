import json
from collections.abc import Callable

import httpx
import pytest

from app.config import Config, load_config
from app.sync.fetch import PluggyFetchError, fetch_from_pluggy

CLIENT_ID = "id-teste"
SECRET = "segredo-muito-secreto"
API_KEY = "chave-api-secreta"
ITEM_ID = "item-abc12345"
ITEMS = [ITEM_ID]


@pytest.fixture()
def workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    return tmp_path


def config_with(client_id: str = CLIENT_ID, secret: str = SECRET) -> Config:
    return load_config(
        {
            "PLUGGY_CLIENT_ID": client_id,
            "PLUGGY_CLIENT_SECRET": secret,
            "DASH_SYNC_SOURCE": "pluggy",
        }
    )


def transport(
    routes: dict[tuple[str, str], Callable[[httpx.Request], httpx.Response]],
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        route = routes.get(key)
        if route is None:
            raise AssertionError(f"rota não mapeada no teste: {key}")
        return route(request)

    return httpx.MockTransport(handler)


def _auth(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"apiKey": API_KEY})


def _item_ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": ITEM_ID,
            "status": "UPDATED",
            "executionStatus": "SUCCESS",
            "connector": {"name": "Banco Teste"},
        },
    )


def _accounts_ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "results": [
                {
                    "id": "acc-fetch-1",
                    "type": "BANK",
                    "subtype": "CHECKING_ACCOUNT",
                    "name": "Conta buscada",
                    "marketingName": "Banco Teste",
                    "balance": 42.0,
                    "currencyCode": "BRL",
                }
            ]
        },
    )


def _transactions_ok(request: httpx.Request) -> httpx.Response:
    if "after=c2" in str(request.url):
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "tx-2",
                        "accountId": "acc-fetch-1",
                        "date": "2026-09-21T00:00:00.000Z",
                        "amount": -20.0,
                        "description": "Farmácia",
                    }
                ],
                "next": None,
            },
        )
    return httpx.Response(
        200,
        json={
            "results": [
                {
                    "id": "tx-1",
                    "accountId": "acc-fetch-1",
                    "date": "2026-09-20T00:00:00.000Z",
                    "amount": -10.0,
                    "description": "Padaria",
                }
            ],
            "next": "?accountId=acc-fetch-1&after=c2",
        },
    )


def happy_routes(overrides: dict | None = None) -> dict:
    routes = {
        ("POST", "/auth"): _auth,
        ("GET", f"/items/{ITEM_ID}"): _item_ok,
        ("GET", "/accounts"): _accounts_ok,
        ("GET", "/v2/transactions"): _transactions_ok,
    }
    if overrides:
        routes.update(overrides)
    return routes


def recording_transport(routes: dict) -> httpx.MockTransport:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        key = (request.method, request.url.path)
        route = routes.get(key)
        if route is None:
            raise AssertionError(f"rota não mapeada no teste: {key}")
        return route(request)

    mock = httpx.MockTransport(handler)
    mock.seen = seen  # type: ignore[attr-defined]
    return mock


def test_the_happy_path_writes_raw_files_and_consolidates(workspace):
    mock = recording_transport(happy_routes())

    fetch_from_pluggy(config_with(), ITEMS, transport=mock)

    raw = list((workspace / "data" / "raw").glob("accounts_item-abc*.json"))
    assert raw, "esperava um data/raw/accounts_item-abc*.json"
    page1 = list((workspace / "data" / "raw").glob("v2_transactions_acc-fetc*_p1.json"))
    page2 = list((workspace / "data" / "raw").glob("v2_transactions_acc-fetc*_p2.json"))
    assert page1 and page2
    processed = json.loads((workspace / "data" / "processed" / "transacoes.json").read_text())
    assert len(processed) == 2
    for request in mock.seen[1:]:  # type: ignore[attr-defined]
        assert request.headers["X-API-KEY"] == API_KEY


def test_the_transaction_pages_follow_the_next_cursor(workspace):
    mock = recording_transport(happy_routes())

    fetch_from_pluggy(config_with(), ITEMS, transport=mock)

    transaction_requests = [
        request
        for request in mock.seen  # type: ignore[attr-defined]
        if request.url.path == "/v2/transactions"
    ]
    assert len(transaction_requests) == 2
    assert "after=c2" in str(transaction_requests[1].url)


def test_a_401_on_auth_means_refused_credentials(workspace):
    mock = transport({("POST", "/auth"): lambda request: httpx.Response(401, json={})})

    with pytest.raises(PluggyFetchError, match="recusou as credenciais"):
        fetch_from_pluggy(config_with(), ITEMS, transport=mock)


def test_a_connect_error_means_pluggy_did_not_answer(workspace):
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    mock = transport({("POST", "/auth"): boom})

    with pytest.raises(PluggyFetchError, match="não respondeu"):
        fetch_from_pluggy(config_with(), ITEMS, transport=mock)


def test_a_login_error_item_asks_for_a_new_login(workspace):
    def item_login_error(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": ITEM_ID,
                "status": "LOGIN_ERROR",
                "executionStatus": "LOGIN_ERROR",
                "connector": {"name": "Banco Teste"},
            },
        )

    mock = transport(happy_routes({("GET", f"/items/{ITEM_ID}"): item_login_error}))

    with pytest.raises(
        PluggyFetchError, match="a conexão Banco Teste pede novo login em meu.pluggy.ai."
    ):
        fetch_from_pluggy(config_with(), ITEMS, transport=mock)


def test_a_404_item_asks_for_a_new_login_by_id(workspace):
    def item_404(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={})

    mock = transport(happy_routes({("GET", f"/items/{ITEM_ID}"): item_404}))

    with pytest.raises(PluggyFetchError, match="a conexão item-abc pede novo login"):
        fetch_from_pluggy(config_with(), ITEMS, transport=mock)


def test_any_other_status_is_reported_with_the_path(workspace):
    def accounts_500(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    mock = transport(happy_routes({("GET", "/accounts"): accounts_500}))

    with pytest.raises(PluggyFetchError, match="a Pluggy respondeu 500 em /accounts."):
        fetch_from_pluggy(config_with(), ITEMS, transport=mock)


def test_an_empty_item_list_is_a_failure(workspace):
    with pytest.raises(PluggyFetchError, match="nenhuma conexão cadastrada; cadastre em Conexões"):
        fetch_from_pluggy(config_with(), [])


def test_no_message_ever_contains_the_secret_or_the_api_key(workspace):
    scenarios = [
        transport({("POST", "/auth"): lambda request: httpx.Response(401, json={})}),
        transport(
            happy_routes(
                {("GET", f"/items/{ITEM_ID}"): lambda request: httpx.Response(404, json={})}
            )
        ),
        transport(
            happy_routes({("GET", "/accounts"): lambda request: httpx.Response(500, json={})})
        ),
    ]
    for mock in scenarios:
        with pytest.raises(PluggyFetchError) as failure:
            fetch_from_pluggy(config_with(), ITEMS, transport=mock)
        assert SECRET not in str(failure.value)
        assert API_KEY not in str(failure.value)


def test_a_failure_in_one_item_writes_no_processed_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    second_item = "item-second9"

    def item_router(request: httpx.Request) -> httpx.Response:
        if request.url.path == f"/items/{second_item}":
            return httpx.Response(404, json={})
        return _item_ok(request)

    routes = happy_routes(
        {
            (
                "GET",
                f"/items/{ITEM_ID}",
            ): item_router,
            ("GET", f"/items/{second_item}"): item_router,
        }
    )
    mock = transport(routes)

    with pytest.raises(PluggyFetchError, match="pede novo login"):
        fetch_from_pluggy(config_with(), [ITEM_ID, second_item], transport=mock)

    assert not (tmp_path / "data" / "processed" / "transacoes.json").exists()


def test_no_accounts_at_pluggy_means_the_consolidation_failed(workspace):
    def no_accounts(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    mock = transport(happy_routes({("GET", "/accounts"): no_accounts}))

    with pytest.raises(PluggyFetchError, match="a consolidação dos dados brutos falhou"):
        fetch_from_pluggy(config_with(), ITEMS, transport=mock)
