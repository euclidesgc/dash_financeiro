from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.advisor.chat import (
    ChatEntry,
    InvalidQuestionError,
    UnknownConversationError,
    create_conversation,
    send,
    view,
)
from app.advisor.provider import ChatProvider, ProviderError
from app.advisor.providers import MISSING_KEY, select_provider
from app.config import reference_date
from app.db import connect
from app.queries.advisor_chat import ConversationRow, list_conversations
from app.routers.row_id import RowId

router = APIRouter(prefix="/api/advisor")

RECENT = 20
# Reason: the service holds the real ceiling (MAX_QUESTION) and answers it in
# pt-BR; this bound only keeps an absurd body from reaching it.
BODY_CEILING = 5000
UNKNOWN_CONVERSATION = "Conversa não encontrada."


class Status(BaseModel):
    available: bool
    provider: Literal["anthropic", "gemini"] | None
    model: str | None
    message: str | None


class Conversation(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str


class ConversationsResponse(BaseModel):
    conversations: list[Conversation]


class Entry(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    text: str
    created_at: str
    provider: str | None
    tools: list[str]


class ConversationDetail(BaseModel):
    conversation: Conversation
    messages: list[Entry]


class MessagesResponse(BaseModel):
    messages: list[Entry]


class Question(BaseModel):
    text: str = Field(max_length=BODY_CEILING)


def get_provider() -> ChatProvider | None:
    conn = connect()
    try:
        return select_provider(conn)
    finally:
        conn.close()


def require_provider(
    provider: Annotated[ChatProvider | None, Depends(get_provider)],
) -> ChatProvider:
    if provider is None:
        raise HTTPException(status_code=503, detail=MISSING_KEY)
    return provider


def _conversation(row: ConversationRow) -> Conversation:
    return Conversation(
        id=row.id, title=row.title, created_at=row.created_at, updated_at=row.updated_at
    )


def _entry(entry: ChatEntry) -> Entry:
    return Entry(
        id=entry.id,
        role="user" if entry.role == "user" else "assistant",
        text=entry.text,
        created_at=entry.created_at,
        provider=entry.provider,
        tools=entry.tools,
    )


@contextmanager
def _translated() -> Iterator[None]:
    try:
        yield
    except UnknownConversationError as error:
        raise HTTPException(status_code=404, detail=UNKNOWN_CONVERSATION) from error
    except InvalidQuestionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.get("/status")
def status(provider: Annotated[ChatProvider | None, Depends(get_provider)]) -> Status:
    if provider is None:
        return Status(available=False, provider=None, model=None, message=MISSING_KEY)
    name: Literal["anthropic", "gemini"] = "anthropic" if provider.name == "anthropic" else "gemini"
    return Status(available=True, provider=name, model=provider.model, message=None)


@router.get("/conversations")
def conversations() -> ConversationsResponse:
    conn = connect()
    try:
        rows = list_conversations(conn, RECENT)
    finally:
        conn.close()
    return ConversationsResponse(conversations=[_conversation(row) for row in rows])


@router.post("/conversations", status_code=201)
def start_conversation() -> Conversation:
    conn = connect()
    try:
        row = create_conversation(conn)
    finally:
        conn.close()
    return _conversation(row)


@router.get("/conversations/{conversation_id}")
def conversation(conversation_id: RowId) -> ConversationDetail:
    conn = connect()
    try:
        with _translated():
            found = view(conn, conversation_id)
    finally:
        conn.close()
    return ConversationDetail(
        conversation=_conversation(found.conversation),
        messages=[_entry(entry) for entry in found.entries],
    )


@router.post("/conversations/{conversation_id}/messages")
def ask(
    conversation_id: RowId,
    body: Question,
    provider: Annotated[ChatProvider, Depends(require_provider)],
) -> MessagesResponse:
    conn = connect()
    try:
        with _translated():
            added = send(
                conn,
                provider,
                conversation_id,
                body.text,
                today=reference_date(),
            )
    finally:
        conn.close()
    return MessagesResponse(messages=[_entry(entry) for entry in added])
