"""Async SQLite provider using ``aiosqlite``.

This is the only place where SQL lives. ``save_exchange`` writes the user and
assistant messages in a single transaction, so a failed generation never leaves
a half-saved exchange (see spec, sections 6.2 and 8).
"""

from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

import aiosqlite

from src.ai_girlfriend.exc import StorageError
from src.ai_girlfriend.models.database import ChatSummary
from src.ai_girlfriend.models.llm import Message, Role

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_chat_created
    ON messages (chat_id, created_at);
"""


def _to_iso(value: datetime) -> str:
    return value.isoformat()


def _from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


class SQLiteProvider:
    """Low-level SQLite API implementing ``IDatabaseStorage``.

    - Creates tables and the database file on ``init``.
    - Performs SELECT/INSERT operations behind the async contract.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._connection: aiosqlite.Connection | None = None

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise StorageError("Database is not initialized; call init() first.")
        return self._connection

    async def init(self) -> None:
        """Open the connection and create the schema if missing."""
        try:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            await self._connection.execute("PRAGMA foreign_keys = ON;")
            await self._connection.executescript(_SCHEMA)
            await self._connection.commit()
        except aiosqlite.Error as exc:
            raise StorageError(f"Failed to initialize SQLite: {exc}") from exc

    async def create_chat(self) -> UUID:
        """Insert a new chat row and return its identifier."""
        chat_id = uuid4()
        now = _to_iso(datetime.now())
        try:
            await self.connection.execute(
                "INSERT INTO chats (id, created_at, updated_at) VALUES (?, ?, ?);",
                (str(chat_id), now, now),
            )
            await self.connection.commit()
        except aiosqlite.Error as exc:
            raise StorageError(f"Failed to create chat: {exc}") from exc
        return chat_id

    async def save_message(self, message: Message) -> UUID:
        """Persist a single message."""
        try:
            await self.connection.execute(
                """
                INSERT INTO messages (id, chat_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    str(message.id),
                    str(message.conversation_id),
                    message.role.value,
                    message.content,
                    _to_iso(message.created_at),
                ),
            )
            await self.connection.execute(
                "UPDATE chats SET updated_at = ? WHERE id = ?;",
                (_to_iso(message.created_at), str(message.conversation_id)),
            )
            await self.connection.commit()
        except aiosqlite.Error as exc:
            raise StorageError(f"Failed to save message: {exc}") from exc
        return message.id

    async def save_exchange(self, user_message: Message, bot_message: Message) -> None:
        """Save the user and assistant messages in a single transaction."""
        try:
            await self.connection.execute("BEGIN;")
            for message in (user_message, bot_message):
                await self.connection.execute(
                    """
                    INSERT INTO messages (id, chat_id, role, content, created_at)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        str(message.id),
                        str(message.conversation_id),
                        message.role.value,
                        message.content,
                        _to_iso(message.created_at),
                    ),
                )
            await self.connection.execute(
                "UPDATE chats SET updated_at = ? WHERE id = ?;",
                (_to_iso(bot_message.created_at), str(bot_message.conversation_id)),
            )
            await self.connection.commit()
        except aiosqlite.Error as exc:
            await self.connection.rollback()
            raise StorageError(f"Failed to save exchange: {exc}") from exc

    async def get_recent_messages(self, chat_id: UUID, limit: int) -> list[Message]:
        """Return up to ``limit`` most recent messages, oldest first."""
        try:
            cursor = await self.connection.execute(
                """
                SELECT id, chat_id, role, content, created_at
                FROM messages
                WHERE chat_id = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?;
                """,
                (str(chat_id), limit),
            )
            rows = await cursor.fetchall()
            await cursor.close()
        except aiosqlite.Error as exc:
            raise StorageError(f"Failed to read messages: {exc}") from exc

        messages = [
            Message(
                id=UUID(row["id"]),
                conversation_id=UUID(row["chat_id"]),
                role=Role(row["role"]),
                content=row["content"],
                created_at=_from_iso(row["created_at"]),
            )
            for row in rows
        ]
        return list(reversed(messages))

    async def list_chats(self, limit: int = 50) -> list[ChatSummary]:
        """Return recent conversations, most recently updated first."""
        try:
            cursor = await self.connection.execute(
                """
                SELECT
                    c.id AS id,
                    c.updated_at AS updated_at,
                    (SELECT COUNT(*) FROM messages m WHERE m.chat_id = c.id)
                        AS message_count,
                    (SELECT content FROM messages m
                        WHERE m.chat_id = c.id
                        ORDER BY m.created_at DESC, m.rowid DESC
                        LIMIT 1) AS preview
                FROM chats c
                ORDER BY c.updated_at DESC
                LIMIT ?;
                """,
                (limit,),
            )
            rows = await cursor.fetchall()
            await cursor.close()
        except aiosqlite.Error as exc:
            raise StorageError(f"Failed to list chats: {exc}") from exc

        return [
            ChatSummary(
                id=UUID(row["id"]),
                updated_at=_from_iso(row["updated_at"]),
                message_count=row["message_count"] or 0,
                preview=(row["preview"] or "")[:120],
            )
            for row in rows
        ]

    async def get_messages(self, chat_id: UUID) -> list[Message]:
        """Return the full message history of a chat, oldest first."""
        try:
            cursor = await self.connection.execute(
                """
                SELECT id, chat_id, role, content, created_at
                FROM messages
                WHERE chat_id = ?
                ORDER BY created_at ASC, rowid ASC;
                """,
                (str(chat_id),),
            )
            rows = await cursor.fetchall()
            await cursor.close()
        except aiosqlite.Error as exc:
            raise StorageError(f"Failed to read chat messages: {exc}") from exc

        return [
            Message(
                id=UUID(row["id"]),
                conversation_id=UUID(row["chat_id"]),
                role=Role(row["role"]),
                content=row["content"],
                created_at=_from_iso(row["created_at"]),
            )
            for row in rows
        ]

    async def close(self) -> None:
        """Close the underlying connection."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None


__all__ = ["SQLiteProvider"]
