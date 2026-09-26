import json

import pytest
from fastapi.testclient import TestClient

from app.advisor.chat import MAX_ROUNDS, TOO_LONG, UNCHECKED, system_prompt
from app.advisor.provider import ProviderError, Reply
from app.advisor.providers import MISSING_KEY
from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app
from app.routers.advisor_chat import get_provider
from app.taxonomy.seed import seed_taxonomy
from tests.advisor_fakes import ScriptedProvider, answer, call
from tests.conftest import load, transaction

LOGIN = "teste"
PASSWORD = "senha-teste-9k2"
QUESTION = "quais foram meus gastos com posto em agosto?"
SEARCH = {"text": "posto", "date_from": "2026-08-01", "date_to": "2026-08-31"}


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DASH_ENV_FILE", "/dev/null")
    monkeypatch.setenv("DASH_DB_PATH", str(tmp_path / "dash.sqlite"))
    monkeypatch.setenv("SESSION_SECRET", "chave-de-teste")
    monkeypatch.setenv("DASH_TODAY", "2026-09-26")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    built = create_app()
    conn = connect()
    seed_user(conn, LOGIN, PASSWORD)
    seed_taxonomy(conn)
    load(
        conn,
        [
            transaction("p1", "2026-08-04", -100.00, descricao="Posto Sao Joao"),
            transaction("p2", "2026-08-31", -85.50, descricao="Posto dos Cavaleiros"),
        ],
    )
    conn.close()
    return built


@pytest.fixture()
def client(app):
    with TestClient(app, follow_redirects=False) as opened:
        opened.post("/api/auth/login", json={"login": LOGIN, "password": PASSWORD})
        yield opened


def _use(app, provider):
    app.dependency_overrides[get_provider] = lambda: provider


def _stored_roles(conversation_id):
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT role, content, provider FROM advisor_messages WHERE conversation_id = ?"
            " ORDER BY position",
            (conversation_id,),
        ).fetchall()
    finally:
        conn.close()
    return rows


def _new_conversation(client):
    response = client.post("/api/advisor/conversations")
    assert response.status_code == 201
    return response.json()["id"]


def test_every_advisor_route_demands_a_session(app):
    with TestClient(app, follow_redirects=False) as anonymous:
        for method, path in [
            ("get", "/api/advisor/status"),
            ("get", "/api/advisor/conversations"),
            ("post", "/api/advisor/conversations"),
            ("get", "/api/advisor/conversations/1"),
            ("post", "/api/advisor/conversations/1/messages"),
        ]:
            assert getattr(anonymous, method)(path).status_code == 401, path


def test_without_a_key_status_explains_and_sending_is_refused(client):
    status = client.get("/api/advisor/status").json()
    conversation_id = _new_conversation(client)

    sent = client.post(
        f"/api/advisor/conversations/{conversation_id}/messages", json={"text": QUESTION}
    )

    assert status == {"available": False, "provider": None, "model": None, "message": MISSING_KEY}
    assert sent.status_code == 503
    assert sent.json()["detail"] == MISSING_KEY
    assert _stored_roles(conversation_id) == []


def test_status_names_the_selected_provider(app, client):
    _use(app, ScriptedProvider(script=[], name="gemini", model="gemini-2.5-flash"))

    assert client.get("/api/advisor/status").json() == {
        "available": True,
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "message": None,
    }


def test_question_runs_the_tool_and_answers_with_its_numbers(app, client):
    provider = ScriptedProvider(
        script=[
            call("search_transactions", SEARCH),
            answer("Em agosto foram 2 gastos com posto, somando −R$ 185,50."),
        ]
    )
    _use(app, provider)
    conversation_id = _new_conversation(client)

    response = client.post(
        f"/api/advisor/conversations/{conversation_id}/messages", json={"text": QUESTION}
    )

    assert response.status_code == 200
    user, assistant = response.json()["messages"]
    assert user["role"] == "user" and user["text"] == QUESTION
    assert assistant["text"] == "Em agosto foram 2 gastos com posto, somando −R$ 185,50."
    assert assistant["provider"] == "anthropic"
    assert assistant["tools"] == ["search_transactions"]
    tool_round = provider.seen[1][-1]
    assert tool_round.role == "tool"
    assert tool_round.parts[0].content["total"] == "−R$ 185,50"
    assert "2026-09-26" in provider.systems[0]
    assert [spec.name for spec in provider.tools[0]] == ["search_transactions", "spending_summary"]
    roles = [row["role"] for row in _stored_roles(conversation_id)]
    assert roles == ["user", "assistant", "tool", "assistant"]


def test_the_conversation_is_kept_and_resent_on_the_next_question(app, client):
    provider = ScriptedProvider(
        script=[
            call("search_transactions", SEARCH),
            answer("Total: −R$ 185,50."),
            answer("O maior foi −R$ 100,00."),
        ]
    )
    _use(app, provider)
    conversation_id = _new_conversation(client)
    client.post(f"/api/advisor/conversations/{conversation_id}/messages", json={"text": QUESTION})

    client.post(
        f"/api/advisor/conversations/{conversation_id}/messages", json={"text": "e o maior?"}
    )
    detail = client.get(f"/api/advisor/conversations/{conversation_id}").json()
    listed = client.get("/api/advisor/conversations").json()["conversations"]

    assert [m["text"] for m in detail["messages"]] == [
        QUESTION,
        "Total: −R$ 185,50.",
        "e o maior?",
        "O maior foi −R$ 100,00.",
    ]
    assert len(provider.seen[2]) == 5
    assert detail["conversation"]["title"] == QUESTION
    assert listed[0]["id"] == conversation_id


def test_an_answer_citing_a_figure_no_tool_returned_is_withheld(app, client):
    _use(
        app,
        ScriptedProvider(
            script=[call("search_transactions", SEARCH), answer("Foram R$ 999,99 em postos.")]
        ),
    )
    conversation_id = _new_conversation(client)

    response = client.post(
        f"/api/advisor/conversations/{conversation_id}/messages", json={"text": QUESTION}
    )

    assert response.json()["messages"][1]["text"] == UNCHECKED
    stored = _stored_roles(conversation_id)[-1]
    assert "999,99" not in stored["content"]


def test_the_tool_loop_stops_after_the_ceiling(app, client):
    provider = ScriptedProvider(
        script=[call("search_transactions", SEARCH, f"c{n}") for n in range(MAX_ROUNDS + 3)]
    )
    _use(app, provider)
    conversation_id = _new_conversation(client)

    response = client.post(
        f"/api/advisor/conversations/{conversation_id}/messages", json={"text": QUESTION}
    )

    assert len(provider.seen) == MAX_ROUNDS
    assert response.json()["messages"][1]["text"] == TOO_LONG


def test_refusal_becomes_a_pt_br_notice(app, client):
    refused = answer("")
    _use(app, ScriptedProvider(script=[Reply(refused.message, "refusal", "m")]))
    conversation_id = _new_conversation(client)

    response = client.post(
        f"/api/advisor/conversations/{conversation_id}/messages", json={"text": QUESTION}
    )

    assert "recusou" in response.json()["messages"][1]["text"]


def test_provider_failure_returns_502_and_stores_nothing(app, client):
    failure = ProviderError("O consultor está indisponível: a chave da Anthropic foi recusada.")
    _use(app, ScriptedProvider(script=[failure]))
    conversation_id = _new_conversation(client)

    response = client.post(
        f"/api/advisor/conversations/{conversation_id}/messages", json={"text": QUESTION}
    )

    assert response.status_code == 502
    assert response.json()["detail"] == str(failure)
    assert _stored_roles(conversation_id) == []


@pytest.mark.parametrize("text", ["   ", "x" * 501])
def test_empty_or_too_long_question_is_refused(app, client, text):
    _use(app, ScriptedProvider(script=[]))
    conversation_id = _new_conversation(client)

    response = client.post(
        f"/api/advisor/conversations/{conversation_id}/messages", json={"text": text}
    )

    assert response.status_code == 422


def test_unknown_conversation_is_404(app, client):
    _use(app, ScriptedProvider(script=[]))

    assert client.get("/api/advisor/conversations/999").status_code == 404
    sent = client.post("/api/advisor/conversations/999/messages", json={"text": QUESTION})
    assert sent.status_code == 404


def test_stored_assistant_turn_keeps_the_provider_raw_blocks(app, client):
    tool_reply = call("search_transactions", SEARCH)
    signed = Reply(
        message=type(tool_reply.message)(
            role="assistant",
            parts=tool_reply.message.parts,
            raw={"provider": "anthropic", "content": [{"type": "thinking", "signature": "s"}]},
        ),
        stop="tool",
        model="m",
    )
    _use(app, ScriptedProvider(script=[signed, answer("Total: −R$ 185,50.")]))
    conversation_id = _new_conversation(client)

    client.post(f"/api/advisor/conversations/{conversation_id}/messages", json={"text": QUESTION})

    stored = json.loads(_stored_roles(conversation_id)[1]["content"])
    assert stored["raw"]["content"][0]["signature"] == "s"


def test_system_prompt_forbids_arithmetic_and_carries_today():
    from datetime import date

    prompt = system_prompt(date(2026, 9, 26), ["Farmácia", "Posto de combustível"])

    assert "2026-09-26" in prompt
    assert "NUNCA CALCULA" in prompt
    assert "português" in prompt


def test_system_prompt_lists_the_panel_categories_and_the_tool_for_each_question(app, client):
    provider = ScriptedProvider(script=[answer("Pergunte sobre seus gastos.")])
    _use(app, provider)
    conversation_id = _new_conversation(client)

    client.post(f"/api/advisor/conversations/{conversation_id}/messages", json={"text": "oi"})

    system = provider.systems[0]
    assert "Farmácia" in system and "Posto de combustível" in system
    assert "spending_summary" in system and "search_transactions" in system


SUMMARY = {"date_from": "2026-08-01", "date_to": "2026-08-31"}


def test_summary_question_answers_with_the_totals_of_each_category(app, client):
    conn = connect()
    conn.execute("UPDATE transactions SET category = 'Gas stations'")
    conn.commit()
    conn.close()
    provider = ScriptedProvider(
        script=[
            call("spending_summary", SUMMARY),
            answer("Em agosto: Posto de combustível −R$ 185,50, gasto total −R$ 185,50."),
        ]
    )
    _use(app, provider)
    conversation_id = _new_conversation(client)

    response = client.post(
        f"/api/advisor/conversations/{conversation_id}/messages",
        json={"text": "quanto gastei por categoria em agosto?"},
    )

    assistant = response.json()["messages"][1]
    assert assistant["text"].startswith("Em agosto: Posto de combustível −R$ 185,50")
    assert assistant["tools"] == ["spending_summary"]
    summary = provider.seen[1][-1].parts[0].content
    assert summary["by_category"] == [
        {
            "category": "Posto de combustível",
            "count": 2,
            "total_cents": -18550,
            "total": "−R$ 185,50",
        }
    ]
    assert summary["months"][0]["month"] == "2026-08"
    assert len(provider.seen) == 2


def test_a_sum_of_categories_the_summary_did_not_return_is_withheld(app, client):
    conn = connect()
    load(conn, [transaction("f1", "2026-08-12", -23.45, descricao="Drogaria")])
    conn.execute("UPDATE transactions SET category = 'Gas stations' WHERE pluggy_id = 'p1'")
    conn.execute("UPDATE transactions SET category = 'Pharmacy' WHERE pluggy_id = 'p2'")
    conn.commit()
    conn.close()
    _use(
        app,
        ScriptedProvider(
            script=[
                call("spending_summary", SUMMARY),
                answer("Posto e farmácia juntos somam −R$ 185,50."),
            ]
        ),
    )
    conversation_id = _new_conversation(client)

    response = client.post(
        f"/api/advisor/conversations/{conversation_id}/messages",
        json={"text": "quanto foi posto mais farmácia?"},
    )

    assert response.json()["messages"][1]["text"] == UNCHECKED
    conn = connect()
    count = conn.execute("SELECT count(*) FROM transactions").fetchone()[0]
    conn.close()
    assert count == 3
