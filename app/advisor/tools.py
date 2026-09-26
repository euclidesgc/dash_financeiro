import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.advisor.proposals import propose
from app.advisor.provider import ToolCall, ToolResult, ToolSpec
from app.db import fold
from app.formatting import brl
from app.queries.advisor_proposals import ProposalRow, transaction_snapshots
from app.queries.balances import list_balances
from app.queries.categories import list_categories
from app.queries.expenses import (
    View,
    list_expenses,
    monthly_totals,
    period_result,
    sum_by_category,
)

SEARCH_TRANSACTIONS = "search_transactions"
SPENDING_SUMMARY = "spending_summary"
PROPOSE_RECATEGORIZATION = "propose_recategorization"
DEFAULT_LIMIT = 20
MAX_LIMIT = 50
MAX_PROPOSAL = 200
UNCATEGORISED_LABEL = "Sem categoria"
MIN_TEXT = 2
KINDS: dict[str, View] = {"expenses": "expenses", "income": "income"}

_DATE_FROM = {
    "type": "string",
    "description": "Primeiro dia do período, AAAA-MM-DD. Omita para desde o início.",
}
_DATE_TO = {
    "type": "string",
    "description": "Último dia do período, AAAA-MM-DD, inclusive. Omita para até hoje.",
}
_ACCOUNT = {
    "type": "string",
    "description": "Nome da conta ou do banco (ex.: Nubank). Omita para todas as contas.",
}

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
            "date_from": _DATE_FROM,
            "date_to": _DATE_TO,
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
            "account": _ACCOUNT,
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

SUMMARY_SPEC = ToolSpec(
    name=SPENDING_SUMMARY,
    description=(
        "Resumo de um período como o painel calcula: entradas, gastos e saldo; o gasto de cada "
        "categoria (com contagem); e entradas, gastos e saldo de cada mês que teve lançamento. "
        "Use para 'quanto gastei por categoria', 'em que mais gastei', 'mês a mês' e 'quanto "
        "entrou e saiu'. Valores em centavos e já escritos em reais. Transferência entre contas "
        "próprias, estorno e o que foi marcado como não é gasto já ficam de fora. Gasto tem "
        "valor negativo."
    ),
    parameters={
        "type": "object",
        "properties": {"date_from": _DATE_FROM, "date_to": _DATE_TO, "account": _ACCOUNT},
    },
)

_FILTER_TEXT = {
    "type": "string",
    "description": "Mesmo trecho de texto usado em search_transactions.",
}

PROPOSE_SPEC = ToolSpec(
    name=PROPOSE_RECATEGORIZATION,
    description=(
        "Prepara a troca de categoria de lançamentos para o dono conferir. NÃO muda nada: cria "
        "uma proposta que aparece como cartão abaixo da sua resposta, e só o clique do dono em "
        "Aplicar grava. Escolha os lançamentos repetindo o MESMO filtro da busca anterior "
        "(date_from, date_to, text, category, account, kind), que pega todos os que a busca "
        "contou, ou passe transaction_ids com os ids que a busca devolveu quando o dono escolheu "
        "só alguns. Lançamento que já está na categoria de destino fica de fora. Devolve quantos "
        "mudam e a soma."
    ),
    parameters={
        "type": "object",
        "properties": {
            "target_category": {
                "type": "string",
                "description": "Categoria nova, com o nome exato de uma categoria do painel.",
            },
            "transaction_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Ids de lançamento devolvidos por search_transactions.",
            },
            "date_from": _DATE_FROM,
            "date_to": _DATE_TO,
            "text": _FILTER_TEXT,
            "category": {
                "type": "string",
                "description": "Categoria atual dos lançamentos, como no filtro da busca.",
            },
            "account": _ACCOUNT,
            "kind": {
                "type": "string",
                "enum": list(KINDS),
                "description": "expenses para gastos (padrão), income para entradas.",
            },
        },
        "required": ["target_category"],
    },
)

TOOLS = [SEARCH_SPEC, SUMMARY_SPEC, PROPOSE_SPEC]


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


def _period(arguments: dict[str, Any]) -> tuple[date | None, date | None]:
    date_from = _day(arguments, "date_from")
    date_to = _day(arguments, "date_to")
    if date_from and date_to and date_to < date_from:
        raise ToolInputError("date_to precisa ser igual ou posterior a date_from.")
    return date_from, date_to


def _iso(day: date | None) -> str | None:
    return day.isoformat() if day else None


def _money(prefix: str, cents: int) -> dict[str, Any]:
    return {f"{prefix}_cents": cents, prefix: brl(cents)}


def search_transactions(conn: sqlite3.Connection, arguments: dict[str, Any]) -> dict[str, Any]:
    date_from, date_to = _period(arguments)
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


def spending_summary(conn: sqlite3.Connection, arguments: dict[str, Any]) -> dict[str, Any]:
    date_from, date_to = _period(arguments)
    asked_account = _text(arguments, "account")
    account = resolve_account(conn, asked_account) if asked_account else None
    start, end = _iso(date_from), _iso(date_to)
    account_id = account.key if account else None
    result = period_result(conn, date_from=start, date_to=end, account_id=account_id)
    categories = [
        {"category": row.label, "count": row.count, **_money("total", row.total_cents)}
        for row in sum_by_category(conn, date_from=start, date_to=end, account_id=account_id)
    ]
    months = [
        {
            "month": row.month,
            **_money("income", row.income_cents),
            **_money("spending", row.spending_cents),
            **_money("balance", row.balance_cents),
        }
        for row in monthly_totals(conn, date_from=start, date_to=end, account_id=account_id)
    ]
    return {
        "filters": {
            "date_from": start,
            "date_to": end,
            "account": account.label if account else None,
        },
        **_money("income", result.income_cents),
        **_money("spending", result.spending_cents),
        **_money("balance", result.balance_cents),
        "by_category": categories,
        "months": months,
    }


@dataclass(frozen=True)
class ToolContext:
    conversation_id: int
    now: str


def _ids(arguments: dict[str, Any]) -> list[int] | None:
    value = arguments.get("transaction_ids")
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        raise ToolInputError("transaction_ids precisa ser uma lista de ids.")
    ids: list[int] = []
    for item in value:
        number = int(item) if isinstance(item, float) and item.is_integer() else item
        if not isinstance(number, int) or isinstance(number, bool):
            raise ToolInputError("transaction_ids precisa ter só números inteiros.")
        if number not in ids:
            ids.append(number)
    return ids


def _filtered_ids(conn: sqlite3.Connection, arguments: dict[str, Any]) -> list[int]:
    date_from, date_to = _period(arguments)
    text = _text(arguments, "text")
    asked_category = _text(arguments, "category")
    asked_account = _text(arguments, "account")
    if not any((date_from, date_to, text, asked_category, asked_account)):
        raise ToolInputError(
            "Diga quais lançamentos mudar: transaction_ids ou o mesmo filtro da busca anterior."
        )
    if text is not None and len(text) < MIN_TEXT:
        raise ToolInputError(f"text precisa de pelo menos {MIN_TEXT} letras.")
    kind = _text(arguments, "kind") or "expenses"
    if kind not in KINDS:
        raise ToolInputError("kind precisa ser expenses ou income.")
    category = resolve_category(conn, asked_category) if asked_category else None
    account = resolve_account(conn, asked_account) if asked_account else None
    page = list_expenses(
        conn,
        page=1,
        page_size=MAX_PROPOSAL + 1,
        view=KINDS[kind],
        date_from=_iso(date_from),
        date_to=_iso(date_to),
        account_id=account.key if account else None,
        search=text,
        category=category.key if category else None,
    )
    if page.total == 0:
        raise ToolInputError("Nenhum lançamento corresponde a esse filtro.")
    return [item["id"] for item in page.items]


def _proposal_content(
    proposal: ProposalRow, already_there: int, labels: dict[str, str]
) -> dict[str, Any]:
    total_cents = sum(item.amount_cents for item in proposal.items)
    items = [
        {
            "id": item.transaction_id,
            "date": item.date,
            "description": item.description,
            "from_category": item.previous_label or UNCATEGORISED_LABEL,
            "amount_cents": item.amount_cents,
            "amount": brl(item.amount_cents),
        }
        for item in proposal.items[:MAX_LIMIT]
    ]
    return {
        "proposal_id": proposal.id,
        "status": proposal.status,
        "target_category": labels.get(proposal.target_category, proposal.target_category),
        "count": len(proposal.items),
        "already_in_target": already_there,
        "total_cents": total_cents,
        "total": brl(total_cents),
        "shown": len(items),
        "items": items,
        "next_step": (
            "Nada foi alterado. O dono confere o cartão abaixo da resposta e clica em Aplicar "
            "ou Descartar."
        ),
    }


def propose_recategorization(
    conn: sqlite3.Connection, arguments: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    asked_target = _text(arguments, "target_category")
    if asked_target is None:
        raise ToolInputError("target_category é obrigatório.")
    target = resolve_category(conn, asked_target)
    asked_ids = _ids(arguments)
    ids = asked_ids if asked_ids is not None else _filtered_ids(conn, arguments)
    if len(ids) > MAX_PROPOSAL:
        raise ToolInputError(
            f"São mais de {MAX_PROPOSAL} lançamentos. Restrinja o período ou o filtro."
        )
    snapshots = transaction_snapshots(conn, ids)
    found = {item.id for item in snapshots}
    unknown = [item for item in ids if item not in found]
    if unknown:
        listed = ", ".join(str(item) for item in unknown)
        raise ToolInputError(
            f"Lançamentos que não existem: {listed}. Use os ids devolvidos por search_transactions."
        )
    changing = [item for item in snapshots if item.category != target.key]
    if not changing:
        raise ToolInputError(f"Todos os {len(snapshots)} lançamentos já estão em {target.label}.")
    proposal = propose(conn, context.conversation_id, target.key, changing, context.now)
    return _proposal_content(proposal, len(snapshots) - len(changing), {target.key: target.label})


Handler = Callable[[sqlite3.Connection, dict[str, Any], ToolContext], dict[str, Any]]

_HANDLERS: dict[str, Handler] = {
    SEARCH_TRANSACTIONS: lambda conn, arguments, _: search_transactions(conn, arguments),
    SPENDING_SUMMARY: lambda conn, arguments, _: spending_summary(conn, arguments),
    PROPOSE_RECATEGORIZATION: propose_recategorization,
}


def run_tool(conn: sqlite3.Connection, call: ToolCall, context: ToolContext) -> ToolResult:
    handler = _HANDLERS.get(call.name)
    if handler is None:
        return ToolResult(
            call_id=call.id,
            name=call.name,
            content={"error": f"Ferramenta desconhecida: {call.name}."},
            is_error=True,
        )
    try:
        content = handler(conn, call.input, context)
    except ToolInputError as error:
        failure = {"error": str(error)}
        return ToolResult(call_id=call.id, name=call.name, content=failure, is_error=True)
    return ToolResult(call_id=call.id, name=call.name, content=content)
