import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.advisor.provider import ToolCall, ToolResult, ToolSpec
from app.db import fold
from app.formatting import brl
from app.queries.balances import list_balances
from app.queries.categories import list_categories
from app.queries.expenses import View, list_expenses

SEARCH_TRANSACTIONS = "search_transactions"
DEFAULT_LIMIT = 20
MAX_LIMIT = 50
MIN_TEXT = 2
KINDS: dict[str, View] = {"expenses": "expenses", "income": "income"}

SEARCH_SPEC = ToolSpec(
    name=SEARCH_TRANSACTIONS,
    description=(
        "Busca lançamentos do painel e devolve a contagem, o total do filtro inteiro (em centavos "
        "e já escrito em reais) e até 50 lançamentos. Use para qualquer pergunta que liste, some "
        "ou conte gastos ou entradas. Transferência entre contas próprias e estorno já ficam de "
        "fora. Gasto tem valor negativo."
    ),
    parameters={
        "type": "object",
        "properties": {
            "date_from": {
                "type": "string",
                "description": "Primeiro dia do período, AAAA-MM-DD. Omita para desde o início.",
            },
            "date_to": {
                "type": "string",
                "description": "Último dia do período, AAAA-MM-DD, inclusive. Omita para até hoje.",
            },
            "text": {
                "type": "string",
                "description": (
                    "Trecho da descrição ou do nome de quem recebeu, sem distinguir acento nem "
                    "maiúscula (ex.: posto, ifood). Pelo menos 2 letras."
                ),
            },
            "category": {
                "type": "string",
                "description": "Categoria como o painel mostra (ex.: Farmácia, Supermercado).",
            },
            "account": {
                "type": "string",
                "description": "Nome da conta ou do banco (ex.: Nubank).",
            },
            "kind": {
                "type": "string",
                "enum": list(KINDS),
                "description": "expenses para gastos (padrão), income para entradas.",
            },
            "limit": {
                "type": "integer",
                "description": (
                    f"Quantos lançamentos listar, de 1 a {MAX_LIMIT}. Padrão {DEFAULT_LIMIT}."
                ),
            },
        },
    },
)

TOOLS = [SEARCH_SPEC]


class ToolInputError(ValueError):
    pass


@dataclass(frozen=True)
class _Resolved:
    key: str
    label: str


def _text(arguments: dict[str, Any], name: str) -> str | None:
    value = arguments.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ToolInputError(f"{name} precisa ser texto.")
    stripped = value.strip()
    return stripped or None


def _day(arguments: dict[str, Any], name: str) -> date | None:
    value = _text(arguments, name)
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ToolInputError(f"{name} precisa estar no formato AAAA-MM-DD.") from None


def _limit(arguments: dict[str, Any]) -> int:
    value = arguments.get("limit", DEFAULT_LIMIT)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_LIMIT:
        raise ToolInputError(f"limit precisa ser um número inteiro de 1 a {MAX_LIMIT}.")
    return value


def resolve_category(conn: sqlite3.Connection, asked: str) -> _Resolved:
    wanted = fold(asked)
    known = list_categories(conn)
    for category in known:
        if wanted in (fold(category.key), fold(category.label)):
            return _Resolved(key=category.key, label=category.label)
    labels = ", ".join(category.label for category in known)
    raise ToolInputError(f"Categoria '{asked}' não existe. Categorias do painel: {labels}.")


def resolve_account(conn: sqlite3.Connection, asked: str) -> _Resolved:
    wanted = fold(asked) or ""
    rows = list_balances(conn)
    names = {row["id"]: " · ".join(filter(None, (row["institution"], row["name"]))) for row in rows}
    found = [
        account_id for account_id, name in names.items() if wanted and wanted in (fold(name) or "")
    ]
    if len(found) == 1:
        return _Resolved(key=found[0], label=names[found[0]])
    listed = "; ".join(names.values())
    if not found:
        raise ToolInputError(f"Conta '{asked}' não encontrada. Contas do painel: {listed}.")
    matches = "; ".join(names[account_id] for account_id in found)
    raise ToolInputError(f"'{asked}' corresponde a mais de uma conta: {matches}. Seja específico.")


def search_transactions(conn: sqlite3.Connection, arguments: dict[str, Any]) -> dict[str, Any]:
    date_from = _day(arguments, "date_from")
    date_to = _day(arguments, "date_to")
    if date_from and date_to and date_to < date_from:
        raise ToolInputError("date_to precisa ser igual ou posterior a date_from.")
    text = _text(arguments, "text")
    if text is not None and len(text) < MIN_TEXT:
        raise ToolInputError(f"text precisa de pelo menos {MIN_TEXT} letras.")
    kind = _text(arguments, "kind") or "expenses"
    if kind not in KINDS:
        raise ToolInputError("kind precisa ser expenses ou income.")
    limit = _limit(arguments)
    asked_category = _text(arguments, "category")
    category = resolve_category(conn, asked_category) if asked_category else None
    asked_account = _text(arguments, "account")
    account = resolve_account(conn, asked_account) if asked_account else None
    page = list_expenses(
        conn,
        page=1,
        page_size=limit,
        view=KINDS[kind],
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        account_id=account.key if account else None,
        search=text,
        category=category.key if category else None,
    )
    items = [
        {
            "id": item["id"],
            "date": item["date"],
            "description": item["description"],
            "payee": item["payee_name"],
            "account": " · ".join(
                filter(None, (item["account_institution"], item["account_name"]))
            ),
            "category": item["category"],
            "amount_cents": item["amount_cents"],
            "amount": brl(item["amount_cents"]),
        }
        for item in page.items
    ]
    return {
        "filters": {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "text": text,
            "category": category.label if category else None,
            "account": account.label if account else None,
            "kind": kind,
        },
        "count": page.total,
        "total_cents": page.total_cents,
        "total": brl(page.total_cents),
        "shown": len(items),
        "items": items,
    }


_HANDLERS = {SEARCH_TRANSACTIONS: search_transactions}


def run_tool(conn: sqlite3.Connection, call: ToolCall) -> ToolResult:
    handler = _HANDLERS.get(call.name)
    if handler is None:
        return ToolResult(
            call_id=call.id,
            name=call.name,
            content={"error": f"Ferramenta desconhecida: {call.name}."},
            is_error=True,
        )
    try:
        content = handler(conn, call.input)
    except ToolInputError as error:
        failure = {"error": str(error)}
        return ToolResult(call_id=call.id, name=call.name, content=failure, is_error=True)
    return ToolResult(call_id=call.id, name=call.name, content=content)
