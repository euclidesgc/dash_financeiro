from datetime import date

import httpx
import pytest

from app.advisor.context import as_text, snapshot
from app.advisor.gaps import SETTLEMENT, dismiss, next_question, pending
from app.advisor.gemini import INSTRUCTION, AdvisorUnavailableError, ask
from tests.test_plan import REFERENCE, prepare, rent, salary


def base(conn):
    return prepare(conn, salary(5000.0) + rent(-1000.0))


def fact(conn, name, valid_until=None):
    conn.execute(
        "INSERT OR REPLACE INTO plan_facts "
        "(name, label, value, unit, source, captured_at, valid_until) "
        "VALUES (?, ?, 100, 'centavos', 'humano', '2026-01-01', ?)",
        (name, name, valid_until),
    )
    conn.commit()


def test_the_advisor_asks_one_question_at_a_time(taxonomy_conn):
    conn = base(taxonomy_conn)
    found = next_question(conn, today=REFERENCE)

    assert found is not None
    assert isinstance(found, dict)
    assert found["name"] == pending(conn, today=REFERENCE)[0]["name"]


def test_an_answered_fact_is_never_asked_again(taxonomy_conn):
    conn = base(taxonomy_conn)
    fact(conn, SETTLEMENT)

    assert SETTLEMENT not in [item["name"] for item in pending(conn, today=REFERENCE)]


def test_an_expired_fact_comes_back(taxonomy_conn):
    conn = base(taxonomy_conn)
    fact(conn, SETTLEMENT, valid_until="2026-08-01")

    assert SETTLEMENT in [item["name"] for item in pending(conn, today=REFERENCE)]


def test_a_dismissed_question_disappears_and_the_advisor_does_not_insist(taxonomy_conn):
    conn = base(taxonomy_conn)
    first = next_question(conn, today=REFERENCE)
    dismiss(conn, first["name"])
    after = next_question(conn, today=REFERENCE)

    assert after is None or after["name"] != first["name"]


def test_a_dismissed_question_returns_when_the_fact_expires(taxonomy_conn):
    conn = base(taxonomy_conn)
    fact(conn, SETTLEMENT, valid_until="2026-08-01")
    dismiss(conn, SETTLEMENT)

    assert SETTLEMENT in [item["name"] for item in pending(conn, today=REFERENCE)]


def test_the_context_carries_every_number_the_model_may_say(taxonomy_conn):
    conn = base(taxonomy_conn)
    numbers = snapshot(conn, today=REFERENCE)
    text = as_text(numbers)

    for key in ("consolidated", "committed", "monthly_result", "reserve_target"):
        assert key in numbers
    assert "Resultado mensal:" in text
    assert "Reserva alvo:" in text
    assert numbers["reference"] == REFERENCE.isoformat()


def test_the_instruction_forbids_the_model_from_calculating():
    assert "NUNCA CALCULA" in INSTRUCTION
    assert "copiado dígito a dígito" in INSTRUCTION


def test_without_a_key_the_advisor_says_the_numbers_do_not_depend_on_it():
    with pytest.raises(AdvisorUnavailableError) as refusal:
        ask("e daí?", "contexto", api_key=None)

    assert "GEMINI_API_KEY" in str(refusal.value)
    assert "não dependem dela" in str(refusal.value)


def test_a_network_failure_degrades_instead_of_breaking(monkeypatch):
    def explode(*args, **kwargs):
        raise httpx.ConnectError("sem rede")

    monkeypatch.setattr(httpx, "post", explode)

    with pytest.raises(AdvisorUnavailableError) as refusal:
        ask("e daí?", "contexto", api_key="chave")

    assert "indisponível" in str(refusal.value)


def test_an_empty_answer_is_treated_as_unavailable(monkeypatch):
    class Answer:
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "   "}]}}]}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: Answer())

    with pytest.raises(AdvisorUnavailableError):
        ask("e daí?", "contexto", api_key="chave")


def test_the_reading_comes_back_when_the_model_answers(monkeypatch):
    class Answer:
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "O pior ponto é em outubro."}]}}]}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: Answer())
    found = ask("por quê?", "contexto", api_key="chave")

    assert found.text == "O pior ponto é em outubro."
    assert found.model


def test_the_snapshot_never_calls_the_model(taxonomy_conn, monkeypatch):
    def explode(*args, **kwargs):
        raise AssertionError("o modelo foi chamado para produzir número")

    monkeypatch.setattr(httpx, "post", explode)
    conn = base(taxonomy_conn)

    assert snapshot(conn, today=date(2026, 9, 5))["consolidated"] is not None


def test_the_screen_shows_every_line_the_model_receives(taxonomy_conn):
    from app.advisor.context import lines

    conn = base(taxonomy_conn)
    numbers = snapshot(conn, today=REFERENCE)
    shown = lines(numbers)
    text = as_text(numbers)

    assert len(shown) == len(text.splitlines())
    for line in shown:
        assert f"{line['label']}: {line['value']}." in text


def test_a_question_that_is_not_in_the_catalogue_is_refused(taxonomy_conn):
    from app.advisor.gaps import UnknownQuestionError

    with pytest.raises(UnknownQuestionError):
        dismiss(taxonomy_conn, "x" * 5000)
    with pytest.raises(UnknownQuestionError):
        dismiss(taxonomy_conn, "<script>alert(1)</script>")

    assert taxonomy_conn.execute("SELECT COUNT(*) FROM advisor_questions").fetchone()[0] == 0


def test_postponing_everything_is_not_the_same_as_answering_everything(taxonomy_conn):
    from app.advisor.gaps import WANTED, postponed

    conn = base(taxonomy_conn)
    for wanted in WANTED:
        dismiss(conn, wanted["name"])

    assert next_question(conn, today=REFERENCE) is None
    assert postponed(conn) == len(WANTED)


def test_the_refusal_of_the_provider_is_said_in_portuguese(monkeypatch):
    class Answer:
        status_code = 401

        def raise_for_status(self):
            raise httpx.HTTPStatusError("401", request=None, response=self)

    monkeypatch.setattr(httpx, "post", lambda *a, **k: Answer())

    with pytest.raises(AdvisorUnavailableError) as refusal:
        ask("e daí?", "contexto", api_key="chave-errada")

    assert "chave foi recusada" in str(refusal.value)
    assert "HTTPStatusError" not in str(refusal.value)


def test_a_timeout_is_said_in_portuguese(monkeypatch):
    def slow(*args, **kwargs):
        raise httpx.ReadTimeout("demorou")

    monkeypatch.setattr(httpx, "post", slow)

    with pytest.raises(AdvisorUnavailableError) as refusal:
        ask("e daí?", "contexto", api_key="chave")

    assert "demorou demais" in str(refusal.value)
