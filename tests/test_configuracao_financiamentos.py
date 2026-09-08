import json
import re
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.debts.ladder import rebuild
from app.main import create_app

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
REFERENCE = date(2026, 9, 5)

SCREEN = "/configuracao"
FINANCING = f"{SCREEN}/financiamento"
DEBTS = "/dividas"

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

MORTGAGE_JSON = {
    "prazo_restante_meses": 370,
    "saldo_devedor": 238585.18,
    "juros_efetivos_aa_pct": 8.9899,
}
VEHICLE_JSON = {
    "prazo_meses": 60,
    "juros_efetivo_mensal_pct": 1.63,
    "valor_parcela": 1235.33,
    "primeiro_vencimento": "2025-06-11",
}


def _insert(conn, row):
    conn.execute(
        "INSERT INTO financings "
        "(kind, monthly_rate_bp, term_months, balance_cents, payment_cents, first_due_date) "
        "VALUES (:kind, :monthly_rate_bp, :term_months, :balance_cents, :payment_cents, :first_due_date)",
        row,
    )
    conn.commit()


def _section(html: str, marker: str) -> str:
    start = html.index(marker)
    end = html.index("</section>", start)
    return html[start:end]


def _article(html: str, marker: str) -> str:
    start = html.index(marker)
    end = html.index("</article>", start)
    return html[start:end]


def _boot(tmp_path, monkeypatch, *, manual_dir):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", REFERENCE.isoformat())
    monkeypatch.setenv("DASH_MANUAL_DIR", str(manual_dir))
    return create_app()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    app = _boot(tmp_path, monkeypatch, manual_dir=tmp_path / "sem-contrato")
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    _insert(conn, MORTGAGE_ROW)
    _insert(conn, VEHICLE_ROW)
    # A ladder already built once, as the daily rebuild already produces
    # before any of these tests touch the screen: without it /dividas would
    # start from an empty debts table, and no order would be there to change.
    rebuild(conn, today=REFERENCE)
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


def test_the_two_forms_read_from_the_table(client):
    page = client.get(SCREEN).text
    section = _section(page, 'id="financiamentos"')

    assert 'data-financiamento="mortgage"' in section
    assert re.search(r'name="saldo"[^>]*value="238\.585,18"', section)
    assert re.search(r'name="taxa"[^>]*value="0,72"', section)
    assert re.search(r'name="prazo"[^>]*value="370"', section)

    assert 'data-financiamento="vehicle"' in section
    assert re.search(r'name="taxa"[^>]*value="1,63"', section)
    assert re.search(r'name="parcela"[^>]*value="1\.235,33"', section)
    assert re.search(r'name="prazo"[^>]*value="60"', section)
    assert re.search(r'name="vencimento"[^>]*value="2025-06-11"', section)


def test_the_vehicle_balance_is_shown_and_not_an_input(client):
    page = client.get(SCREEN).text
    article = _article(page, 'data-financiamento="vehicle"')

    assert "−R$ 39.176,36" in article
    assert 'name="saldo"' not in article


def test_the_section_without_any_financing_is_two_empty_forms(tmp_path, monkeypatch):
    app = _boot(tmp_path, monkeypatch, manual_dir=tmp_path / "sem-contrato")
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()

    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        config_page = opened.get(SCREEN)
        debts_page = opened.get(DEBTS)

    assert config_page.status_code == 200
    section = _section(config_page.text, 'id="financiamentos"')
    assert re.search(r'name="saldo"[^>]*value=""', section)
    assert re.search(r'name="parcela"[^>]*value=""', section)
    assert "data-financiamento" not in debts_page.text
    assert "CDC do veículo" not in debts_page.text


def test_writing_the_mortgage_reorders_the_ladder_read_next(client):
    first = _section(client.get(DEBTS).text, 'id="escada"')
    assert re.search(r'<tr data-degrau="[^"]*" data-taxa="163"', first)

    written = client.post(
        FINANCING, data={"tipo": "mortgage", "saldo": "200.000,00", "taxa": "5,00", "prazo": "300"}
    )

    assert written.status_code == 200
    assert "Salvo." in written.text

    conn = connect()
    financing_row = conn.execute(
        "SELECT monthly_rate_bp, term_months, balance_cents FROM financings WHERE kind = 'mortgage'"
    ).fetchone()
    debts_row = conn.execute(
        "SELECT monthly_rate_bp, balance_cents FROM debts WHERE kind = 'mortgage'"
    ).fetchone()
    conn.close()
    assert tuple(financing_row) == (500, 300, -20000000)
    assert tuple(debts_row) == (500, -20000000)

    second = _section(client.get(DEBTS).text, 'id="escada"')
    assert re.search(r'<tr data-degrau="[^"]*" data-taxa="500"', second)


def test_a_typed_money_value_outside_the_grammar_is_refused_with_the_screen_up(client):
    refused = client.post(
        FINANCING, data={"tipo": "mortgage", "saldo": "abc", "taxa": "0,72", "prazo": "370"}
    )

    assert refused.status_code == 400
    assert 'id="recusa"' in refused.text
    assert "abc" in refused.text
    assert 'id="financiamentos"' in refused.text
    assert 'id="beneficiarios"' in refused.text

    conn = connect()
    balance = conn.execute(
        "SELECT balance_cents FROM financings WHERE kind = 'mortgage'"
    ).fetchone()[0]
    conn.close()
    assert balance == -23858518


def test_a_non_iso_date_a_zero_rate_and_an_unknown_kind_are_refused_never_500(client):
    cases = [
        {
            "tipo": "vehicle",
            "taxa": "1,63",
            "parcela": "1.235,33",
            "prazo": "60",
            "vencimento": "31/01/2026",
        },
        {
            "tipo": "vehicle",
            "taxa": "0",
            "parcela": "1.235,33",
            "prazo": "60",
            "vencimento": "2025-06-11",
        },
        {
            "tipo": "carro",
            "taxa": "1,63",
            "parcela": "1.235,33",
            "prazo": "60",
            "vencimento": "2025-06-11",
        },
    ]
    answers = [client.post(FINANCING, data=case) for case in cases]

    for answer in answers:
        assert answer.status_code == 400
        assert 'id="recusa"' in answer.text
    assert "31/01/2026" in answers[0].text
    assert "carro" in answers[2].text

    conn = connect()
    row = conn.execute(
        "SELECT monthly_rate_bp, first_due_date FROM financings WHERE kind = 'vehicle'"
    ).fetchone()
    conn.close()
    assert tuple(row) == (163, "2025-06-11")


def test_the_screen_write_reaches_the_ladder_the_import_produced(tmp_path, monkeypatch):
    manual = tmp_path / "manual"
    manual.mkdir()
    (manual / "financiamento_caixa.json").write_text(json.dumps(MORTGAGE_JSON))
    (manual / "cdc_safra_veiculo.json").write_text(json.dumps(VEHICLE_JSON))

    app = _boot(tmp_path, monkeypatch, manual_dir=manual)
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    rebuild(conn, today=REFERENCE)
    conn.close()

    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        first = _section(opened.get(DEBTS).text, 'id="escada"')

        written = opened.post(
            FINANCING,
            data={"tipo": "mortgage", "saldo": "100.000,00", "taxa": "0,72", "prazo": "370"},
        )
        assert written.status_code == 200

        second = _section(opened.get(DEBTS).text, 'id="escada"')

    assert re.search(r'data-taxa="72"\s+data-saldo="-23858518"', first)
    assert re.search(r'data-taxa="163"\s+data-saldo="-3917636"', first)
    assert re.search(r'data-taxa="72"\s+data-saldo="-10000000"', second)
    assert re.search(r'data-taxa="163"\s+data-saldo="-3917636"', second)


def test_typing_the_vehicle_reaches_the_same_numbers_importing_would(tmp_path, monkeypatch):
    empty_manual = tmp_path / "manual-vazio"
    empty_manual.mkdir()

    app = _boot(tmp_path, monkeypatch, manual_dir=empty_manual)
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()

    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        boot = opened.get(SCREEN)
        assert boot.status_code == 200
        assert 'id="financiamentos"' in boot.text

        written = opened.post(
            FINANCING,
            data={
                "tipo": "vehicle",
                "taxa": "1,63",
                "parcela": "1.235,33",
                "prazo": "60",
                "vencimento": "2025-06-11",
            },
        )
        assert written.status_code == 200

    conn = connect()
    row = conn.execute(
        "SELECT balance_cents, monthly_rate_bp, term_months, payment_cents "
        "FROM debts WHERE kind = 'vehicle'"
    ).fetchone()
    conn.close()

    assert tuple(row) == (-3917636, 163, 45, -123533)
