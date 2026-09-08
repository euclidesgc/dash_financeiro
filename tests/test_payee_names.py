from urllib.parse import quote

import httpx
import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.ingest.loader import STALE_CONSOLIDATED, ingest
from app.main import create_app
from app.payees import lookup, names
from app.payees.names import DESCRIPTION, LEGAL, LOOKUP, OWNER, PLUGGY, display_name, ranked
from app.queries.axes import PAYEE_AXIS
from tests.conftest import ACCOUNT, load, transaction

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"

SCREEN = "/configuracao"
NAME_URL = f"{SCREEN}/beneficiario"
CNPJ_URL = f"{SCREEN}/cnpj"

FANTASY = "loja com nome fantasia"
BUSINESS = "loja so com razao social"
RECEIVER = "boleto so com recebedor"
BARE = "loja sem nome nenhum"

CNPJ = "12345678000199"
NICKNAME = "Consórcio Coimex"
LOOKED_UP = "COIMEX ADMINISTRADORA DE CONSORCIOS"


def _rows():
    return [
        transaction("t-fantasia", "2026-08-01", -100.0, descricao=FANTASY, nome_fantasia="Shopee"),
        transaction(
            "t-razao",
            "2026-08-02",
            -200.0,
            descricao=BUSINESS,
            razao_social="LOJA COMERCIO LTDA",
            cnpj=CNPJ,
        ),
        transaction(
            "t-recebedor", "2026-08-03", -300.0, descricao=RECEIVER, recebedor="IFOOD.COM S.A."
        ),
        transaction("t-nu", "2026-08-04", -50.0, descricao=BARE),
    ]


@pytest.fixture()
def conn(taxonomy_conn):
    load(taxonomy_conn, _rows())
    taxonomy_conn.execute("UPDATE transactions SET payee = description")
    taxonomy_conn.commit()
    return taxonomy_conn


def _named(conn):
    return display_name(conn)


def test_the_empty_string_is_absence_and_never_a_value(conn):
    stored = dict(
        conn.execute(
            "SELECT payee, merchant_legal_name FROM transactions WHERE payee = ?", (FANTASY,)
        ).fetchone()
    )

    assert stored["merchant_legal_name"] is None
    assert (
        conn.execute("SELECT count(*) FROM transactions WHERE merchant_name = ''").fetchone()[0]
        == 0
    )


def test_the_precedence_walks_from_the_owner_down_to_the_description(conn):
    names.name_it(conn, BARE, "Padaria da esquina", OWNER)
    found = _named(conn)

    assert found[BARE] == {"name": "Padaria da esquina", "source": OWNER}
    assert found[FANTASY] == {"name": "Shopee", "source": PLUGGY}
    assert found[BUSINESS] == {"name": "LOJA COMERCIO LTDA", "source": LEGAL}
    assert found[RECEIVER] == {"name": "IFOOD.COM S.A.", "source": LEGAL}


def test_a_payee_named_by_the_owner_keeps_the_looked_up_name_underneath(conn):
    names.name_it(conn, BUSINESS, LOOKED_UP, LOOKUP)
    names.name_it(conn, BUSINESS, NICKNAME, OWNER)

    assert _named(conn)[BUSINESS] == {"name": NICKNAME, "source": OWNER}

    names.forget(conn, BUSINESS, OWNER)

    # Reason: not the legal name, and not the description — one level down,
    # exactly.
    assert _named(conn)[BUSINESS] == {"name": LOOKED_UP, "source": LOOKUP}


def test_the_trade_name_of_the_pluggy_beats_the_looked_up_one(conn):
    names.name_it(conn, FANTASY, "OUTRO NOME LTDA", LOOKUP)

    assert _named(conn)[FANTASY]["source"] == PLUGGY


def test_the_list_is_ordered_by_how_much_money_each_one_represents(conn):
    listed = ranked(conn, 3)

    assert [row["payee"] for row in listed["payees"]] == [RECEIVER, BUSINESS, FANTASY]
    assert [row["total_cents"] for row in listed["payees"]] == [-30000, -20000, -10000]
    assert listed["total_payees"] == 4
    assert listed["payees"][0]["origin"] == LEGAL


def test_a_payee_with_no_name_anywhere_keeps_the_normalised_description(conn):
    assert _named(conn)[BARE] == {"name": BARE, "source": DESCRIPTION}
    assert BARE not in names.labels(conn)


def test_a_consolidated_file_without_the_new_keys_is_refused(taxonomy_conn):
    stale = transaction("t-velha", "2026-08-01", -10.0)
    for key in ("nome_fantasia", "razao_social", "cnpj", "recebedor"):
        stale.pop(key)

    result = ingest(taxonomy_conn, transactions=[stale], accounts=[ACCOUNT], source="tests")

    assert result.status == "failed"
    assert result.message == STALE_CONSOLIDATED
    assert result.transactions_written == 0


def test_an_unknown_source_is_refused_by_name(conn):
    with pytest.raises(names.UnknownSourceError) as refusal:
        names.name_it(conn, BARE, "qualquer", "inventada")

    assert "inventada" in str(refusal.value)


def test_the_cnpj_is_validated_as_fourteen_digits_before_becoming_a_url():
    assert lookup.digits("12.345.678/0001-99") == CNPJ

    for typed in ("../etc", "123", "", "123456780001999"):
        with pytest.raises(lookup.InvalidCnpjError):
            lookup.digits(typed)


def test_the_lookup_degrades_in_portuguese_when_the_network_does_not_answer(monkeypatch):
    def timeout(*args, **kwargs):
        raise httpx.TimeoutException("demorou")

    monkeypatch.setattr(httpx, "get", timeout)

    with pytest.raises(lookup.LookupUnavailableError) as refusal:
        lookup.trade_name(CNPJ)

    assert "tempo esgotou" in str(refusal.value)


def test_the_lookup_is_off_until_the_owner_turns_it_on(monkeypatch):
    monkeypatch.delenv("DASH_CNPJ_LOOKUP", raising=False)

    assert lookup.enabled() is False

    monkeypatch.setenv("DASH_CNPJ_LOOKUP", "sim")

    assert lookup.enabled() is True


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    opened_conn = connect()
    seed_user(opened_conn, LOGIN, PASSWORD)
    load(opened_conn, _rows())
    opened_conn.execute("UPDATE transactions SET payee = description")
    opened_conn.commit()
    opened_conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


def _total_spending() -> int:
    conn = connect()
    try:
        from app.queries.spending import total_spending_cents

        return total_spending_cents(conn)
    finally:
        conn.close()


def test_naming_a_payee_moves_no_total(client):
    before = _total_spending()

    named = client.post(NAME_URL, data={"beneficiario": BUSINESS, "nome": NICKNAME})

    assert named.status_code == 200
    assert NICKNAME in named.text
    assert _total_spending() == before


def test_an_accent_survives_the_form(client):
    client.post(NAME_URL, data={"beneficiario": BUSINESS, "nome": NICKNAME})

    conn = connect()
    try:
        stored = conn.execute(
            "SELECT name FROM payee_names WHERE payee = ? AND source = ?", (BUSINESS, OWNER)
        ).fetchone()
    finally:
        conn.close()

    assert stored["name"] == NICKNAME


def test_an_unknown_payee_is_refused_without_writing(client):
    refused = client.post(NAME_URL, data={"beneficiario": "nao-existe", "nome": "x"})

    assert refused.status_code == 400
    assert "nao-existe" in refused.text


def test_the_lookup_says_it_is_off_instead_of_hiding_the_button(client):
    answer = client.post(CNPJ_URL, data={"beneficiario": BUSINESS})

    assert answer.status_code == 200
    assert "DASH_CNPJ_LOOKUP" in answer.text


def test_the_lookup_degrades_with_200_and_keeps_the_name_already_there(client, monkeypatch):
    monkeypatch.setenv("DASH_CNPJ_LOOKUP", "sim")
    client.post(NAME_URL, data={"beneficiario": BUSINESS, "nome": NICKNAME})

    def timeout(*args, **kwargs):
        raise httpx.TimeoutException("demorou")

    monkeypatch.setattr(httpx, "get", timeout)
    answer = client.post(CNPJ_URL, data={"beneficiario": BUSINESS})

    assert answer.status_code == 200
    assert "tempo esgotou" in answer.text
    assert NICKNAME in answer.text


def test_a_payee_without_cnpj_is_told_so_and_never_reaches_the_network(client, monkeypatch):
    monkeypatch.setenv("DASH_CNPJ_LOOKUP", "sim")

    answer = client.post(CNPJ_URL, data={"beneficiario": BARE})

    assert answer.status_code == 200
    assert "não tem CNPJ" in answer.text


def test_the_payee_axis_shows_the_resolved_name_and_keeps_the_key(client):
    client.post(NAME_URL, data={"beneficiario": BUSINESS, "nome": NICKNAME})

    page = client.get(
        f"/gastos?eixo={PAYEE_AXIS}&inicio=2026-08-01&fim=2026-08-31&chave={quote(BUSINESS)}"
    ).text

    # Reason: the label resolves and the key does not — row['key'] is the
    # rendered name and the drill-down parameter at once, and the panel context
    # used to overwrite the resolved map after the table had built it.
    assert NICKNAME in page
    assert f"chave={quote(BUSINESS)}" in page
    # Reason: the drill-down heading names the key the list was opened by.
    assert f'<h3 class="section-title">{BUSINESS}' in page


def test_no_reading_screen_renames_the_axis_of_the_rules(client):
    client.post(NAME_URL, data={"beneficiario": BUSINESS, "nome": NICKNAME})

    assert NICKNAME not in client.get("/regras").text
