from app.advisor.cited import figures, uncited

CONTEXT = (
    "Custo de continuar como está: R$ 309,10. "
    "Custo da proposta Banco Teste: R$ 202,38. "
    "Diferença: R$ 106,72. Taxa do degrau: 20,0%."
)


def test_a_reading_that_only_copies_the_context_is_not_accused():
    assert uncited("A proposta custa R$ 202,38 contra R$ 309,10.", CONTEXT) == []


def test_a_figure_absent_from_the_context_is_accused():
    assert uncited("Você economiza R$ 987.654,32.", CONTEXT) == ["R$ 987.654,32"]


def test_an_invented_figure_written_without_the_space_is_accused():
    # Reason: the previous grammar did not recognise this form as a figure,
    # and what it did not recognise it let through — the guard failed open.
    assert uncited("Você economiza R$987.654,32.", CONTEXT) == ["R$987.654,32"]


def test_an_invented_figure_written_with_one_decimal_is_accused():
    assert uncited("A proposta custa R$ 202,4.", CONTEXT) == ["R$ 202,4"]


def test_an_invented_figure_written_without_decimals_is_accused():
    assert uncited("A proposta custa R$ 203.", CONTEXT) == ["R$ 203"]


def test_a_context_figure_rewritten_without_the_space_is_not_accused():
    assert uncited("A proposta custa R$202,38.", CONTEXT) == []


def test_a_context_figure_rewritten_without_the_thousands_dot_is_not_accused():
    assert uncited("Economia de R$ 1234,56.", "Economia: R$ 1.234,56.") == []


def test_a_truncated_figure_that_changes_the_number_is_accused():
    assert uncited("Sobram R$ 3.400.", "Sobram R$ 3.400,57.") == ["R$ 3.400"]


def test_an_invented_rate_is_accused_whatever_the_spacing():
    assert uncited("A taxa é de 35 %.", CONTEXT) == ["35 %"]


def test_a_context_rate_written_with_another_decimal_is_not_accused():
    assert uncited("A taxa é de 20%.", CONTEXT) == []


def test_the_grammar_still_ignores_a_bare_integer():
    assert figures("O prazo é de 24 meses, em 2026.") == []
