from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
REFERENCE = date(2026, 9, 5)

SCREEN = "/configuracao"
OFFER = f"{SCREEN}/proposta"
OFFER_REMOVE = f"{OFFER}/remover"


def _article(html: str, marker: str) -> str:
    start = html.index(marker)
    end = html.index("</article>", start)
    return html[start:end]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", REFERENCE.isoformat())
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


def _names(conn) -> list[str]:
    return [row["name"] for row in conn.execute("SELECT name FROM offers")]


def test_a_saved_offer_reads_back_on_the_screen_in_the_same_recorte(client):
    written = client.post(
        OFFER,
        data={
            "nome": "Banco Teste",
            "taxa": "10",
            "prazo": "2",
            "liberado": "1.000,00",
            "contratacao": "50,00",
        },
    )
    assert written.status_code == 200

    page = client.get(SCREEN).text
    article = _article(page, 'data-proposta="Banco Teste"')

    assert 'data-prazo="2"' in article
    assert "10,00%" in article
    assert "1.000,00" in article
    assert "50,00" in article
    assert "05/09/2026" in article


def test_a_dotted_amount_is_refused_and_the_next_request_is_the_positive_control(client):
    refused = client.post(
        OFFER,
        data={"nome": "Banco Ruim", "taxa": "1", "prazo": "2", "liberado": "5.000.00"},
    )

    assert refused.status_code == 400
    assert 'id="recusa"' in refused.text
    assert "Valor liberado" in refused.text
    assert 'id="propostas"' in refused.text

    accepted = client.post(
        OFFER,
        data={"nome": "Banco Bom", "taxa": "1", "prazo": "2", "liberado": "5.000,00"},
    )
    assert accepted.status_code == 200

    conn = connect()
    names = _names(conn)
    conn.close()
    assert "Banco Bom" in names
    assert "Banco Ruim" not in names


def test_an_offer_with_no_rate_is_saved_with_a_null_rate_and_shown_as_absent(client):
    written = client.post(
        OFFER,
        data={"nome": "Banco Sem Taxa", "taxa": "", "prazo": "24", "liberado": "1.000,00"},
    )
    assert written.status_code == 200

    conn = connect()
    rate = conn.execute(
        "SELECT monthly_rate_bp FROM offers WHERE name = 'Banco Sem Taxa'"
    ).fetchone()[0]
    conn.close()
    assert rate is None

    page = client.get(SCREEN).text
    article = _article(page, 'data-proposta="Banco Sem Taxa"')
    assert "Ausente" in article


def test_removing_one_offer_leaves_its_neighbour_on_the_screen(client):
    client.post(
        OFFER,
        data={
            "nome": "Banco Teste",
            "taxa": "10",
            "prazo": "2",
            "liberado": "1.000,00",
        },
    )
    client.post(
        OFFER,
        data={"nome": "Banco Sem Taxa", "taxa": "", "prazo": "24", "liberado": "1.000,00"},
    )

    removed = client.post(OFFER_REMOVE, data={"nome": "Banco Sem Taxa"})

    assert removed.status_code == 200
    assert 'data-proposta="Banco Sem Taxa"' not in removed.text
    assert 'data-proposta="Banco Teste"' in removed.text
