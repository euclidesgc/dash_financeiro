import json

import anthropic
import httpx
import pytest
from anthropic.types import Message as SdkMessage

from app.advisor import anthropic_provider, gemini_provider
from app.advisor.anthropic_provider import AnthropicProvider
from app.advisor.config import save
from app.advisor.gemini_provider import GeminiProvider
from app.advisor.provider import Message, ProviderError, TextPart, ToolCall, ToolResult
from app.advisor.providers import select_provider
from app.advisor.tools import TOOLS
from app.config import load_config

QUESTION = Message(role="user", parts=[TextPart("gastos com posto em agosto?")])
CALL = ToolCall(id="toolu_1", name="search_transactions", input={"text": "posto"})
RESULT = ToolResult(call_id="toolu_1", name="search_transactions", content={"total": "−R$ 1,00"})


def _sdk_message(content, stop_reason):
    return SdkMessage.model_validate(
        {
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "model": "claude-opus-5",
            "content": content,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {"input_tokens": 12, "output_tokens": 7},
        }
    )


class FakeCreate:
    def __init__(self, outcome):
        self.outcome = outcome
        self.kwargs = []

    def __call__(self, **kwargs):
        self.kwargs.append(kwargs)
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


def _bare(error_class):
    # Reason: the SDK error constructors demand a live HTTP response object;
    # the adapter only branches on the class, so an instance without one is
    # enough to prove the translation.
    return error_class.__new__(error_class)


def test_anthropic_translates_a_tool_request_and_keeps_raw_blocks():
    create = FakeCreate(
        _sdk_message(
            [
                {"type": "thinking", "thinking": "", "signature": "sig-1"},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "search_transactions",
                    "input": {"text": "posto"},
                },
            ],
            "tool_use",
        )
    )
    provider = AnthropicProvider(api_key="k", model="claude-opus-5", create=create)

    reply = provider.reply("sistema", [QUESTION], TOOLS)

    assert reply.stop == "tool"
    assert reply.message.calls() == [CALL]
    assert reply.message.raw["content"][0]["signature"] == "sig-1"
    assert (reply.input_tokens, reply.output_tokens) == (12, 7)
    sent = create.kwargs[0]
    assert sent["model"] == "claude-opus-5"
    assert sent["system"] == "sistema"
    assert [tool["name"] for tool in sent["tools"]] == ["search_transactions", "spending_summary"]
    assert all("input_schema" in tool for tool in sent["tools"])
    assert sent["thinking"] == {"type": "adaptive"}


def test_anthropic_resends_own_raw_blocks_and_tool_results_in_one_user_message():
    own = Message(
        role="assistant",
        parts=[CALL],
        raw={"provider": "anthropic", "content": [{"type": "thinking", "signature": "s"}]},
    )
    foreign = Message(role="assistant", parts=[TextPart("oi")], raw={"provider": "gemini"})
    results = Message(role="tool", parts=[RESULT])

    wire = anthropic_provider.to_wire([QUESTION, own, results, foreign])

    assert wire[1] == {"role": "assistant", "content": [{"type": "thinking", "signature": "s"}]}
    assert wire[2]["role"] == "user"
    block = wire[2]["content"][0]
    assert block["type"] == "tool_result" and block["tool_use_id"] == "toolu_1"
    assert json.loads(block["content"]) == {"total": "−R$ 1,00"}
    assert wire[3] == {"role": "assistant", "content": [{"type": "text", "text": "oi"}]}


@pytest.mark.parametrize(
    ("stop_reason", "stop"),
    [("end_turn", "end"), ("refusal", "refusal"), ("max_tokens", "truncated")],
)
def test_anthropic_maps_stop_reasons(stop_reason, stop):
    create = FakeCreate(_sdk_message([{"type": "text", "text": "ok"}], stop_reason))

    reply = AnthropicProvider(api_key="k", model="m", create=create).reply("s", [QUESTION], [])

    assert reply.stop == stop


@pytest.mark.parametrize(
    ("error_class", "fragment"),
    [
        (anthropic.AuthenticationError, "chave da Anthropic foi recusada"),
        (anthropic.PermissionDeniedError, "chave da Anthropic foi recusada"),
        (anthropic.RateLimitError, "excesso de chamadas"),
        (anthropic.NotFoundError, "DASH_ADVISOR_MODEL"),
        (anthropic.APIConnectionError, "não foi possível alcançar"),
        (anthropic.InternalServerError, "respondeu com erro"),
    ],
)
def test_anthropic_errors_become_pt_br(error_class, fragment):
    provider = AnthropicProvider(api_key="k", model="m", create=FakeCreate(_bare(error_class)))

    with pytest.raises(ProviderError, match=fragment):
        provider.reply("s", [QUESTION], [])


def _gemini(handler):
    seen = []

    def transport(request):
        seen.append(request)
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(transport))
    return GeminiProvider(api_key="chave", model="gemini-2.5-flash", client=client), seen


def _candidate(parts, reason="STOP"):
    return {
        "candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": reason}],
        "usageMetadata": {"promptTokenCount": 30, "candidatesTokenCount": 4},
        "modelVersion": "gemini-2.5-flash",
    }


def test_gemini_translates_a_function_call_and_keeps_the_signature():
    body = _candidate(
        [
            {
                "functionCall": {"name": "search_transactions", "args": {"text": "posto"}},
                "thoughtSignature": "sig",
            }
        ]
    )
    provider, seen = _gemini(lambda request: httpx.Response(200, json=body))

    reply = provider.reply("sistema", [QUESTION], TOOLS)

    assert reply.stop == "tool"
    [call] = reply.message.calls()
    assert (call.name, call.input) == ("search_transactions", {"text": "posto"})
    assert reply.message.raw["content"]["parts"][0]["thoughtSignature"] == "sig"
    sent = json.loads(seen[0].content)
    assert seen[0].headers["x-goog-api-key"] == "chave"
    assert "gemini-2.5-flash:generateContent" in str(seen[0].url)
    assert sent["systemInstruction"]["parts"][0]["text"] == "sistema"
    declarations = sent["tools"][0]["functionDeclarations"]
    assert [item["name"] for item in declarations] == ["search_transactions", "spending_summary"]
    assert all(item["parameters"]["type"] == "object" for item in declarations)


def test_gemini_rebuilds_function_response_and_resends_own_raw_turn():
    own = Message(
        role="assistant",
        parts=[CALL],
        raw={"provider": "gemini", "content": {"role": "model", "parts": [{"x": 1}]}},
    )

    wire = gemini_provider.to_wire([QUESTION, own, Message(role="tool", parts=[RESULT])])

    assert wire[1] == {"role": "model", "parts": [{"x": 1}]}
    assert wire[2] == {
        "role": "user",
        "parts": [
            {"functionResponse": {"name": "search_transactions", "response": {"total": "−R$ 1,00"}}}
        ],
    }


def test_gemini_text_answer_ends_the_turn_and_skips_thoughts():
    body = _candidate([{"text": "pensando", "thought": True}, {"text": "Resposta."}])
    provider, _ = _gemini(lambda request: httpx.Response(200, json=body))

    reply = provider.reply("s", [QUESTION], TOOLS)

    assert reply.stop == "end"
    assert reply.message.text() == "Resposta."
    assert (reply.input_tokens, reply.output_tokens) == (30, 4)


@pytest.mark.parametrize(
    ("status", "fragment"),
    [
        (403, "chave do Gemini foi recusada"),
        (404, "gemini-2.5-flash não está disponível"),
        (429, "excesso de chamadas"),
        (503, "sobrecarregado"),
        (500, r"com erro \(HTTP 500\)"),
    ],
)
def test_gemini_http_errors_become_pt_br(status, fragment):
    provider, _ = _gemini(lambda request: httpx.Response(status, json={}))

    with pytest.raises(ProviderError, match=fragment):
        provider.reply("s", [QUESTION], TOOLS)


def _exhausted(*details):
    return {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "details": list(details)}}


RETRY = {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "32.4s"}


def _quota(quota_id):
    return {
        "@type": "type.googleapis.com/google.rpc.QuotaFailure",
        "violations": [{"quotaMetric": "generate_content_requests", "quotaId": quota_id}],
    }


@pytest.mark.parametrize(
    ("body", "fragment"),
    [
        (
            _exhausted(_quota("GenerateRequestsPerMinutePerProjectPerModel-FreeTier"), RETRY),
            "tente de novo em 33 segundos",
        ),
        (
            _exhausted(_quota("GenerateRequestsPerDayPerProjectPerModel-FreeTier"), RETRY),
            "cota diária do Gemini acabou; tente amanhã",
        ),
        (_exhausted(), "excesso de chamadas ao Gemini; tente daqui a pouco"),
        ({"error": "texto"}, "excesso de chamadas ao Gemini; tente daqui a pouco"),
    ],
)
def test_gemini_rate_limit_says_how_long_to_wait_or_that_the_day_is_over(body, fragment):
    provider, _ = _gemini(lambda request: httpx.Response(429, json=body))

    with pytest.raises(ProviderError, match=fragment):
        provider.reply("s", [QUESTION], TOOLS)


def test_gemini_rate_limit_with_a_body_that_is_not_json_keeps_the_generic_text():
    provider, _ = _gemini(lambda request: httpx.Response(429, text="Too Many Requests"))

    with pytest.raises(ProviderError, match="excesso de chamadas ao Gemini; tente daqui a pouco"):
        provider.reply("s", [QUESTION], TOOLS)


def test_gemini_unreachable_and_malformed_become_pt_br():
    def down(request):
        raise httpx.ConnectError("sem rede", request=request)

    unreachable, _ = _gemini(down)
    malformed, _ = _gemini(lambda request: httpx.Response(200, json={"candidates": []}))

    with pytest.raises(ProviderError, match="alcançar o Gemini"):
        unreachable.reply("s", [QUESTION], TOOLS)
    with pytest.raises(ProviderError, match="formato inesperado"):
        malformed.reply("s", [QUESTION], TOOLS)


def test_selection_prefers_anthropic_then_gemini_then_none(taxonomy_conn, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    both = load_config({"ANTHROPIC_API_KEY": "a", "DASH_ADVISOR_MODEL": "claude-sonnet-5"})
    none = load_config({})

    chosen = select_provider(taxonomy_conn, both)
    absent = select_provider(taxonomy_conn, none)
    save(taxonomy_conn, api_key="chave-da-tela", model="gemini-2.5-pro")
    gemini = select_provider(taxonomy_conn, none)
    pinned = select_provider(taxonomy_conn, load_config({"DASH_ADVISOR_GEMINI_MODEL": "g-x"}))

    assert (chosen.name, chosen.model) == ("anthropic", "claude-sonnet-5")
    assert absent is None
    assert (gemini.name, gemini.model) == ("gemini", "gemini-3.8-flash")
    assert pinned.model == "g-x"


def test_anthropic_model_defaults_to_current_opus(taxonomy_conn):
    chosen = select_provider(taxonomy_conn, load_config({"ANTHROPIC_API_KEY": "a"}))

    assert chosen.model == "claude-opus-5"
