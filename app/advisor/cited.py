import re

# Limitação: a gramática reconhece só "R$" seguido de valor e número seguido de
# "%" — um inteiro solto como "24" não é acusado. Uma gramática mais larga
# acusaria "2026" e transformaria a guarda em ruído que alguém desliga na
# primeira semana (norma 23).
_MONEY = re.compile(r"R\$ [\d.]+,\d{2}")
_PERCENT = re.compile(r"\d+(?:,\d+)?%")


def figures(text: str) -> list[str]:
    return _MONEY.findall(text) + _PERCENT.findall(text)


def uncited(reading: str, context: str) -> list[str]:
    # Decisão: comparação literal, sem normalizar — "R$ 3.400" onde o contexto
    # traz "R$ 3.400,00" é citação truncada, não a mesma cifra.
    return [figure for figure in figures(reading) if figure not in context]
