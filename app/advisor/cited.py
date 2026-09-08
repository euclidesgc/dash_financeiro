import re

# Limitação: a gramática reconhece só "R$" seguido de valor e número seguido de
# "%" — um inteiro solto como "24" não é acusado. Uma gramática mais larga
# acusaria "2026" e transformaria a guarda em ruído que alguém desliga na
# primeira semana (norma 23).
#
# Motivo do espaço e das casas serem opcionais: a gramática que exigia
# "R$ " e exatamente duas casas não reconhecia "R$987.654,32" nem "R$ 202,4"
# como cifra nenhuma — e o que ela não reconhece, ela deixa passar. A guarda
# falhava aberta justamente nas formas que um modelo varia sozinho.
_MONEY = re.compile(r"R\$\s*\d+(?:\.\d{3})*(?:,\d{1,2})?")
_PERCENT = re.compile(r"\d+(?:,\d+)?\s*%")

CENTS_IN_UNIT = 100


def figures(text: str) -> list[str]:
    return _MONEY.findall(text) + _PERCENT.findall(text)


def _as_cents(figure: str) -> int:
    digits = figure.replace("R$", "").strip().replace(".", "")
    units, _, decimals = digits.partition(",")
    return int(units or 0) * CENTS_IN_UNIT + int((decimals or "0").ljust(2, "0"))


def _canonical(figure: str) -> tuple[str, str]:
    if "%" in figure:
        units, _, decimals = figure.replace("%", "").strip().partition(",")
        return ("%", f"{int(units)}.{decimals.rstrip('0') or '0'}")
    return ("R$", str(_as_cents(figure)))


def uncited(reading: str, context: str) -> list[str]:
    # Decisão: a comparação é pelo número, não pela escrita dele. Uma cifra
    # reescrita — sem o espaço, sem o ponto de milhar, com uma casa decimal em
    # vez de duas — é a mesma cifra, e descartá-la seria recusar leitura
    # correta. Uma cifra que o contexto não contém continua acusada, seja qual
    # for a forma em que o modelo a escreveu.
    seen = {_canonical(figure) for figure in figures(context)}
    return [figure for figure in figures(reading) if _canonical(figure) not in seen]
