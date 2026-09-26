import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from app.advisor.provider import Message, Role, part_from_json, part_to_json


@dataclass(frozen=True)
class ConversationRow:
    id: int
    title: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class StoredMessage:
    id: int
    position: int
    message: Message
    provider: str | None
    model: str | None
    created_at: str


@dataclass(frozen=True)
class NewMessage:
    message: Message
    provider: str | None = None
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


_CONVERSATION = "SELECT id, title, created_at, updated_at FROM advisor_conversations"
_MESSAGES = (
    "SELECT id, position, role, content, provider, model, created_at FROM advisor_messages "
    "WHERE conversation_id = ? ORDER BY position"
)


def _conversation(row: sqlite3.Row) -> ConversationRow:
    return ConversationRow(
        id=row["id"], title=row["title"], created_at=row["created_at"], updated_at=row["updated_at"]
    )


def insert_conversation(conn: sqlite3.Connection, title: str, now: str) -> int:
    cursor = conn.execute(
        "INSERT INTO advisor_conversations (title, created_at, updated_at) VALUES (?, ?, ?)",
        (title, now, now),
    )
    return int(cursor.lastrowid or 0)


def get_conversation(conn: sqlite3.Connection, conversation_id: int) -> ConversationRow | None:
    row = conn.execute(f"{_CONVERSATION} WHERE id = ?", (conversation_id,)).fetchone()
    return None if row is None else _conversation(row)


def list_conversations(conn: sqlite3.Connection, limit: int) -> list[ConversationRow]:
    rows = conn.execute(
        f"{_CONVERSATION} ORDER BY updated_at DESC, id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [_conversation(row) for row in rows]


def rename_conversation(conn: sqlite3.Connection, conversation_id: int, title: str) -> None:
    conn.execute(
        "UPDATE advisor_conversations SET title = ? WHERE id = ?", (title, conversation_id)
    )


def _encode(message: Message) -> str:
    body: dict[str, Any] = {"parts": [part_to_json(part) for part in message.parts]}
    if message.raw is not None:
        body["raw"] = message.raw
    return json.dumps(body, ensure_ascii=False)


def _decode(role: Role, content: str) -> Message:
    body = json.loads(content)
    return Message(
        role=role,
        parts=[part_from_json(part) for part in body["parts"]],
        raw=body.get("raw"),
    )


def list_messages(conn: sqlite3.Connection, conversation_id: int) -> list[StoredMessage]:
    rows = conn.execute(_MESSAGES, (conversation_id,)).fetchall()
    return [
        StoredMessage(
            id=row["id"],
            position=row["position"],
            message=_decode(row["role"], row["content"]),
            provider=row["provider"],
            model=row["model"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


def append_messages(
    conn: sqlite3.Connection, conversation_id: int, messages: list[NewMessage], now: str
) -> None:
    (last,) = conn.execute(
        "SELECT coalesce(max(position), 0) FROM advisor_messages WHERE conversation_id = ?",
        (conversation_id,),
    ).fetchone()
    conn.executemany(
        "INSERT INTO advisor_messages (conversation_id, position, role, content, provider, model,"
        " input_tokens, output_tokens, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                conversation_id,
                int(last) + offset,
                item.message.role,
                _encode(item.message),
                item.provider,
                item.model,
                item.input_tokens,
                item.output_tokens,
                now,
            )
            for offset, item in enumerate(messages, start=1)
        ],
    )
    conn.execute(
        "UPDATE advisor_conversations SET updated_at = ? WHERE id = ?", (now, conversation_id)
    )
