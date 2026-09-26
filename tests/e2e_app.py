from fastapi import FastAPI

from app.advisor.provider import Message, Reply, TextPart, ToolCall, ToolResult, ToolSpec
from app.main import create_app
from app.routers.advisor_chat import get_provider

SEARCH = {"text": "farmacia"}


class ScriptedE2eProvider:
    """Offline stand-in for a real model: asks the real tool, then reads its numbers back."""

    name = "anthropic"
    model = "modelo-e2e"

    def reply(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> Reply:
        last = messages[-1]
        if last.role == "user":
            call = ToolCall(id=f"call-{len(messages)}", name="search_transactions", input=SEARCH)
            return Reply(Message(role="assistant", parts=[call]), stop="tool", model=self.model)
        result = next(part for part in last.parts if isinstance(part, ToolResult))
        text = (
            f"Encontrei {result.content['count']} lançamentos com farmácia, "
            f"somando {result.content['total']}."
        )
        return Reply(
            Message(role="assistant", parts=[TextPart(text)]), stop="end", model=self.model
        )


def create_e2e_app() -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_provider] = ScriptedE2eProvider
    return app
