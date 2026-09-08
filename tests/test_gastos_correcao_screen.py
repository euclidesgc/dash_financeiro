import re

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.taxonomy.classify import classify_all
from app.taxonomy.seed import load_seed, seed_taxonomy
from tests.conftest import load, narrowed, rule, transaction

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
TODAY = "2026-09-05"

SCREEN = "/gastos"
CORRECTION = f"{SCREEN}/correcao"

CATEGORY = "Categoria da fonte"
FINANCEIRO = "Financeiro"
PESSOAL = "Pessoal"

CIFRA = re.compile(r'class="[^"]*\bcifra\b[^"]*"[^>]*>([^<]*)<')


def _between(html: str, marker: str, closing: str = "</p>") -> str:
    found = re.search(re.escape(f'id="{marker}"') + r".*?" + re.escape(closing), html, re.S)
    assert found is not None, f"{marker} não encontrado na resposta"
    return found.group(0)


def _absent(html: str, marker: str) -> bool:
    return f'id="{marker}"' not in html


def _table_total(html: str) -> str:
    segment = re.search(r'id="tabela".*?id="detalhe"', html, re.S)
    assert segment is not None
    figures = CIFRA.findall(segment.group(0))
    return figures[0].strip()


def _select_options(html: str, name: str) -> str:
    found = re.search(rf'<select[^>]*name="{name}"[^>]*>(.*?)</select>', html, re.S)
    assert found is not None, f"select {name} não encontrado"
    return found.group(1)


def _rows_of(section_id: str, html: str) -> str:
    found = re.search(
        re.escape(f'<section id="{section_id}"') + r".*?<tbody>(.*?)</tbody>", html, re.S
    )
    assert found is not None
    return found.group(1)


def _group_id(conn, name: str) -> int:
    return conn.execute("SELECT id FROM category_groups WHERE name = ?", (name,)).fetchone()[0]


@pytest.fixture
def three_payments():
    return [
        transaction("t-ml-1", "2026-09-02", -100.00, descricao="Mercado Livre", categoria=CATEGORY),
        transaction("t-ml-2", "2026-09-03", -50.00, descricao="Mercado Livre", categoria=CATEGORY),
        transaction(
            "t-mlp", "2026-09-04", -25.00, descricao="Mercado Livre Pago", categoria=CATEGORY
        ),
    ]


def _client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", TODAY)
    app = create_app()
    return app


@pytest.fixture
def opened(tmp_path, monkeypatch, three_payments):
    app = _client(tmp_path, monkeypatch)
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    load(conn, three_payments)
    seed_taxonomy(conn, narrowed(load_seed(), []))
    classify_all(conn)
    conn.commit()
    target = conn.execute("SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'").fetchone()[0]
    pessoal = _group_id(conn, PESSOAL)
    conn.close()
    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield client, target, pessoal


def test_opening_the_correction_shows_both_reaches_the_fields_and_leaves_the_totals_untouched(
    opened,
):
    client, target, _pessoal = opened

    page = client.get(SCREEN, params={"eixo": "grupo", "chave": "Outros", "corrigir": target})
    without_target = client.get(SCREEN, params={"eixo": "grupo", "chave": "Outros"})
    unknown_target = client.get(
        SCREEN, params={"eixo": "grupo", "chave": "Outros", "corrigir": 999999}
    )

    assert page.status_code == 200
    for needle in (
        'id="correcao"',
        'name="grupo"',
        'name="natureza"',
        'name="essencialidade"',
        'name="grupo_novo"',
        "mercado livre",
    ):
        assert needle in page.text
    assert 'name="categoria"' not in page.text

    reach = _between(page.text, "alcance")
    assert "2 lançamento" in reach
    assert "−R$ 150,00" in reach
    assert "em toda a base" in reach

    category_reach = _between(page.text, "alcance-categoria")
    assert "3 lançamento" in category_reach
    assert "−R$ 175,00" in category_reach

    assert without_target.status_code == 200
    assert _absent(without_target.text, "correcao")
    assert unknown_target.status_code == 200
    assert _absent(unknown_target.text, "correcao")

    for response in (page, without_target, unknown_target):
        assert _table_total(response.text) == "−R$ 175,00"


def test_a_correction_that_writes_a_rule_reports_and_repartitions_the_axis(opened):
    client, target, pessoal = opened

    response = client.post(
        CORRECTION,
        params={
            "eixo": "grupo",
            "inicio": "2026-09-01",
            "fim": "2026-09-05",
            "chave": "Outros",
            "corrigir": target,
        },
        data={
            "grupo": str(pessoal),
            "grupo_novo": "",
            "natureza": "variável",
            "essencialidade": "supérfluo",
        },
    )

    assert response.status_code == 200
    result = _between(response.text, "resultado")
    assert "2 lançamento" in result
    assert PESSOAL in result

    conn = connect()
    assert (
        conn.execute(
            "SELECT count(*) FROM category_rules WHERE match_kind = 'description'"
        ).fetchone()[0]
        == 1
    )
    assert (
        conn.execute(
            "SELECT count(*) FROM transactions WHERE rule_id = "
            "(SELECT id FROM category_rules WHERE match_kind = 'description')"
        ).fetchone()[0]
        == 2
    )
    conn.close()

    rows = _rows_of("tabela", response.text)
    pessoal_row = next(part for part in rows.split("<tr") if f">{PESSOAL}<" in part)
    assert "−R$ 150,00" in pessoal_row
    assert _table_total(response.text) == "−R$ 175,00"


def test_a_lower_precedence_rule_already_holding_the_payee_is_named_in_the_result(
    tmp_path, monkeypatch, three_payments
):
    app = _client(tmp_path, monkeypatch)
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    load(conn, three_payments)
    seed_taxonomy(
        conn,
        narrowed(load_seed(), [rule("description", "^mercado", FINANCEIRO, "fixa", "essencial")]),
    )
    classify_all(conn)
    conn.commit()
    target = conn.execute("SELECT id FROM transactions WHERE pluggy_id = 't-ml-1'").fetchone()[0]
    pessoal = _group_id(conn, PESSOAL)
    conn.close()

    with TestClient(app, follow_redirects=False) as client:
        client.post("/login", data={"login": LOGIN, "senha": PASSWORD})

        opened = client.get(
            SCREEN, params={"eixo": "grupo", "chave": FINANCEIRO, "corrigir": target}
        )
        reach = _between(opened.text, "alcance")
        assert "2 lançamento" in reach
        assert "−R$ 150,00" in reach

        response = client.post(
            CORRECTION,
            params={
                "eixo": "grupo",
                "inicio": "2026-09-01",
                "fim": "2026-09-05",
                "chave": FINANCEIRO,
                "corrigir": target,
            },
            data={"grupo": str(pessoal), "natureza": "variável", "essencialidade": "supérfluo"},
        )

    assert response.status_code == 200
    result = _between(response.text, "resultado")
    assert "0 dos 2 lançamentos previstos" in result
    assert "^mercado" in result
    assert 'href="/regras"' in result

    conn = connect()
    assert conn.execute("SELECT count(*) FROM category_rules").fetchone()[0] == 2
    assert (
        conn.execute(
            "SELECT count(*) FROM transactions WHERE group_id = "
            "(SELECT id FROM category_groups WHERE name = ?)",
            (PESSOAL,),
        ).fetchone()[0]
        == 0
    )
    conn.close()


def test_a_new_group_is_created_from_a_raw_utf8_body(opened):
    client, target, _pessoal = opened

    def percent_encode(text: str) -> str:
        return "".join(f"%{byte:02X}" for byte in text.encode("utf-8"))

    body = (
        "grupo=&grupo_novo="
        + percent_encode("Educação do filho")
        + "&natureza="
        + percent_encode("variável")
        + "&essencialidade="
        + percent_encode("supérfluo")
    )

    response = client.post(
        CORRECTION,
        params={
            "eixo": "grupo",
            "inicio": "2026-09-01",
            "fim": "2026-09-05",
            "chave": "Outros",
            "corrigir": target,
        },
        content=body.encode("utf-8"),
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    conn = connect()
    assert (
        conn.execute(
            "SELECT count(*) FROM category_groups WHERE name = 'Educação do filho'"
        ).fetchone()[0]
        == 1
    )
    assert (
        conn.execute(
            "SELECT nature FROM category_rules WHERE match_kind = 'description'"
        ).fetchone()[0]
        == "variável"
    )
    conn.close()
    assert "Educação do filho" in _select_options(response.text, "grupo")


def test_the_two_refusals_leave_no_rule_beside_the_positive_control(opened):
    client, target, pessoal = opened

    invalid_group = client.post(
        CORRECTION,
        params={
            "eixo": "grupo",
            "inicio": "2026-09-01",
            "fim": "2026-09-05",
            "chave": "Outros",
            "corrigir": target,
        },
        data={"grupo": "9999", "natureza": "variável", "essencialidade": "supérfluo"},
    )
    unknown_payee = client.post(
        CORRECTION,
        params={
            "eixo": "grupo",
            "inicio": "2026-09-01",
            "fim": "2026-09-05",
            "chave": "Outros",
            "corrigir": 999999,
        },
        data={"grupo": str(pessoal), "natureza": "variável", "essencialidade": "supérfluo"},
    )

    assert invalid_group.status_code == 400
    assert "grupo inválido: 9999" in _between(invalid_group.text, "erro-correcao")
    assert unknown_payee.status_code == 400
    assert "beneficiário desconhecido" in _between(unknown_payee.text, "erro-correcao")

    conn = connect()
    assert (
        conn.execute(
            "SELECT count(*) FROM category_rules WHERE match_kind = 'description'"
        ).fetchone()[0]
        == 0
    )
    conn.close()

    valid = client.post(
        CORRECTION,
        params={
            "eixo": "grupo",
            "inicio": "2026-09-01",
            "fim": "2026-09-05",
            "chave": "Outros",
            "corrigir": target,
        },
        data={"grupo": str(pessoal), "natureza": "variável", "essencialidade": "supérfluo"},
    )
    assert valid.status_code == 200
    conn = connect()
    assert (
        conn.execute(
            "SELECT count(*) FROM category_rules WHERE match_kind = 'description'"
        ).fetchone()[0]
        == 1
    )
    conn.close()


def test_a_correction_posted_without_a_target_still_shows_the_refusal(opened):
    client, _target, pessoal = opened

    response = client.post(
        CORRECTION,
        params={"eixo": "grupo", "inicio": "2026-09-01", "fim": "2026-09-05", "chave": "Outros"},
        data={"grupo": str(pessoal), "natureza": "variável", "essencialidade": "supérfluo"},
    )

    assert response.status_code == 400
    assert "Nenhum lançamento selecionado para corrigir." in _between(
        response.text, "erro-correcao"
    )

    conn = connect()
    assert (
        conn.execute(
            "SELECT count(*) FROM category_rules WHERE match_kind = 'description'"
        ).fetchone()[0]
        == 0
    )
    conn.close()


def test_the_payee_that_only_shares_a_prefix_stays_where_it_was(opened):
    client, target, pessoal = opened

    response = client.post(
        CORRECTION,
        params={"eixo": "grupo", "corrigir": target},
        data={"grupo": str(pessoal), "natureza": "variável", "essencialidade": "supérfluo"},
    )

    assert response.status_code == 200
    conn = connect()
    exact = [
        row["name"]
        for row in conn.execute(
            "SELECT g.name FROM transactions AS t JOIN category_groups AS g ON g.id = t.group_id "
            "WHERE t.payee = 'mercado livre'"
        )
    ]
    sibling = [
        row["name"]
        for row in conn.execute(
            "SELECT g.name FROM transactions AS t JOIN category_groups AS g ON g.id = t.group_id "
            "WHERE t.payee = 'mercado livre pago'"
        )
    ]
    conn.close()
    assert exact == [PESSOAL, PESSOAL]
    assert sibling == ["Outros"]


def test_rules_screen_lists_the_rule_written_from_the_correction(opened):
    client, target, pessoal = opened

    response = client.post(
        CORRECTION,
        params={"eixo": "grupo", "corrigir": target},
        data={"grupo": str(pessoal), "natureza": "variável", "essencialidade": "supérfluo"},
    )
    assert response.status_code == 200

    rules_page = client.get("/regras")
    assert rules_page.status_code == 200
    rows = _rows_of("regras", rules_page.text)
    row = next(
        part for part in rows.split("<tr") if "mercado" in part and "mercado livre pago" not in part
    )
    for needle in (PESSOAL, "variável", "supérfluo"):
        assert needle in row
    assert ">2<" in row

    conn = connect()
    assert (
        conn.execute(
            "SELECT count(*) FROM category_rules WHERE match_kind = 'description'"
        ).fetchone()[0]
        == 1
    )
    conn.close()
