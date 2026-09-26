import json
import math
import re
import uuid
from typing import Any

import httpx

from app.advisor.provider import (
    Message,
    Part,
    ProviderError,
    Reply,
    Stop,
    TextPart,
    ToolCall,
    ToolSpec,
)

NAME = "gemini"
# Decision: not the model list of the old /consultor screen — every 2.5 model
# on it answers 404 "no longer available to new users" (measured 26/09/2026),
# so the chat keeps its own default, overridable by DASH_ADVISOR_GEMINI_MODEL.
DEFAULT_MODEL = "gemini-3.8-flash"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT_SECONDS = 60.0
UNAUTHORISED = (401, 403)
BAD_REQUEST = 400
NOT_FOUND = 404
TOO_MANY = 429
OVERLOADED = 503

_STOPS: dict[str, Stop] = {
    "STOP": "end",
    "MAX_TOKENS": "truncated",
    "SAFETY": "refusal",
    "RECITATION": "refusal",
    "PROHIBITED_CONTENT": "refusal",
    "BLOCKLIST": "refusal",
    "SPII": "refusal",
}


def _unavailable(reason: str) -> ProviderError:
    return ProviderError(f"O consultor está indisponível: {reason}.")


_DELAY = re.compile(r"^(\d+(?:\.\d+)?)s$")
DAILY_QUOTA = "PerDay"


def _details(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        details = response.json()["error"]["details"]
    except (KeyError, TypeError, ValueError):
        return []
    return [item for item in details if isinstance(item, dict)] if isinstance(details, list) else []


def _too_many(response: httpx.Response) -> str:
    details = _details(response)
    quotas = [
        str(violation.get("quotaId", ""))
        for item in details
        for violation in item.get("violations") or []
        if isinstance(violation, dict)
    ]
    if any(DAILY_QUOTA in quota for quota in quotas):
        return "a cota diária do Gemini acabou; tente amanhã ou configure ANTHROPIC_API_KEY no .env"
    for item in details:
        found = _DELAY.match(str(item.get("retryDelay", "")))
        if found:
            seconds = max(1, math.ceil(float(found.group(1))))
            return f"excesso de chamadas ao Gemini; tente de novo em {seconds} segundos"
    return "excesso de chamadas ao Gemini; tente daqui a pouco"


def _refused(status: int, model: str) -> str:
    if status == NOT_FOUND:
        return f"o modelo {model} não está disponível no Gemini; confira DASH_ADVISOR_GEMINI_MODEL"
    if status in UNAUTHORISED:
        return "a chave do Gemini foi recusada; confira GEMINI_API_KEY ou a tela Configuração"
    if status == BAD_REQUEST:
        return "o Gemini recusou o pedido (a chave pode ser inválida)"
    if status == OVERLOADED:
        return "o Gemini está sobrecarregado; tente daqui a pouco"
    return f"o Gemini respondeu com erro (HTTP {status})"


def _neutral_part(part: Part) -> dict[str, Any]:
    if isinstance(part, TextPart):
        return {"text": part.text}
    if isinstance(part, ToolCall):
        return {"functionCall": {"name": part.name, "args": part.input}}
    return {"functionResponse": {"name": part.name, "response": part.content}}


def to_wire(messages: list[Message]) -> list[dict[str, Any]]:
    wire: list[dict[str, Any]] = []
    for message in messages:
        if message.role == "assistant":
            if message.raw is not None and message.raw.get("provider") == NAME:
                wire.append(dict(message.raw["content"]))
            else:
                wire.append({"role": "model", "parts": [_neutral_part(p) for p in message.parts]})
        else:
            wire.append({"role": "user", "parts": [_neutral_part(p) for p in message.parts]})
    return wire


def from_wire(content: dict[str, Any]) -> Message:
    parts: list[Part] = []
    for part in content.get("parts", []):
        if part.get("thought"):
            continue
        if "text" in part:
            parts.append(TextPart(text=str(part["text"])))
        elif "functionCall" in part:
            call = part["functionCall"]
            call_id = str(call.get("id") or f"call_{uuid.uuid4().hex[:12]}")
            arguments = dict(call.get("args") or {})
            parts.append(ToolCall(id=call_id, name=str(call["name"]), input=arguments))
    raw = {"provider": NAME, "content": {"role": "model", "parts": content.get("parts", [])}}
    return Message(role="assistant", parts=parts, raw=raw)


def _tool(spec: ToolSpec) -> dict[str, Any]:
    return {"name": spec.name, "description": spec.description, "parameters": spec.parameters}


class GeminiProvider:
    name = NAME

    def __init__(self, *, api_key: str, model: str, client: httpx.Client | None = None) -> None:
        self.model = model
        self._api_key = api_key
        self._client = client or httpx.Client(timeout=TIMEOUT_SECONDS)

    def reply(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> Reply:
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": to_wire(messages),
            "tools": [{"functionDeclarations": [_tool(spec) for spec in tools]}],
        }
        try:
            answer = self._client.post(
                ENDPOINT.format(model=self.model),
                headers={"x-goog-api-key": self._api_key},
                json=body,
            )
            answer.raise_for_status()
            payload = answer.json()
            candidate = payload["candidates"][0]
            message = from_wire(candidate.get("content") or {})
            reason = str(candidate.get("finishReason", "STOP"))
        except httpx.TimeoutException:
            raise _unavailable("o Gemini demorou demais para responder") from None
        except httpx.HTTPStatusError as failure:
            if failure.response.status_code == TOO_MANY:
                raise _unavailable(_too_many(failure.response)) from None
            raise _unavailable(_refused(failure.response.status_code, self.model)) from None
        except httpx.HTTPError:
            raise _unavailable("não foi possível alcançar o Gemini") from None
        except UnicodeEncodeError:
            # Reason: httpx encodes a str header as ascii, so a key from the
            # environment with a stray accented byte fails here, not on the wire.
            raise _unavailable(
                "a chave do Gemini tem um caractere que o cabeçalho não aceita"
            ) from None
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
            raise _unavailable("o Gemini respondeu num formato inesperado") from None
        usage = payload.get("usageMetadata") or {}
        stop: Stop = "tool" if message.calls() else _STOPS.get(reason, "end")
        return Reply(
            message=message,
            stop=stop,
            model=str(payload.get("modelVersion") or self.model),
            input_tokens=int(usage.get("promptTokenCount", 0)),
            output_tokens=int(usage.get("candidatesTokenCount", 0)),
        )
