from typing import Any
from urllib.parse import urlencode, urlparse

import httpx

from app.config import Config
from ingestao.pluggy_consolidate import NoRawAccountsError, consolidate
from ingestao.raw import salvar

API = "https://api.pluggy.ai"
SOURCE = "pluggy"
PAGE_SIZE = 500
RELINK_STATUSES = frozenset({"LOGIN_ERROR", "WAITING_USER_INPUT", "USER_AUTHORIZATION_REVOKED"})

REFUSED = (
    "pluggy: a Pluggy recusou as credenciais; confira PLUGGY_CLIENT_ID e PLUGGY_CLIENT_SECRET."
)
UNREACHABLE = "pluggy: a Pluggy não respondeu; verifique a conexão com a internet e tente de novo."
NO_ITEMS = "pluggy: nenhuma conexão cadastrada; cadastre em Conexões."
CONSOLIDATION_FAILED = "pluggy: a consolidação dos dados brutos falhou."


class PluggyFetchError(RuntimeError):
    pass


def relink_message(name: str) -> str:
    return f"pluggy: a conexão {name} pede novo login em meu.pluggy.ai."


def unexpected_message(status: int, path: str) -> str:
    return f"pluggy: a Pluggy respondeu {status} em {path}."


def fetch_from_pluggy(
    config: Config, item_ids: list[str], *, transport: httpx.BaseTransport | None = None
) -> None:
    if not item_ids:
        raise PluggyFetchError(NO_ITEMS)
    try:
        with httpx.Client(base_url=API, timeout=60.0, transport=transport) as client:
            client.headers["X-API-KEY"] = _authenticate(client, config)
            for item_id in item_ids:
                _fetch_item(client, item_id)
    except httpx.HTTPError as failure:
        raise PluggyFetchError(UNREACHABLE) from failure
    try:
        consolidate()
    except NoRawAccountsError as failure:
        raise PluggyFetchError(CONSOLIDATION_FAILED) from failure


def _authenticate(client: httpx.Client, config: Config) -> str:
    response = client.post(
        "/auth",
        json={
            "clientId": config.pluggy["PLUGGY_CLIENT_ID"],
            "clientSecret": config.pluggy["PLUGGY_CLIENT_SECRET"],
        },
    )
    if response.status_code != 200:
        raise PluggyFetchError(REFUSED)
    return str(response.json()["apiKey"])


def _get(client: httpx.Client, path: str, params: dict[str, Any] | None = None) -> Any:
    response = client.get(path, params=params)
    if response.status_code != 200:
        raise PluggyFetchError(unexpected_message(response.status_code, response.request.url.path))
    return response.json()


def _fetch_item(client: httpx.Client, item_id: str) -> None:
    short = item_id[:8]
    response = client.get(f"/items/{item_id}")
    if response.status_code == 404:
        raise PluggyFetchError(relink_message(short))
    if response.status_code != 200:
        raise PluggyFetchError(unexpected_message(response.status_code, response.request.url.path))
    item = response.json()
    if item.get("status") in RELINK_STATUSES or item.get("executionStatus") in RELINK_STATUSES:
        raise PluggyFetchError(relink_message((item.get("connector") or {}).get("name") or short))
    salvar(f"item_{short}", item)
    accounts = _get(client, "/accounts", {"itemId": item_id, "pageSize": PAGE_SIZE})
    salvar(f"accounts_{short}", accounts)
    for account in accounts.get("results", []):
        _fetch_transactions(client, str(account["id"]))


def _fetch_transactions(client: httpx.Client, account_id: str) -> None:
    # Reason: unlike /accounts, /v2/transactions refuses pageSize with a 400
    # ("property pageSize should not exist"); its page size is the server's.
    params: dict[str, Any] = {"accountId": account_id}
    query = urlencode(params)
    page = 1
    while True:
        body = _get(client, f"/v2/transactions?{query}")
        salvar(f"v2_transactions_{account_id[:8]}", body, page)
        cursor = body.get("next")
        if not cursor or not body.get("results"):
            return
        query = _next_query(cursor, params)
        page += 1


def _next_query(cursor: str, params: dict[str, Any]) -> str:
    # Reason: Pluggy has answered `next` as a query string, as a full URL and
    # as a bare cursor; the extraction script follows the same three shapes.
    if cursor.startswith("?"):
        return cursor[1:]
    if cursor.startswith("http"):
        return urlparse(cursor).query
    return urlencode({**params, "after": cursor})
