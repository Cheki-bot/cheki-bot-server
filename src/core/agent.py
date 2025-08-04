from abc import ABC

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.language_models.chat_models import BaseChatModel

from .conts import THINK_TAGS
from .entities.context_manager import ContextManager


class Agent(ABC):
    """Abstract base class for all agents in the system.

    This class provides the foundational structure for agents that interact with
    language models and manage context through a context manager. It defines the
    interface for streaming responses based on queries and chat history.

    Attributes:
        chat_model (BaseChatModel): The language model used for generating responses.
        context_manager (ContextManager): Manager for retrieving and handling context.
    """

    def __init__(self, chat_model: BaseChatModel, context_manager: ContextManager):
        """Initialize the Agent with a chat model and context manager.

        Args:
            chat_model (BaseChatModel): The language model to use for responses.
            context_manager (ContextManager): The manager for handling context retrieval.
        """
        self.chat_model = chat_model
        self.context_manager = context_manager

    async def stream(self, query: str, history: BaseChatMessageHistory):
        """Stream response chunks for a given query and chat history.

        This method retrieves relevant context using the context manager,
        then streams chunks from the chat model while filtering out
        think tags from the output.

        Args:
            query (str): The user's query to process.
            history (BaseChatMessageHistory): The chat history for context.

        Yields:
            str: Response chunks as they become available.
        """
        messages = await self.context_manager.retrieve_context(query, history)
        async for chunk in self.chat_model.astream(messages):
            output = str(chunk.content)
            output = output.replace(THINK_TAGS[0], "").replace(THINK_TAGS[1], "")
            yield output
