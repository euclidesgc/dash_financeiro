import json
from collections.abc import Callable
from typing import Any, cast

import anthropic
from anthropic.types import Message as SdkMessage

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

NAME = "anthropic"
DEFAULT_MODEL = "claude-opus-5"
MAX_TOKENS = 16000
TIMEOUT_SECONDS = 90.0
# Reason: a chat answer over a handful of tool results does not repay the
# default effort; medium keeps latency down without thinking turned off, which
# on this model family can write a tool call into the visible text instead of
# a tool_use block.
EFFORT = "medium"

Create = Callable[..., SdkMessage]

_STOPS: dict[str, Stop] = {
    "end_turn": "end",
    "stop_sequence": "end",
    "tool_use": "tool",
    "refusal": "refusal",
    "max_tokens": "truncated",
    "pause_turn": "truncated",
}


def _unavailable(reason: str) -> ProviderError:
    return ProviderError(f"O consultor está indisponível: {reason}.")


def _tool(spec: ToolSpec) -> dict[str, Any]:
    return {"name": spec.name, "description": spec.description, "input_schema": spec.parameters}


def _neutral_block(part: Part) -> dict[str, Any]:
    if isinstance(part, TextPart):
        return {"type": "text", "text": part.text}
    if isinstance(part, ToolCall):
        return {"type": "tool_use", "id": part.id, "name": part.name, "input": part.input}
    return {
        "type": "tool_result",
        "tool_use_id": part.call_id,
        "content": json.dumps(part.content, ensure_ascii=False),
        "is_error": part.is_error,
    }


def to_wire(messages: list[Message]) -> list[dict[str, Any]]:
    wire: list[dict[str, Any]] = []
    for message in messages:
        if message.role == "assistant":
            if message.raw is not None and message.raw.get("provider") == NAME:
                content = list(message.raw["content"])
            else:
                content = [_neutral_block(part) for part in message.parts]
            wire.append({"role": "assistant", "content": content})
        else:
            wire.append({"role": "user", "content": [_neutral_block(p) for p in message.parts]})
    return wire


def from_wire(response: SdkMessage) -> Message:
    parts: list[Part] = []
    for block in response.content:
        if block.type == "text":
            parts.append(TextPart(text=block.text))
        elif block.type == "tool_use":
            parts.append(ToolCall(id=block.id, name=block.name, input=dict(block.input)))
    raw = {"provider": NAME, "content": [block.to_dict() for block in response.content]}
    return Message(role="assistant", parts=parts, raw=raw)


class AnthropicProvider:
    name = NAME

    def __init__(self, *, api_key: str, model: str, create: Create | None = None) -> None:
        self.model = model
        if create is None:
            client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SECONDS)
            create = cast(Create, client.messages.create)
        self._create = create

    def reply(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> Reply:
        try:
            response = self._create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=to_wire(messages),
                tools=[_tool(spec) for spec in tools],
                thinking={"type": "adaptive"},
                output_config={"effort": EFFORT},
            )
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError):
            raise _unavailable(
                "a chave da Anthropic foi recusada; confira ANTHROPIC_API_KEY"
            ) from None
        except anthropic.RateLimitError:
            raise _unavailable("excesso de chamadas à Anthropic; tente daqui a pouco") from None
        except anthropic.NotFoundError:
            raise _unavailable(
                f"o modelo {self.model} não foi encontrado; confira DASH_ADVISOR_MODEL"
            ) from None
        except anthropic.APIConnectionError:
            raise _unavailable("não foi possível alcançar a Anthropic") from None
        except anthropic.APIStatusError:
            raise _unavailable("a Anthropic respondeu com erro") from None
        return Reply(
            message=from_wire(response),
            stop=_STOPS.get(response.stop_reason or "", "end"),
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
