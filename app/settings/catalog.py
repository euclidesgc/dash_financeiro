from typing import Any

CENTS = "centavos"
BASIS_POINTS = "pontos-base"
MONTHS = "meses"
UNITS = (CENTS, BASIS_POINTS, MONTHS)

FACT = "fato"
GOAL = "meta"
KINDS = (FACT, GOAL)

CARD_RATE = "taxa-cartao"
SETTLEMENT = "quitacao-cdc"
TRANSPORT = "transporte-sem-carro"
RESERVE = "reserva-meses"
MEDIAN = "mediana-meses"
MONTHLY_CEILING = "teto-mensal"

# Reason: these are the defaults the code used as constants before there was
# a place to inform them. They live here because a default and the value
# that replaces it are the same number seen from two sides, and two homes is
# how they drift apart.
RESERVE_MONTHS = 6
MEDIAN_MONTHS = 6

DEBTS_SCREEN = "/dividas"
SIMULATOR_SCREEN = "/simulador"
SETTINGS_SCREEN = "/configuracao"
EXPENSES_SCREEN = "/app/expenses"

# Reason: the owner reads a screen by the name the menu gives it, never by
# its address; a path as link text is a word he has no use for.
SCREEN_LABELS = {
    DEBTS_SCREEN: "Dívidas",
    SIMULATOR_SCREEN: "Simulador",
    SETTINGS_SCREEN: "Configuração",
    EXPENSES_SCREEN: "Gastos do painel novo",
}

# Reason: the order is the order of how much the answer moves the
# projection, and it is the order the advisor asks in — a rate decides where
# the next real goes, and a payoff balance decides a thirty-nine thousand
# real question.
CATALOG = (
    {
        "name": CARD_RATE,
        "label": "Taxa mensal dos cartões",
        "question": "a taxa mensal dos seus cartões",
        "help": (
            "A taxa que o cartão cobra sobre o saldo rotativo. Cada cartão tem a sua, e se "
            "edita tanto aqui, na seção Cartões desta tela, quanto na tela Dívidas, ao lado do "
            "degrau do cartão — as duas escrevem no mesmo lugar."
        ),
        "unit": BASIS_POINTS,
        "kind": FACT,
        "screen": DEBTS_SCREEN,
        "screen_label": SCREEN_LABELS[DEBTS_SCREEN],
        "moves": "a ordem da escada de dívida, e com ela onde o próximo real rende mais",
        "default": None,
        # Reason: one rate per debt, in debts.monthly_rate_bp — it is not a
        # name → value line, and copying it into the store would create a
        # second answer to the same question (RF-08).
        "stored": False,
    },
    {
        "name": SETTLEMENT,
        "label": "Saldo de quitação do CDC do carro",
        "question": "o saldo de quitação antecipada do CDC do carro",
        "help": (
            "Quanto o banco cobra hoje para encerrar o CDC antes do prazo. Só o banco informa, "
            "e o número envelhece: vale a pena registrar até quando ele vale."
        ),
        "unit": CENTS,
        "kind": FACT,
        "screen": SIMULATOR_SCREEN,
        "screen_label": SCREEN_LABELS[SIMULATOR_SCREEN],
        "moves": "a conta de vender o carro, que é a maior decisão em aberto",
        "default": None,
        "stored": True,
    },
    {
        "name": TRANSPORT,
        "label": "Custo de transporte sem o carro",
        "question": "quanto custaria seu transporte por mês sem o carro",
        "help": (
            "O que você gastaria por mês em transporte se vendesse o carro. Sem esse número a "
            "venda aparece como economia bruta, e não como o que sobra de verdade."
        ),
        "unit": CENTS,
        "kind": FACT,
        "screen": SIMULATOR_SCREEN,
        "screen_label": SCREEN_LABELS[SIMULATOR_SCREEN],
        "moves": "o fluxo líquido que a venda do carro libera",
        "default": None,
        "stored": True,
    },
    {
        "name": RESERVE,
        "label": "Meses de reserva do objetivo",
        "question": "quantos meses de sobrevivência a sua reserva precisa cobrir",
        "help": (
            "Quantos meses de piso de sobrevivência a reserva alvo precisa cobrir. É escolha "
            "sua: seis meses é a premissa do painel enquanto você não decidir outra."
        ),
        "unit": MONTHS,
        "kind": GOAL,
        "screen": SETTINGS_SCREEN,
        "screen_label": SCREEN_LABELS[SETTINGS_SCREEN],
        "moves": "a reserva alvo do objetivo, e com ela o tempo até alcançá-lo",
        "default": RESERVE_MONTHS,
        "stored": True,
    },
    {
        "name": MEDIAN,
        "label": "Meses da janela da mediana",
        "question": "quantos meses fechados representam o seu mês típico",
        "help": (
            "Quantos meses fechados entram na mediana que define o mês típico. Uma janela mais "
            "longa é mais estável; uma mais curta acompanha uma mudança recente mais depressa."
        ),
        "unit": MONTHS,
        "kind": GOAL,
        "screen": SETTINGS_SCREEN,
        "screen_label": SCREEN_LABELS[SETTINGS_SCREEN],
        "moves": (
            "o mês típico da projeção, e com ele o piso de sobrevivência e a reserva alvo — "
            "os dois não são independentes"
        ),
        "default": MEDIAN_MONTHS,
        "stored": True,
    },
    {
        "name": MONTHLY_CEILING,
        "label": "Teto mensal de gasto",
        "question": "quanto, no máximo, você quer gastar por mês",
        "help": (
            "O total de gasto que um mês fechado pode alcançar para o plano de recuperação "
            "seguir de pé. Nasce vazio: os números do plano definem déficit e renda, não um "
            "teto de gasto, e só você decide esse valor."
        ),
        "unit": CENTS,
        "kind": GOAL,
        "screen": EXPENSES_SCREEN,
        "screen_label": SCREEN_LABELS[EXPENSES_SCREEN],
        "moves": "o sinal do mês na página de gastos",
        "default": None,
        "stored": True,
    },
)

BY_NAME = {item["name"]: item for item in CATALOG}


def entry(name: str) -> dict[str, Any] | None:
    return BY_NAME.get(name)


def of_kind(kind: str) -> tuple[dict[str, Any], ...]:
    return tuple(item for item in CATALOG if item["kind"] == kind)
