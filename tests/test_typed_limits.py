import re
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.debts.ladder import rebuild
from app.financings import MORTGAGE, VEHICLE
from app.financings.typed import read_form as financing_read_form
from app.ingest.loader import ingest
from app.main import create_app
from app.offers import store as offers_store
from app.offers.typed import read_form as offer_read_form
from app.payees import names
from app.plan.whatif import INCOME, Move, save
from app.settings import limits
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
from tests.conftest import narrowed, transaction

TODAY = date(2026, 9, 8)

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
REFERENCE = date(2026, 9, 5)

# Motivo: a coerência dos campos (RF-03) precisa de uma dívida sem taxa (para
# o campo de /dividas), um cartão (para a seção de cartões), um financiamento
# de cada tipo (para a seção de financiamentos e para a escada com taxa) e
# uma proposta (para a seção de propostas) — a mesma base que qualquer tela
# real teria, só que pequena.
OVERDRAFT_ACCOUNT = {
    "id": "acc-cheque-especial",
    "type": "BANK",
    "subtype": "CHECKING_ACCOUNT",
    "name": "Conta corrente",
    "balance": -500.0,
}
CREDIT_ACCOUNT = {
    "id": "acc-cartao-coerencia",
    "type": "CREDIT",
    "subtype": "CREDIT_CARD",
    "name": "Cartão de teste",
    "balance": -200.0,
}
MORTGAGE_ROW = {
    "kind": "mortgage",
    "monthly_rate_bp": 72,
    "term_months": 370,
    "balance_cents": -23858518,
    "payment_cents": None,
    "first_due_date": None,
}
VEHICLE_ROW = {
    "kind": "vehicle",
    "monthly_rate_bp": 163,
    "term_months": 60,
    "balance_cents": None,
    "payment_cents": -123533,
    "first_due_date": "2025-06-11",
}
NEW_OFFER = {
    "nome": "Banco Teste",
    "taxa": "1,99",
    "prazo": "24",
    "liberado": "10.000,00",
    "contratacao": "0",
}


def _insert_financing(conn, row):
    conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES (:kind, :monthly_rate_bp, :term_months, :balance_cents, :payment_cents, :first_due_date)",
        row,
    )
    conn.commit()


@pytest.fixture
def campos_client(tmp_path, monkeypatch, seed):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", REFERENCE.isoformat())
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    result = ingest(
        conn,
        transactions=[
            transaction(
                "txn-coerencia",
                "2026-09-01",
                -150.0,
                conta_id=OVERDRAFT_ACCOUNT["id"],
                descricao="Mercado da Esquina",
                categoria="Categoria da fonte",
            )
        ],
        accounts=[OVERDRAFT_ACCOUNT, CREDIT_ACCOUNT],
        source="tests",
    )
    assert result.status == "ok", result.message
    seed_taxonomy(conn, narrowed(seed, []))
    classify.classify_all(conn)
    conn.commit()
    _insert_financing(conn, MORTGAGE_ROW)
    _insert_financing(conn, VEHICLE_ROW)
    rebuild(conn, today=REFERENCE)
    offers_store.write(conn, NEW_OFFER, today=REFERENCE)
    target = conn.execute(
        "SELECT id FROM transactions WHERE pluggy_id = 'txn-coerencia'"
    ).fetchone()[0]
    conn.close()
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield client, target


def _input_tag(html: str, field_id: str) -> str:
    match = re.search(rf'<input\b[^>]*\bid="{re.escape(field_id)}"[^>]*>', html, re.S)
    assert match is not None, f"campo {field_id} não encontrado na página"
    return match.group(0)


def _maxlength_of(html: str, field_id: str) -> int:
    tag = _input_tag(html, field_id)
    found = re.search(r'maxlength="(\d+)"', tag)
    assert found is not None, f"{field_id} está sem maxlength"
    return int(found.group(1))


def _inputmode_of(html: str, field_id: str) -> str | None:
    tag = _input_tag(html, field_id)
    found = re.search(r'inputmode="([^"]*)"', tag)
    return found.group(1) if found else None


def _first_tag_with_prefix(html: str, id_prefix: str) -> str:
    match = re.search(rf'<input\b[^>]*\bid="{re.escape(id_prefix)}[^"]*"[^>]*>', html, re.S)
    assert match is not None, f"nenhum campo com prefixo {id_prefix}"
    return match.group(0)


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


def test_coerencia_do_login_e_da_senha_com_o_teto_de_credencial(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()
    with TestClient(app, follow_redirects=False) as client:
        page = client.get("/login").text
    assert _maxlength_of(page, "campo-login") == limits.CREDENTIAL_FIELD_MAXLENGTH
    assert _maxlength_of(page, "campo-senha") == limits.CREDENTIAL_FIELD_MAXLENGTH


def test_coerencia_dos_campos_de_dinheiro_taxa_e_prazo_no_simulador(campos_client):
    client, _target = campos_client
    page = client.get("/simulador").text
    for money_id in ("mensal", "unico", "fato-valor"):
        assert _maxlength_of(page, money_id) == limits.MONEY_FIELD_MAXLENGTH
        assert _inputmode_of(page, money_id) == "decimal"
    assert _maxlength_of(page, "prazo") == limits.MAX_DIGITS
    assert _inputmode_of(page, "prazo") == "numeric"
    assert _maxlength_of(page, "nome") == limits.SCENARIO_NAME_MAX
    assert _maxlength_of(page, "fato-validade") == limits.VALIDITY_FIELD_MAXLENGTH


def test_coerencia_da_taxa_opcional_e_do_aporte_em_dividas(campos_client):
    client, _target = campos_client
    page = client.get("/dividas").text
    tag = _first_tag_with_prefix(page, "taxa-")
    found = re.search(r'maxlength="(\d+)"', tag)
    assert found is not None
    assert int(found.group(1)) == limits.RATE_FIELD_MAXLENGTH
    assert "required" not in tag
    assert _maxlength_of(page, "aporte") == limits.MONEY_FIELD_MAXLENGTH
    assert "required" in _input_tag(page, "aporte")
    assert _maxlength_of(page, "quitacao") == limits.MONEY_FIELD_MAXLENGTH
    assert _maxlength_of(page, "transporte") == limits.MONEY_FIELD_MAXLENGTH


def test_coerencia_da_pergunta_livre_no_consultor(campos_client):
    client, _target = campos_client
    page = client.get("/consultor").text
    assert _maxlength_of(page, "pergunta-livre") == limits.MAX_QUESTION
    assert "required" in _input_tag(page, "pergunta-livre")


def test_coerencia_da_expressao_da_regra(campos_client):
    client, _target = campos_client
    page = client.get("/regras").text
    assert _maxlength_of(page, "campo-match-value") == limits.RULE_EXPRESSION_MAX
    assert "required" in _input_tag(page, "campo-match-value")


def test_coerencia_do_grupo_novo_na_correcao_de_gastos(campos_client):
    client, target = campos_client
    page = client.get(
        "/gastos", params={"eixo": "grupo", "chave": "Mercado da Esquina", "corrigir": target}
    ).text
    assert 'id="correcao"' in page
    assert _maxlength_of(page, "campo-correcao-grupo-novo") == limits.CATEGORY_GROUP_MAXLENGTH


def test_coerencia_dos_campos_em_configuracao(campos_client):
    client, _target = campos_client
    page = client.get("/configuracao").text

    # Fatos e metas: a mesma marcação atende dinheiro (quitação/transporte) e
    # meses (reserva/mediana) — o teto e o inputmode seguem a unidade do item.
    assert _maxlength_of(page, "campo-quitacao-cdc") == limits.MONEY_FIELD_MAXLENGTH
    assert _inputmode_of(page, "campo-quitacao-cdc") == "decimal"
    assert _maxlength_of(page, "campo-reserva-meses") == limits.MAX_DIGITS
    assert _inputmode_of(page, "campo-reserva-meses") == "numeric"
    assert "required" in _input_tag(page, "campo-quitacao-cdc")

    assert _maxlength_of(page, "apelido-1") == limits.PAYEE_ALIAS_MAX
    assert "required" not in _input_tag(page, "apelido-1")

    assert _maxlength_of(page, "financiamento-mortgage-saldo") == limits.MONEY_FIELD_MAXLENGTH
    assert _maxlength_of(page, "financiamento-mortgage-taxa") == limits.RATE_FIELD_MAXLENGTH
    assert _maxlength_of(page, "financiamento-mortgage-prazo") == limits.MAX_DIGITS
    assert _maxlength_of(page, "financiamento-vehicle-taxa") == limits.RATE_FIELD_MAXLENGTH
    assert _maxlength_of(page, "financiamento-vehicle-parcela") == limits.MONEY_FIELD_MAXLENGTH
    assert _maxlength_of(page, "financiamento-vehicle-prazo") == limits.MAX_DIGITS
    assert "required" in _input_tag(page, "financiamento-vehicle-vencimento")
    assert "maxlength" not in _input_tag(page, "financiamento-vehicle-vencimento")

    assert _maxlength_of(page, "proposta-nova-nome") == limits.NAME_MAX
    assert "required" in _input_tag(page, "proposta-nova-nome")
    assert _maxlength_of(page, "proposta-nova-taxa") == limits.RATE_FIELD_MAXLENGTH
    assert "required" not in _input_tag(page, "proposta-nova-taxa")
    assert _maxlength_of(page, "proposta-nova-prazo") == limits.MAX_DIGITS
    assert _maxlength_of(page, "proposta-nova-liberado") == limits.MONEY_FIELD_MAXLENGTH
    assert _maxlength_of(page, "proposta-nova-contratacao") == limits.MONEY_FIELD_MAXLENGTH
    assert "required" not in _input_tag(page, "proposta-nova-contratacao")

    assert _maxlength_of(page, "proposta-1-taxa") == limits.RATE_FIELD_MAXLENGTH
    assert "required" not in _input_tag(page, "proposta-1-taxa")
    assert _maxlength_of(page, "proposta-1-prazo") == limits.MAX_DIGITS
    assert "required" in _input_tag(page, "proposta-1-prazo")
    assert _maxlength_of(page, "proposta-1-liberado") == limits.MONEY_FIELD_MAXLENGTH

    assert _maxlength_of(page, "ia-chave") == limits.CREDENTIAL_FIELD_MAXLENGTH

    limite_id = "campo-acc-cartao-coerencia-limite"
    taxa_id = "campo-acc-cartao-coerencia-taxa"
    fechamento_id = "campo-acc-cartao-coerencia-fechamento"
    assert _maxlength_of(page, limite_id) == limits.MONEY_FIELD_MAXLENGTH
    assert _inputmode_of(page, limite_id) == "decimal"
    assert _maxlength_of(page, taxa_id) == limits.RATE_FIELD_MAXLENGTH
    assert _maxlength_of(page, fechamento_id) == limits.DAY_FIELD_MAXLENGTH
    assert _inputmode_of(page, fechamento_id) == "numeric"


def test_a_twelve_digit_aporte_and_a_420_month_financing_term_are_both_accepted(campos_client):
    client, _target = campos_client
    debts_page = client.get("/dividas").text
    laddered = re.search(r'data-degrau="(\d+)" data-taxa="\d+"', debts_page)
    assert laddered is not None, "nenhum degrau com taxa para simular o aporte"
    degrau = laddered.group(1)

    twelve_digits = client.post(
        "/dividas/simular", data={"degrau": degrau, "aporte": "999.999.999,99"}
    )
    assert twelve_digits.status_code == 200
    assert 'id="recusa"' not in twelve_digits.text

    financing = client.post(
        "/configuracao/financiamento",
        data={
            "tipo": "vehicle",
            "taxa": "1,63",
            "parcela": "1.235,33",
            "prazo": "420",
            "vencimento": "2025-06-11",
        },
    )
    assert financing.status_code == 200
    assert "Salvo." in financing.text
    conn = connect()
    term = conn.execute("SELECT term_months FROM financings WHERE kind = 'vehicle'").fetchone()[0]
    conn.close()
    assert term == 420
