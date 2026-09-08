from datetime import date

import pytest

from app.financings import MORTGAGE, VEHICLE
from app.financings.typed import read_form as financing_read_form
from app.offers.typed import read_form as offer_read_form
from app.payees import names
from app.plan.whatif import INCOME, Move, save
from app.settings.limits import (
    NAME_MAX,
    PAYEE_ALIAS_MAX,
    RULE_EXPRESSION_MAX,
    SCENARIO_NAME_MAX,
)
from app.settings.typed import InvalidValueError, parse_money, parse_months, parse_rate
from app.taxonomy import classify
from app.taxonomy.rules import InvalidExpressionError, create_rule
from app.taxonomy.seed import seed_taxonomy
from tests.conftest import narrowed

TODAY = date(2026, 9, 8)

OFFER_BASE = {"prazo": "12", "liberado": "1.000,00", "contratacao": "0"}
MORTGAGE_FORM = {"taxa": "100", "prazo": "360", "saldo": "300.000,00"}
VEHICLE_FORM = {
    "taxa": "100",
    "prazo": "48",
    "parcela": "1.500,00",
    "vencimento": "2026-10-05",
}


@pytest.fixture
def rule_conn(taxonomy_conn, seed):
    seed_taxonomy(taxonomy_conn, narrowed(seed, []))
    return taxonomy_conn


def _rule_terms(seed):
    return {
        "group_id": _group_id(seed),
        "nature": seed["natures"][0],
        "essentiality": seed["essentialities"][0],
    }


def _group_id(seed):
    return seed["groups"][0]["name"]


def _group_row_id(conn, name):
    return conn.execute("SELECT id FROM category_groups WHERE name = ?", (name,)).fetchone()[0]


def test_a_arabic_indic_digito_is_refused_by_parse_money():
    with pytest.raises(InvalidValueError):
        parse_money("١٢٣")


def test_a_fullwidth_digito_is_refused_by_parse_money():
    with pytest.raises(InvalidValueError):
        parse_money("１２３")


def test_ascii_digito_keeps_returning_the_same_cents():
    assert parse_money("123") == 12300


def test_a_financiamento_imobiliario_refuses_the_generic_hundred_percent_rate():
    with pytest.raises(InvalidValueError):
        financing_read_form(MORTGAGE, MORTGAGE_FORM)


def test_the_generic_reader_still_accepts_the_rate_a_financiamento_refuses():
    assert parse_rate("100", "Taxa mensal") == 10000


def test_a_financiamento_de_veiculo_has_a_ceiling_of_its_own():
    tight_for_a_mortgage = {**MORTGAGE_FORM, "taxa": "30"}
    with pytest.raises(InvalidValueError):
        financing_read_form(MORTGAGE, tight_for_a_mortgage)

    roomy_for_a_vehicle = {**VEHICLE_FORM, "taxa": "30"}
    accepted = financing_read_form(VEHICLE, roomy_for_a_vehicle)
    assert accepted["monthly_rate_bp"] == 3000

    with pytest.raises(InvalidValueError):
        financing_read_form(VEHICLE, {**VEHICLE_FORM, "taxa": "45"})


def test_a_nome_with_a_replacement_character_is_refused():
    with pytest.raises(InvalidValueError):
        offer_read_form({**OFFER_BASE, "nome": "Consigna��o"}, today=TODAY)


def test_a_nome_with_a_control_character_is_refused():
    with pytest.raises(InvalidValueError):
        offer_read_form({**OFFER_BASE, "nome": "Consig\x00nacao"}, today=TODAY)


def test_a_nome_with_accent_and_cedilla_is_still_accepted():
    accepted = offer_read_form({**OFFER_BASE, "nome": "Consignação Itaú"}, today=TODAY)
    assert accepted["name"] == "Consignação Itaú"


def test_teto_of_apelido_de_beneficiario_rejects_one_over_and_accepts_at_the_limit(taxonomy_conn):
    at_limit = "a" * PAYEE_ALIAS_MAX
    over_limit = "a" * (PAYEE_ALIAS_MAX + 1)
    names.name_it(taxonomy_conn, "payee-x", at_limit, names.OWNER)
    with pytest.raises(InvalidValueError):
        names.name_it(taxonomy_conn, "payee-x", over_limit, names.OWNER)


def test_teto_of_nome_de_cenario_rejects_one_over_and_accepts_at_the_limit(taxonomy_conn):
    move = Move(kind=INCOME, monthly_cents=100000, once_cents=0, months=None)
    at_limit = "a" * SCENARIO_NAME_MAX
    over_limit = "a" * (SCENARIO_NAME_MAX + 1)
    save(taxonomy_conn, at_limit, move)
    with pytest.raises(InvalidValueError):
        save(taxonomy_conn, over_limit, move)


def test_teto_of_expressao_de_regra_rejects_one_over_and_accepts_at_the_limit(rule_conn, seed):
    terms = _rule_terms(seed)
    group_id = _group_row_id(rule_conn, terms["group_id"])
    at_limit = "a" * RULE_EXPRESSION_MAX
    over_limit = "a" * (RULE_EXPRESSION_MAX + 1)
    create_rule(
        rule_conn,
        match_kind=classify.MATCH_DESCRIPTION,
        match_value=at_limit,
        group_id=group_id,
        nature=terms["nature"],
        essentiality=terms["essentiality"],
    )
    with pytest.raises(InvalidExpressionError):
        create_rule(
            rule_conn,
            match_kind=classify.MATCH_DESCRIPTION,
            match_value=over_limit,
            group_id=group_id,
            nature=terms["nature"],
            essentiality=terms["essentiality"],
        )


def test_teto_of_nome_de_proposta_rejects_one_over_and_accepts_at_the_limit():
    at_limit = "a" * NAME_MAX
    over_limit = "a" * (NAME_MAX + 1)
    accepted = offer_read_form({**OFFER_BASE, "nome": at_limit}, today=TODAY)
    assert accepted["name"] == at_limit
    with pytest.raises(InvalidValueError):
        offer_read_form({**OFFER_BASE, "nome": over_limit}, today=TODAY)


def test_a_term_of_420_months_is_still_accepted():
    assert parse_months("420", "Prazo") == 420


def test_a_twelve_digit_amount_is_still_accepted():
    assert parse_money("999.999.999,99") == 99999999999
