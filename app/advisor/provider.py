from dataclasses import dataclass
from typing import Any, Literal, Protocol

Role = Literal["user", "assistant", "tool"]
Stop = Literal["end", "tool", "refusal", "truncated"]


@dataclass(frozen=True)
class TextPart:
    text: str


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    name: str
    content: dict[str, Any]
    is_error: bool = False


Part = TextPart | ToolCall | ToolResult


@dataclass(frozen=True)
class Message:
    role: Role
    parts: list[Part]
    # Reason: a provider may attach opaque data to its own turn (Anthropic
    # thinking signatures, Gemini thought signatures) that must travel back
    # unchanged on the next request to that same provider; any other provider
    # rebuilds the turn from the neutral parts.
    raw: dict[str, Any] | None = None

    def text(self) -> str:
        return "".join(part.text for part in self.parts if isinstance(part, TextPart)).strip()

    def calls(self) -> list[ToolCall]:
        return [part for part in self.parts if isinstance(part, ToolCall)]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class Reply:
    message: Message
    stop: Stop
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class ProviderError(RuntimeError):
    pass


class ChatProvider(Protocol):
    name: str
    model: str

    def reply(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> Reply: ...


def part_to_json(part: Part) -> dict[str, Any]:
    if isinstance(part, TextPart):
        return {"type": "text", "text": part.text}
    if isinstance(part, ToolCall):
        return {"type": "tool_call", "id": part.id, "name": part.name, "input": part.input}
    return {
        "type": "tool_result",
        "call_id": part.call_id,
        "name": part.name,
        "content": part.content,
        "is_error": part.is_error,
    }


def part_from_json(data: dict[str, Any]) -> Part:
    kind = data["type"]
    if kind == "text":
        return TextPart(text=str(data["text"]))
    if kind == "tool_call":
        return ToolCall(id=str(data["id"]), name=str(data["name"]), input=dict(data["input"]))
    return ToolResult(
        call_id=str(data["call_id"]),
        name=str(data["name"]),
        content=dict(data["content"]),
        is_error=bool(data.get("is_error", False)),
    )
