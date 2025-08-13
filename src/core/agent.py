from abc import ABC
from typing import Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage

from src.core.conts import THINK_TAGS

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

    async def stream(self, query: str, history: Sequence[BaseMessage]):
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

    async def invoke(self, query: str, history: Sequence[BaseMessage]) -> str:
        """Process a query and generate a response using context-aware reasoning.

        Retrieves relevant context based on the query and conversation history,
        then uses the chat model to generate a response. Removes thinking tags
        from the final output to provide clean responses.

        Args:
            query (str): The user's query or question to process
            history (list[BaseMessage]): Conversation history with previous messages

        Returns:
            str: The generated response text with thinking tags removed

        Example:
            >>> agent = Agent()
            >>> response = await agent.invoke("What is AI?", [])
            >>> print(response)
            "AI stands for Artificial Intelligence..."
        """
        messages = await self.context_manager.retrieve_context(query, history)

        prev_system_msg = SystemMessage(
            content="Vamos a manejar mensajes para telegram y whatsapp "
            + "En las reglas generales ignora la regla 6 "
            + "Respeta al pie de la letra todas las reglas excepto la 6"
            + "no incluyas las etiquetas en la respuesta"
            + "si muestras enlaces deben ser sin markdown"
        )

        output = await self.chat_model.ainvoke([prev_system_msg, *messages])
        return str(output.content).replace(THINK_TAGS[0], "").replace(THINK_TAGS[1], "")
