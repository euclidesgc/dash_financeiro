from dataclasses import dataclass, field

from app.advisor.provider import Message, ProviderError, Reply, TextPart, ToolCall, ToolSpec


@dataclass
class ScriptedProvider:
    """Hand-written double of the ChatProvider port: answers from a script."""

    script: list[Reply | ProviderError]
    name: str = "anthropic"
    model: str = "modelo-de-teste"
    seen: list[list[Message]] = field(default_factory=list)
    systems: list[str] = field(default_factory=list)
    tools: list[list[ToolSpec]] = field(default_factory=list)

    def reply(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> Reply:
        self.seen.append(list(messages))
        self.systems.append(system)
        self.tools.append(tools)
        step = self.script.pop(0)
        if isinstance(step, ProviderError):
            raise step
        return step


def call(name: str, arguments: dict[str, object], call_id: str = "call-1") -> Reply:
    message = Message(role="assistant", parts=[ToolCall(id=call_id, name=name, input=arguments)])
    return Reply(message=message, stop="tool", model="modelo-de-teste", input_tokens=10)


def answer(text: str) -> Reply:
    message = Message(role="assistant", parts=[TextPart(text)])
    return Reply(message=message, stop="end", model="modelo-de-teste", output_tokens=5)
