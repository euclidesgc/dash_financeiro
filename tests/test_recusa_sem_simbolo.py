import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import load_seed, seed_taxonomy
from tests.conftest import load, narrowed, transaction

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
TODAY = "2026-09-05"

FORBIDDEN = ("None", "null", "NoneType", "Traceback")


@pytest.fixture
def refusing(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", TODAY)
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    load(conn, [transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre")])
    seed_taxonomy(conn, narrowed(load_seed(), []))
    classify_all(conn)
    conn.commit()
    target = conn.execute("SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'").fetchone()[0]
    conn.close()
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield client, target


def _cases(target: int) -> tuple[tuple[str, dict[str, str], dict[str, str], int], ...]:
    return (
        ("/consultor", {}, {"pergunta": ""}, 400),
        ("/consultor/adiar", {}, {"nome": "pergunta-desconhecida-xyz"}, 400),
        ("/comprometido/dispensar", {}, {"serie": "serie-desconhecida-xyz"}, 400),
        ("/dividas/taxa", {}, {"degrau": "xxx", "taxa": ""}, 400),
        ("/dividas/simular", {}, {"degrau": "xxx", "aporte": "100"}, 400),
        ("/dividas/parametro", {}, {"nome": "campo-desconhecido-xyz", "valor": ""}, 400),
        ("/configuracao/financiamento", {}, {"tipo": ""}, 400),
        ("/configuracao/proposta", {}, {"nome": ""}, 400),
        ("/regras", {}, {"match_kind": ""}, 400),
        (
            "/regras/999999/editar",
            {},
            {"match_kind": "category", "match_value": "x", "group_id": "1"},
            400,
        ),
        ("/regras/999999/remover", {}, {}, 400),
        ("/configuracao", {}, {"nome": "campo-desconhecido-xyz", "valor": ""}, 400),
        (
            "/configuracao/beneficiario",
            {},
            {"beneficiario": "beneficiario-desconhecido-xyz", "nome": "Apelido"},
            400,
        ),
        ("/configuracao/cnpj", {}, {"beneficiario": "qualquer"}, 200),
        ("/configuracao/ia", {}, {"chave": "", "modelo": "modelo-desconhecido-xyz"}, 400),
        (
            "/gastos/correcao",
            {"corrigir": str(target)},
            {"grupo": "", "grupo_novo": "", "natureza": "variável", "essencialidade": "supérfluo"},
            400,
        ),
        ("/simulador", {}, {"tipo": "tipo-desconhecido-xyz"}, 400),
        ("/simulador/fato", {}, {"nome": ""}, 400),
        (
            "/configuracao/cartao",
            {},
            {"cartao": "", "campo": "campo-desconhecido-xyz", "valor": ""},
            400,
        ),
    )


def test_recusa_sem_simbolo_varre_as_rotas_de_escrita_do_painel(refusing):
    client, target = refusing

    for path, params, data, expected_status in _cases(target):
        response = client.post(path, params=params, data=data)

        assert response.status_code == expected_status, f"{path}: {response.status_code}"
        for needle in FORBIDDEN:
            assert needle not in response.text, f"{path} devolveu {needle!r} na resposta"


def test_a_sincronizacao_sem_credencial_recusa_sem_simbolo(refusing, monkeypatch):
    client, _target = refusing
    monkeypatch.setenv("DASH_SYNC_SOURCE", "pluggy")
    monkeypatch.delenv("PLUGGY_CLIENT_ID", raising=False)
    monkeypatch.delenv("PLUGGY_CLIENT_SECRET", raising=False)

    response = client.post("/sincronizar")

    assert response.status_code == 400
    for needle in FORBIDDEN:
        assert needle not in response.text
