from abc import ABC

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.language_models.chat_models import BaseChatModel

from .entities.context_manager import ContextManager


class Agent(ABC):
    def __init__(self, chat_model: BaseChatModel, context_manager: ContextManager):
        self.chat_model = chat_model
        self.context_manager = context_manager

    async def stream(self, query: str, history: BaseChatMessageHistory):
        messages = await self.context_manager.retrieve_context(query, history)
        async for chunk in self.chat_model.astream(messages):
            output = str(chunk.content)
            if output in ["<think>", "</think>"]:
                yield ""
            yield output
