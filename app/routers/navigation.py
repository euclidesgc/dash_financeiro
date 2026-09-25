from typing import Any

from app.routers import (
    advisor,
    commitments,
    debts,
    plan,
    rules,
    settings,
    spending,
    summary,
    whatif,
)

LOGOUT = "/logout"

# Reason: the destination comes from the router that owns it, so a screen
# that moves takes its menu entry along instead of leaving a link that
# answers 404.
SCREENS: tuple[dict[str, str], ...] = (
    {"href": summary.SCREEN, "label": "Resumo"},
    {"href": spending.SCREEN, "label": "Gastos"},
    {"href": commitments.SCREEN, "label": "Comprometido"},
    {"href": debts.SCREEN, "label": "Dívidas"},
    {"href": plan.SCREEN, "label": "Objetivo"},
    {"href": whatif.SCREEN, "label": "Simulador"},
    {"href": advisor.SCREEN, "label": "Consultor"},
    {"href": rules.SCREEN, "label": "Regras"},
    {"href": settings.SCREEN, "label": "Configuração"},
)


# Reason: the new panel is a separate client app mounted under /app; these are
# full page loads into it, kept beside the old rail until the migration ends.
SPA_SCREENS: tuple[dict[str, str], ...] = (
    {"href": "/app/", "label": "Saldos"},
    {"href": "/app/expenses", "label": "Gastos"},
    {"href": "/app/categories", "label": "Categorias"},
    {"href": "/app/connections", "label": "Conexões"},
)


def current(path: str, href: str) -> bool:
    # Reason: a screen keeps the mark while the reader is inside it —
    # /regras/7/editar is still Regras. The root would swallow every path
    # under the prefix rule, so it matches whole.
    if href == "/":
        return path == "/"
    return path == href or path.startswith(f"{href}/")


def marked(path: str) -> tuple[dict[str, Any], ...]:
    return tuple({**screen, "current": current(path, screen["href"])} for screen in SCREENS)
