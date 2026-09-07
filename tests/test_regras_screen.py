import re

import pytest
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.routers.rules import EMPTY_MATCH_MESSAGE
from app.taxonomy.classify import MATCH_CATEGORY, MATCH_DESCRIPTION, classify_all
from app.taxonomy.seed import message, seed_taxonomy
from tests.conftest import load, narrowed, rule, transaction

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"

SCREEN = "/regras"

FIGURE = re.compile(r"^−?R\$ [\d.]+,\d{2}$")
CIFRA = re.compile(r'class="[^"]*\bcifra\b[^"]*"[^>]*>([^<]*)<')
RULES_BODY = re.compile(r'<section id="regras".*?<tbody>(.*?)</tbody>', re.S)
LOOSE_BODY = re.compile(r'<section id="sem-regra".*?<tbody>(.*?)</tbody>', re.S)

HELD = "Categoria que a regra segura"
LOOSE = "Categoria que nenhuma regra alcanca"
PAYEE = "loja do bairro"
UNKNOWN_GROUP = "9999"
BROKEN_EXPRESSION = "[a-"

HELD_AMOUNT = -40000
SECOND_AMOUNT = -25000
LOOSE_AMOUNT = -9000
SECOND_LOOSE_AMOUNT = -6000
HELD_ENTRIES = 2
PAYEE_ENTRIES = 2
LOOSE_ENTRIES = 2

START = "2026-03-02"
END = "2026-03-04"


def _rows(pattern: re.Pattern[str], html: str) -> list[str]:
    found = pattern.search(html)
    return [] if found is None else re.findall(r"<tr[^>]*>", found.group(1))


def _figures(html: str) -> list[str]:
    return [value.strip() for value in CIFRA.findall(html)]


def _count(statement: str, *params: object) -> int:
    conn = connect()
    try:
        return int(conn.execute(statement, params).fetchone()[0])
    finally:
        conn.close()


def _rule_id(match_value: str) -> int:
    return _count("SELECT id FROM category_rules WHERE match_value = ?", match_value)


@pytest.fixture()
def terms(seed):
    return {
        "group": seed["groups"][0]["name"],
        "other": seed["groups"][1]["name"],
        "nature": seed["natures"][0],
        "essentiality": seed["essentialities"][0],
        "last": seed["essentialities"][-1],
    }


@pytest.fixture()
def client(tmp_path, monkeypatch, seed, terms):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    app = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    load(
        conn,
        [
            transaction("t-held", START, HELD_AMOUNT / 100, descricao="Padaria", categoria=HELD),
            transaction("t-held-2", END, SECOND_AMOUNT / 100, descricao="Padaria", categoria=HELD),
            transaction(
                "t-loose",
                END,
                LOOSE_AMOUNT / 100,
                descricao="Loja do Bairro 12/03",
                categoria=LOOSE,
            ),
            transaction(
                "t-loose-2",
                END,
                SECOND_LOOSE_AMOUNT / 100,
                descricao="Loja do Bairro 15/04",
                categoria=LOOSE,
            ),
        ],
    )
    seed_taxonomy(
        conn,
        narrowed(
            seed,
            [rule(MATCH_CATEGORY, HELD, terms["group"], terms["nature"], terms["essentiality"])],
        ),
    )
    classify_all(conn)
    conn.commit()
    conn.close()
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/login", data={"login": LOGIN, "senha": PASSWORD})
        yield opened


def _write(client, form: dict[str, str], path: str = SCREEN):
    return client.post(path, data=form)


@pytest.fixture()
def new_rule(terms):
    conn = connect()
    try:
        group_id = conn.execute(
            "SELECT id FROM category_groups WHERE name = ?", (terms["other"],)
        ).fetchone()[0]
    finally:
        conn.close()
    return {
        "match_kind": MATCH_DESCRIPTION,
        "match_value": PAYEE,
        "group_id": str(group_id),
        "nature": terms["nature"],
        "essentiality": terms["essentiality"],
    }


def test_the_list_carries_one_row_per_rule_with_what_it_reaches(client, terms):
    page = client.get(SCREEN)
    row = next(part for part in page.text.split("<tr") if HELD in part)

    assert page.status_code == 200
    assert len(_rows(RULES_BODY, page.text)) == _count("SELECT count(*) FROM category_rules")
    for held in (HELD, terms["group"], terms["nature"], terms["essentiality"], f">{HELD_ENTRIES}<"):
        assert held in row


def test_a_new_rule_says_how_many_transactions_it_reclassified(client, new_rule):
    written = _write(client, new_rule)

    assert written.status_code == 200
    assert "lançamentos reclassificados" in written.text
    assert (
        _count(
            "SELECT count(*) FROM category_rules WHERE match_kind = ? AND match_value = ?",
            MATCH_DESCRIPTION,
            PAYEE,
        )
        == 1
    )
    assert (
        _count("SELECT count(*) FROM transactions WHERE rule_id = ?", _rule_id(PAYEE))
        == PAYEE_ENTRIES
    )


def test_a_rule_that_reaches_nothing_says_so_instead_of_going_quiet(client, new_rule):
    written = _write(client, new_rule | {"match_value": PAYEE.capitalize()})

    assert written.status_code == 200
    assert "não alcançou nenhum lançamento" in written.text
    assert "caixa baixa, sem acento e sem dígito" in written.text
    assert (
        _count("SELECT count(*) FROM transactions WHERE rule_id = ?", _rule_id(PAYEE.capitalize()))
        == 0
    )


def test_the_form_shows_the_shape_a_description_is_matched_against(client):
    page = client.get(SCREEN)
    samples = re.findall(r'<span class="sample">([^<]*)</span>', page.text)

    assert samples
    assert all(
        sample == sample.lower() and not any(c.isdigit() for c in sample) for sample in samples
    )


def test_editing_a_rule_reclassifies_what_it_holds(client, terms):
    rule_id = _rule_id(HELD)
    group_id = _count("SELECT group_id FROM category_rules WHERE id = ?", rule_id)

    edited = _write(
        client,
        {
            "match_kind": MATCH_CATEGORY,
            "match_value": HELD,
            "group_id": str(group_id),
            "nature": terms["nature"],
            "essentiality": terms["last"],
        },
        f"{SCREEN}/{rule_id}/editar",
    )

    assert edited.status_code == 200
    assert f"{HELD_ENTRIES} lançamentos reclassificados" in edited.text
    assert (
        _count("SELECT count(*) FROM transactions WHERE essentiality = ?", terms["last"])
        == HELD_ENTRIES
    )


def test_removing_a_rule_drops_what_it_held_into_the_block_that_leads_the_screen(client):
    rule_id = _rule_id(HELD)

    removed = _write(client, {}, f"{SCREEN}/{rule_id}/remover")
    loose = _rows(LOOSE_BODY, removed.text)

    assert removed.status_code == 200
    assert f"{HELD_ENTRIES} lançamentos reclassificados" in removed.text
    assert _count("SELECT count(*) FROM transactions WHERE rule_id IS NULL") == (
        HELD_ENTRIES + LOOSE_ENTRIES
    )
    assert removed.text.index('id="sem-regra"') < removed.text.index('id="regras"')
    assert len(loose) > 1
    assert HELD in removed.text.split('id="sem-regra"')[1].split('id="regras"')[0]


def test_the_block_that_leads_the_screen_starts_at_the_biggest_absolute_value(client):
    removed = _write(client, {}, f"{SCREEN}/{_rule_id(HELD)}/remover")
    block = removed.text.split('id="sem-regra"')[1].split('id="regras"')[0]
    figures = [value.replace(".", "").replace(",", "") for value in _figures(block)[1:]]

    assert figures
    assert figures == sorted(figures, key=lambda value: -int(re.sub(r"\D", "", value)))


def test_a_term_outside_the_vocabulary_is_refused_by_name_and_nothing_is_written(client, new_rule):
    before = _count("SELECT count(*) FROM category_rules")

    refused = _write(client, new_rule | {"group_id": UNKNOWN_GROUP})

    assert refused.status_code == 400
    assert message("invalid_group", UNKNOWN_GROUP) in refused.text
    assert _count("SELECT count(*) FROM category_rules") == before


def test_an_expression_that_does_not_compile_is_refused_and_nothing_is_written(client, new_rule):
    before = _count("SELECT count(*) FROM category_rules")

    refused = _write(client, new_rule | {"match_value": BROKEN_EXPRESSION})

    assert refused.status_code == 400
    assert message("invalid_expression", BROKEN_EXPRESSION) in refused.text
    assert _count("SELECT count(*) FROM category_rules") == before


def test_an_empty_match_is_refused_before_it_swallows_the_whole_base(client, new_rule):
    before = _count("SELECT count(*) FROM transactions WHERE rule_id IS NOT NULL")

    refused = _write(client, new_rule | {"match_value": ""})

    assert refused.status_code == 400
    assert EMPTY_MATCH_MESSAGE in refused.text
    assert _count("SELECT count(*) FROM transactions WHERE rule_id IS NOT NULL") == before


def test_the_refused_form_comes_back_carrying_what_was_typed(client, new_rule):
    refused = _write(client, new_rule | {"group_id": UNKNOWN_GROUP})

    assert f'value="{PAYEE}"' in refused.text
    assert 'aria-describedby="erro-regra"' in refused.text
    assert refused.text.count('id="erro-regra"') == 1


def test_every_figure_of_the_screen_carries_the_minus_glued_to_the_number(client):
    _write(client, {}, f"{SCREEN}/{_rule_id(HELD)}/remover")
    figures = _figures(client.get(SCREEN).text)

    assert figures
    assert [value for value in figures if not FIGURE.match(value)] == []


def test_a_row_of_the_block_carries_the_match_back_into_the_form(client):
    _write(client, {}, f"{SCREEN}/{_rule_id(HELD)}/remover")
    page = client.get(SCREEN, params={"tipo": MATCH_CATEGORY, "valor": LOOSE})

    assert f'value="{LOOSE}"' in page.text
    assert f"?tipo={MATCH_CATEGORY}&amp;valor=" in page.text


def test_asking_to_edit_a_rule_opens_the_form_on_it(client):
    rule_id = _rule_id(HELD)

    page = client.get(SCREEN, params={"editar": rule_id})

    assert f'action="{SCREEN}/{rule_id}/editar"' in page.text
    assert f'value="{HELD}"' in page.text


def test_a_form_body_that_carries_raw_utf8_bytes_still_finds_the_vocabulary(client, seed, new_rule):
    accented = next(value for value in seed["natures"] if not value.isascii())
    body = "&".join(
        f"{field}={value}" for field, value in (new_rule | {"nature": accented}).items()
    )

    written = client.post(
        SCREEN,
        content=body.encode("utf-8"),
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    assert written.status_code == 200
    assert (
        _count(
            "SELECT count(*) FROM category_rules WHERE nature = ? AND match_value = ?",
            accented,
            PAYEE,
        )
        == 1
    )
