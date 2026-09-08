from app.settings.catalog import BASIS_POINTS, CENTS

ACTION = "/configuracao/cartao"

LIMIT = "limite"
RATE = "taxa"
CLOSING = "fechamento"
DUE = "vencimento"
DAY = "dia"

FIELDS = (
    {
        "name": LIMIT,
        "column": "limit_cents",
        "label": "Limite",
        "unit": CENTS,
        "help": "O teto de crédito do cartão, o que o banco informa na fatura.",
    },
    {
        "name": RATE,
        "column": "monthly_rate_bp",
        "label": "Taxa mensal",
        "unit": BASIS_POINTS,
        "help": "A taxa que o cartão cobra sobre o saldo rotativo, ao mês.",
    },
    {
        "name": CLOSING,
        "column": "closing_day",
        "label": "Dia do fechamento",
        "unit": DAY,
        "help": "O dia do mês em que a fatura deste cartão fecha.",
    },
    {
        "name": DUE,
        "column": "due_day",
        "label": "Dia do vencimento",
        "unit": DAY,
        "help": "O dia do mês em que a fatura deste cartão vence.",
    },
)

BY_NAME = {item["name"]: item for item in FIELDS}
