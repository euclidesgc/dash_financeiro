from app.financings.money import RATE_SCALE


class InvalidCostInputError(ValueError):
    pass


def total_cost(
    released_cents: int,
    monthly_rate_bp: int,
    term_months: int,
    fee_cents: int = 0,
) -> int:
    # Invariante: sem rota na frente para barrar antes — a comparação da fase
    # 2 chama esta função direto —, prazo zero divide por zero e taxa negativa
    # devolve custo negativo. A rota de proposta já recusa os dois; esta função
    # precisa recusar sozinha também.
    if term_months <= 0:
        raise InvalidCostInputError("Prazo precisa ser maior que zero.")
    if monthly_rate_bp < 0:
        raise InvalidCostInputError("Taxa mensal não pode ser negativa.")
    if monthly_rate_bp == 0:
        return fee_cents
    rate = monthly_rate_bp / RATE_SCALE
    payment = round(released_cents * rate / (1 - (1 + rate) ** -term_months))
    return payment * term_months - released_cents + fee_cents
