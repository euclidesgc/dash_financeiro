from fastapi import FastAPI

from app.advisor.provider import Message, Reply, TextPart, ToolCall, ToolResult, ToolSpec
from app.advisor.tools import PROPOSE_RECATEGORIZATION, SEARCH_TRANSACTIONS
from app.main import create_app
from app.routers.advisor_chat import get_provider

SEARCH = {"text": "farmacia"}
RECATEGORIZE_CUE = "passe"
TARGET = "Farmácia"


def _answer(result: ToolResult) -> str:
    content = result.content
    if result.is_error:
        return f"Não consegui: {content['error']}"
    if result.name == PROPOSE_RECATEGORIZATION:
        return (
            f"Preparei a mudança de {content['count']} lançamentos para "
            f"{content['target_category']}, somando {content['total']}. Confira no cartão e "
            "clique em Aplicar."
        )
    return f"Encontrei {content['count']} lançamentos com farmácia, somando {content['total']}."


class ScriptedE2eProvider:
    """Offline stand-in for a real model: asks the real tool, then reads its numbers back."""

    name = "anthropic"
    model = "modelo-e2e"

    def reply(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> Reply:
        last = messages[-1]
        if last.role == "user":
            wants_change = RECATEGORIZE_CUE in last.text().casefold()
            name = PROPOSE_RECATEGORIZATION if wants_change else SEARCH_TRANSACTIONS
            arguments = {**SEARCH, "target_category": TARGET} if wants_change else SEARCH
            call = ToolCall(id=f"call-{len(messages)}", name=name, input=arguments)
            return Reply(Message(role="assistant", parts=[call]), stop="tool", model=self.model)
        result = next(part for part in last.parts if isinstance(part, ToolResult))
        return Reply(
            Message(role="assistant", parts=[TextPart(_answer(result))]),
            stop="end",
            model=self.model,
        )


def create_e2e_app() -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_provider] = ScriptedE2eProvider
    return app
