import sqlite3
from calendar import monthrange
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.advisor.proposals import propose
from app.advisor.provider import ToolCall, ToolResult, ToolSpec
from app.db import fold
from app.debts.payoff import (
    BALANCE,
    CARD_INSTALLMENT,
    INFORMED,
    NOMINAL,
    Debt,
    InvalidBudgetError,
    InvalidSavingError,
    LiquidityRow,
    PastTargetError,
    Payoff,
    SavingPlan,
    list_debts,
    payoff_at,
    rank_by_liquidity,
    saving_plan,
    unnumbered,
)
from app.formatting import brl
from app.projection.schedule import (
    CARD_INSTALLMENT as SCHEDULE_CARD_INSTALLMENT,
)
from app.projection.schedule import (
    DEFAULT_MONTHS,
    FINANCING,
    MAX_MONTHS,
    RECURRING_FIXED,
    ScheduleLine,
    schedule_by_month,
)
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
from app.queries.period import shift

SEARCH_TRANSACTIONS = "search_transactions"
SPENDING_SUMMARY = "spending_summary"
PROPOSE_RECATEGORIZATION = "propose_recategorization"
COMMITMENTS_BY_MONTH = "commitments_by_month"
DEBT_PAYOFF = "debt_payoff"
DEBTS_BY_LIQUIDITY = "debts_by_liquidity"
MAX_TARGET_MONTHS = 360
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

COMMITMENTS_SPEC = ToolSpec(
    name=COMMITMENTS_BY_MONTH,
    description=(
        "Projeção do que já está contratado para sair em cada um dos próximos meses, a partir do "
        "mês seguinte a hoje: parcelas de compras parceladas (cartão e crediário), parcelas de "
        "financiamento pelo contrato cadastrado e contas recorrentes e assinaturas vivas. "
        "Devolve por mês o total de cada origem, o total do mês e o que termina naquele mês; e "
        "cada linha com descrição, conta, valor da parcela, parcela k/n no primeiro e no último "
        "mês da janela e o mês da última parcela. Não inclui o gasto do dia a dia (mercado, "
        "delivery). Valores em centavos e já escritos em reais; saída tem valor negativo."
    ),
    parameters={
        "type": "object",
        "properties": {
            "months": {
                "type": "integer",
                "description": (
                    f"Quantos meses à frente, de 1 a {MAX_MONTHS}. Padrão {DEFAULT_MONTHS}."
                ),
            },
        },
    },
)

DEBT_PAYOFF_SPEC = ToolSpec(
    name=DEBT_PAYOFF,
    description=(
        "Quanto custa quitar uma dívida e quanto juntar para isso. Sem 'debt', lista as dívidas "
        "do painel (cheque especial, saldo de cartão, financiamentos e compras parceladas com "
        "parcelas a vencer), cada uma com a chave, o valor para quitar hoje e a soma das "
        "parcelas que faltam. Com 'debt', devolve o valor para quitar hoje e, se vier "
        "'target_date' ou 'months', o valor na data e quanto guardar por mês até lá; se vier "
        "'monthly_saving_cents', o mês em que o dinheiro guardado alcança o valor para quitar. "
        "Considera que as parcelas continuam sendo pagas até a quitação. Quando o saldo de "
        "quitação não foi informado, o valor para quitar vem nulo e o alvo é a soma das "
        "parcelas que faltam, sem desconto. Valores em centavos e já escritos em reais, "
        "positivos: é quanto juntar."
    ),
    parameters={
        "type": "object",
        "properties": {
            "debt": {
                "type": "string",
                "description": (
                    "Chave da dívida devolvida pela lista (ex.: debt-7, installment-12) ou "
                    "parte do nome. Omita para listar as dívidas."
                ),
            },
            "target_date": {
                "type": "string",
                "description": "Data em que quer quitar, AAAA-MM-DD, de hoje em diante.",
            },
            "months": {
                "type": "integer",
                "description": (
                    f"Em quantos meses quer quitar, de 1 a {MAX_TARGET_MONTHS}, no lugar de "
                    "target_date."
                ),
            },
            "monthly_saving_cents": {
                "type": "integer",
                "description": (
                    "Quanto consegue guardar por mês, em centavos (150000 é R$ 1.500,00), para "
                    "saber quando alcança o valor."
                ),
            },
        },
    },
)

LIQUIDITY_SPEC = ToolSpec(
    name=DEBTS_BY_LIQUIDITY,
    description=(
        "Quais dívidas e compras parceladas quitar primeiro para liberar dinheiro no mês: a "
        "lista ordenada pela parcela que deixa de sair por mês a cada real pago na quitação "
        "(parcela ÷ valor para quitar hoje), com o valor para quitar, a parcela liberada, "
        "quantos meses ela ainda sairia e o mês da última. Quando o saldo de quitação não foi "
        "informado, o valor é a soma das parcelas que faltam, marcado como estimativa pelo teto. "
        "Cheque especial, saldo de cartão e financiamento sem parcela cadastrada vêm à parte: "
        "quitá-los reduz juros, não libera parcela. Com 'available_cents', escolhe na ordem da "
        "lista, pulando o que não cabe, o que quitar com esse valor, e devolve o total gasto, a "
        "sobra e a parcela liberada por mês. Valores em centavos e já escritos em reais, "
        "positivos."
    ),
    parameters={
        "type": "object",
        "properties": {
            "available_cents": {
                "type": "integer",
                "description": (
                    "Quanto tem disponível agora para quitar, em centavos (500000 é R$ 5.000,00)."
                ),
            },
            "limit": {
                "type": "integer",
                "description": (
                    f"Quantas dívidas da lista devolver, de 1 a {MAX_LIMIT}. Padrão "
                    f"{DEFAULT_LIMIT}. A escolha com available_cents considera todas."
                ),
            },
        },
    },
)

TOOLS = [
    SEARCH_SPEC,
    SUMMARY_SPEC,
    PROPOSE_SPEC,
    COMMITMENTS_SPEC,
    DEBT_PAYOFF_SPEC,
    LIQUIDITY_SPEC,
]

SOURCE_LABELS = {
    SCHEDULE_CARD_INSTALLMENT: "Compras parceladas",
    FINANCING: "Financiamentos",
    RECURRING_FIXED: "Contas recorrentes e assinaturas",
}


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
    today: date


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


def _months(arguments: dict[str, Any]) -> int:
    value = arguments.get("months", DEFAULT_MONTHS)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_MONTHS:
        raise ToolInputError(f"months precisa ser um número inteiro de 1 a {MAX_MONTHS}.")
    return value


def _installment(number: int | None, total: int | None) -> str | None:
    return f"{number}/{total}" if number is not None and total is not None else None


def _schedule_line(line: ScheduleLine) -> dict[str, Any]:
    return {
        "source": SOURCE_LABELS[line.source],
        "description": line.description,
        "account": line.account,
        **_money("amount", line.amount_cents),
        "first_month": line.first_month,
        "last_month": line.last_month,
        "months_in_window": line.months_in_window,
        **_money("window_total", line.window_total_cents),
        "first_installment": _installment(line.first_installment, line.installment_total),
        "last_installment_in_window": _installment(line.last_installment, line.installment_total),
        "end_month": line.end_month,
        "replaces_fixed_bill": line.replaces,
    }


def commitments_by_month(
    conn: sqlite3.Connection, arguments: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    schedule = schedule_by_month(conn, today=context.today, months=_months(arguments))
    return {
        "months": [
            {
                "month": row.month,
                "by_source": {
                    SOURCE_LABELS[source]: brl(cents) for source, cents in row.by_source.items()
                },
                "by_source_cents": {
                    SOURCE_LABELS[source]: cents for source, cents in row.by_source.items()
                },
                **_money("total", row.total_cents),
                "ending": row.ending,
            }
            for row in schedule.months
        ],
        **_money("window_total", schedule.total_cents),
        "lines": [_schedule_line(line) for line in schedule.lines],
        "not_projected": [
            {
                "source": SOURCE_LABELS[item.source],
                "description": item.description,
                "reason": item.reason,
            }
            for item in schedule.unprojected
        ],
        "notes": (
            "Parcela de cartão vem da última parcela vista na fatura; financiamento vem do "
            "contrato da tela Configuração; conta recorrente é a média da série e vale para todos "
            "os meses. O gasto do dia a dia não entra."
        ),
    }


DEBT_KIND_LABELS = {
    "overdraft": "Cheque especial",
    "card": "Saldo do cartão de crédito",
    "vehicle": "Financiamento de veículo",
    "mortgage": "Financiamento imobiliário",
    CARD_INSTALLMENT: "Compra parcelada",
}
_BALANCE_BASIS = {
    "overdraft": "saldo negativo da conta, informado pelo banco",
    "card": "saldo do cartão, informado pelo banco",
    "mortgage": "saldo devedor cadastrado na tela Configuração",
}
BASIS_LABELS = {
    INFORMED: "saldo de quitação que você informou",
    NOMINAL: "soma das parcelas que faltam, sem desconto",
}
MISSING_SETTLEMENT = (
    "Saldo de quitação não informado: o valor real para quitar só o banco informa. Registre-o "
    "na tela Dívidas (Saldo de quitação) para o consultor usar. Até lá, a soma das parcelas que "
    "faltam é o teto."
)
_BALANCE_AHEAD = (
    "O painel não sabe como esse saldo muda até a data: o valor usado é o de hoje. Confira com "
    "o banco perto da data."
)


def _basis(debt: Debt, payoff: Payoff) -> str:
    if payoff.basis == BALANCE:
        return _BALANCE_BASIS.get(debt.kind, "saldo informado")
    return BASIS_LABELS[payoff.basis]


def _payoff_content(debt: Debt, payoff: Payoff, *, today: date) -> dict[str, Any]:
    content: dict[str, Any] = {
        "date": payoff.day.isoformat(),
        "payoff_cents": payoff.payoff_cents,
        "payoff": brl(payoff.payoff_cents) if payoff.payoff_cents is not None else None,
        **_money("target", payoff.target_cents),
        "basis": _basis(debt, payoff),
    }
    if payoff.nominal_cents is not None:
        content.update(_money("remaining_installments_sum", payoff.nominal_cents))
    if payoff.installments_left is not None:
        content["installments_left"] = payoff.installments_left
    if payoff.end_month is not None:
        content["last_installment_month"] = payoff.end_month
    if payoff.missing_settlement:
        content["missing"] = MISSING_SETTLEMENT
    if payoff.basis == BALANCE and payoff.day.strftime("%Y-%m") != today.strftime("%Y-%m"):
        content["note"] = _BALANCE_AHEAD
    return content


def _debt_header(debt: Debt) -> dict[str, Any]:
    header: dict[str, Any] = {
        "key": debt.key,
        "kind": DEBT_KIND_LABELS[debt.kind],
        "name": debt.name,
    }
    if debt.account:
        header["account"] = debt.account
    if debt.payment_cents is not None:
        header.update(_money("installment", abs(debt.payment_cents)))
    return header


def resolve_debt(debts: list[Debt], asked: str) -> Debt:
    wanted = fold(asked) or ""
    exact = [debt for debt in debts if debt.key == asked.strip()]
    if exact:
        return exact[0]
    found = [debt for debt in debts if wanted and wanted in (fold(debt.name) or "")]
    if len(found) == 1:
        return found[0]
    listed = "; ".join(f"{debt.key} ({debt.name})" for debt in (found or debts))
    if not found:
        raise ToolInputError(f"Dívida '{asked}' não encontrada. Dívidas do painel: {listed}.")
    raise ToolInputError(f"'{asked}' corresponde a mais de uma dívida: {listed}. Use a chave.")


def _saving_input(arguments: dict[str, Any]) -> int | None:
    value = arguments.get("monthly_saving_cents")
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ToolInputError("monthly_saving_cents precisa ser um número inteiro de centavos.")
    return value


def _target_input(arguments: dict[str, Any], today: date) -> date | None:
    target = _day(arguments, "target_date")
    months = arguments.get("months")
    if months is None:
        return target
    if target is not None:
        raise ToolInputError("Passe target_date ou months, não os dois.")
    if isinstance(months, float) and months.is_integer():
        months = int(months)
    if (
        not isinstance(months, int)
        or isinstance(months, bool)
        or not 1 <= months <= MAX_TARGET_MONTHS
    ):
        raise ToolInputError(f"months precisa ser um número inteiro de 1 a {MAX_TARGET_MONTHS}.")
    first = shift(today, months)
    return date(first.year, first.month, min(today.day, monthrange(first.year, first.month)[1]))


def _plan_content(plan: SavingPlan, debt: Debt, *, today: date) -> dict[str, Any]:
    content: dict[str, Any] = {
        "months": plan.months,
        **_money("monthly_saving", plan.monthly_cents),
        "reached_month": plan.reached_month,
        "payoff_then": _payoff_content(debt, plan.payoff, today=today),
    }
    if plan.months is not None:
        content.update(_money("saved_total", plan.monthly_cents * plan.months))
    if debt.first_due is not None:
        content["assumption"] = (
            "As parcelas continuam sendo pagas até a quitação; o valor guardado é à parte delas."
        )
    if plan.months == 0 and plan.payoff.target_cents:
        content["note"] = "A data cai neste mês: é preciso ter o valor inteiro agora."
    elif plan.payoff.target_cents == 0:
        content["note"] = "As parcelas terminam até essa data: não há o que juntar."
    elif plan.reached_month is None:
        content["note"] = "Com esse valor por mês, o dinheiro guardado não alcança a dívida."
    return content


def debt_payoff(
    conn: sqlite3.Connection, arguments: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    today = context.today
    debts = list_debts(conn, today=today)
    asked = _text(arguments, "debt")
    target = _target_input(arguments, today)
    saving = _saving_input(arguments)
    if asked is None:
        if target is not None or saving is not None:
            raise ToolInputError("Diga qual dívida: passe debt com a chave devolvida pela lista.")
        return {
            "today": today.isoformat(),
            "debts": [
                {
                    **_debt_header(debt),
                    "payoff_today": _payoff_content(
                        debt, payoff_at(debt, today, today=today), today=today
                    ),
                }
                for debt in debts
            ],
            "not_listed": [
                {"description": item, "reason": "o lançamento não diz qual parcela é"}
                for item in unnumbered(conn, today=today)
            ],
            "notes": (
                "O saldo do cartão é o que o banco informa hoje e pode já incluir as compras "
                "parceladas listadas em separado: não some os dois. Compra parcelada se quita "
                "pelo valor nominal; o desconto de antecipação só o emissor informa."
            ),
        }
    if target is not None and saving is not None:
        raise ToolInputError("Passe a data (target_date ou months) ou monthly_saving_cents.")
    debt = resolve_debt(debts, asked)
    content: dict[str, Any] = {
        **_debt_header(debt),
        "today": today.isoformat(),
        "payoff_today": _payoff_content(debt, payoff_at(debt, today, today=today), today=today),
    }
    if target is None and saving is None:
        return content
    try:
        plan = saving_plan(debt, today=today, target_date=target, monthly_saving_cents=saving)
    except (PastTargetError, InvalidSavingError) as refusal:
        raise ToolInputError(str(refusal)) from None
    content["saving_plan"] = _plan_content(plan, debt, today=today)
    return content


CEILING_MARK = "estimativa pelo teto — informe o saldo de quitação"
_NOT_RANKED_REASON = {
    "overdraft": "não tem parcela: quitar reduz os juros do cheque especial",
    "card": (
        "não tem parcela, e o saldo pode já incluir as compras parceladas da lista: não "
        "some os dois"
    ),
    "mortgage": "o contrato não tem valor de parcela cadastrado na tela Configuração",
}


def _percent(bp: int) -> str:
    return f"{bp // 100},{bp % 100:02d}%"


def _available_input(arguments: dict[str, Any]) -> int | None:
    value = arguments.get("available_cents")
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ToolInputError("available_cents precisa ser um número inteiro de centavos.")
    return value


def _liquidity_line(position: int, row: LiquidityRow) -> dict[str, Any]:
    line: dict[str, Any] = {
        "position": position,
        **_debt_header(row.debt),
        **_money("payoff", row.payoff.target_cents),
        "basis": _basis(row.debt, row.payoff),
        **_money("monthly_freed", row.monthly_freed_cents),
        "monthly_freed_per_real_paid": _percent(row.freed_bp),
        "installments_left": row.payoff.installments_left,
        "last_installment_month": row.payoff.end_month,
    }
    if row.ceiling:
        line["estimate"] = CEILING_MARK
    return line


def debts_by_liquidity(
    conn: sqlite3.Connection, arguments: dict[str, Any], context: ToolContext
) -> dict[str, Any]:
    today = context.today
    limit = _limit(arguments)
    try:
        ranking = rank_by_liquidity(
            list_debts(conn, today=today), today=today, budget_cents=_available_input(arguments)
        )
    except InvalidBudgetError as refusal:
        raise ToolInputError(str(refusal)) from None
    lines = [_liquidity_line(index, row) for index, row in enumerate(ranking.ranked, start=1)]
    content: dict[str, Any] = {
        "today": today.isoformat(),
        "ranked_total": len(lines),
        "ranked": lines[:limit],
        "not_ranked": [
            {
                **_debt_header(item.debt),
                **_money("payoff", item.payoff.target_cents),
                "reason": _NOT_RANKED_REASON.get(item.debt.kind, "não tem parcela a vencer"),
            }
            for item in ranking.unranked
        ],
        "not_listed": [
            {"description": item, "reason": "o lançamento não diz qual parcela é"}
            for item in unnumbered(conn, today=today)
        ],
        "notes": (
            "A parcela liberada deixa de sair a partir do mês seguinte à quitação, até o mês da "
            "última. Compra parcelada se quita pelo valor nominal; o desconto de antecipação só "
            "o emissor informa, então a razão dela é 1 ÷ parcelas que faltam e quem está no fim "
            "sobe na lista, liberando a parcela só pelos meses que faltavam. Nenhum desconto de "
            "juros é estimado."
        ),
    }
    selection = ranking.selection
    if selection is not None:
        chosen = {row.debt.key for row in selection.chosen}
        content["with_available"] = {
            **_money("available", selection.budget_cents),
            "pay_off": [line for line in lines if line["key"] in chosen],
            **_money("spent", selection.spent_cents),
            **_money("left", selection.left_cents),
            **_money("monthly_freed_total", selection.monthly_freed_cents),
        }
        if not selection.chosen:
            content["with_available"]["note"] = "O valor não quita nenhuma dívida da lista inteira."
        if selection.ceiling:
            content["with_available"]["estimate"] = (
                "Algum valor escolhido é a soma das parcelas que faltam: com o saldo de "
                "quitação do banco, pode sobrar mais."
            )
    return content


Handler = Callable[[sqlite3.Connection, dict[str, Any], ToolContext], dict[str, Any]]

_HANDLERS: dict[str, Handler] = {
    SEARCH_TRANSACTIONS: lambda conn, arguments, _: search_transactions(conn, arguments),
    SPENDING_SUMMARY: lambda conn, arguments, _: spending_summary(conn, arguments),
    PROPOSE_RECATEGORIZATION: propose_recategorization,
    COMMITMENTS_BY_MONTH: commitments_by_month,
    DEBT_PAYOFF: debt_payoff,
    DEBTS_BY_LIQUIDITY: debts_by_liquidity,
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
