from src.ai_girlfriend.database.database_controller import DatabaseController
from uuid import UUID
from src.ai_girlfriend.models.llm import Message
from src.ai_girlfriend.models.context import ContextBundle, IContextProvider


class MemoryManager:
    def __init__(self, database: DatabaseController, context_provider: IContextProvider ):
        self.database = database
        self.context_provider = context_provider

    async def build_context(self, chat_id: UUID, user_message: Message ) -> ContextBundle:
        ...

    async def record_exchange(self, user_message: Message, bot_message: Message):
        ...
