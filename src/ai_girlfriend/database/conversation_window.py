"""Default context provider: a window of the most recent messages.

Returns the last ``window`` messages of a conversation as the context bundle.
No memories are retrieved here; RAG/long-term memory plug in later through the
same ``IContextProvider`` contract (see spec, section 9).
"""

from uuid import UUID

from src.ai_girlfriend.database.database_controller import DatabaseController
from src.ai_girlfriend.models.context import ContextBundle


class ConversationWindowProvider:
    """Builds context from the recent dialogue history only."""

    def __init__(self, database: DatabaseController, window: int = 20):
        self.database = database
        self.window = window

    async def build_context(self, query: str, chat_id: UUID) -> ContextBundle:
        """Return the recent messages of the chat as the context."""
        messages = await self.database.get_recent_messages(chat_id, self.window)
        return ContextBundle(messages=messages, memories=[])


__all__ = ["ConversationWindowProvider"]
