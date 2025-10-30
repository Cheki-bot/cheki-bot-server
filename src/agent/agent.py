from typing import Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from src.agent.commands import AsyncClassifyTopic, AsyncRAGRetrieve, BuildTopicContext
from src.agent.context_managers.prompts import CHAT_RESPONSE_PROMPT
from src.agent.schemas import AgentResponseChunk, Platform
from src.core.tools import get_bo_current_datetime_str


class AsyncAgent:
    """Abstract base class for all agents in the system.

    This class provides the foundational structure for agents that interact with
    language models and manage context through a context manager. It defines the
    interface for streaming responses based on queries and chat history.

    Attributes:
        chat_model (BaseChatModel): The language model used for generating responses.
        context_manager (ContextManager): Manager for retrieving and handling context.
    """

    def __init__(
        self,
        chat_model: BaseChatModel,
        classify_topic: AsyncClassifyTopic,
        rag_retrieve: AsyncRAGRetrieve,
        build_topic_context: BuildTopicContext,
    ):
        """Initialize the AsyncAgent with a chat model and context manager.

        Args:
            chat_model (BaseChatModel): The language model to use for responses.
            context_manager (ContextManager): The manager for handling context retrieval.
        """
        self.chat_model = chat_model
        self.classify_topic = classify_topic
        self.rag_retrieve = rag_retrieve
        self.build_topic_context = build_topic_context

    async def stream(self, messages: Sequence[BaseMessage], platform: Platform = Platform.WEB):
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
        try:
            yield AgentResponseChunk(content="Analizando consulta ...")

            topic_selections = await self.classify_topic(messages)

            yield AgentResponseChunk(content="Obteniendo información...")

            context: str = await self.build_topic_context(topic_selections)

            yield AgentResponseChunk(content="Procesando información...")

            prompt = CHAT_RESPONSE_PROMPT.format(
                content=context,
                platform="Markdown" if platform is Platform.WEB else platform.value,
                date=get_bo_current_datetime_str(),
            )

            yield AgentResponseChunk(content="Generando respuesta...")

            context_messages = [
                SystemMessage(content=prompt),
                SystemMessage(content=topic_selections[0].description),
                HumanMessage(content=topic_selections[0].user_query),
            ]

            async for chunk in self.chat_model.astream(context_messages):
                yield AgentResponseChunk(content=str(chunk.content), type="text")

            yield AgentResponseChunk(content="", type="text", done=True)

        except Exception as e:
            yield AgentResponseChunk(content=f"Error: {str(e)}", type="error", done=True)
            raise e

    async def invoke(
        self, messages: Sequence[BaseMessage], platform: Platform = Platform.WEB
    ) -> str:
        """Process a query and generate a response using context-aware reasoning.

        Retrieves relevant context based on the query and conversation history,
        then uses the chat model to generate a response. Removes thinking tags
        from the final output to provide clean responses.

        Args:
            query (str): The user's query or question to process.
            history (list[BaseMessage]): Conversation history with previous messages

        Returns:
            str: The generated response text with thinking tags removed

        Example:
            >>> agent = AsyncAgent()
            >>> response = await agent.invoke("What is AI?", [])
            >>>
            "AI stands for Artificial Intelligence..."
        """
        topic_selections = await self.classify_topic(messages)

        context = await self.build_topic_context(topic_selections)

        prompt = CHAT_RESPONSE_PROMPT.format(
            content=context,
            platform="Markdown" if platform is Platform.WEB else platform.value,
            date=get_bo_current_datetime_str(),
        )
        context_messages = [
            SystemMessage(content=prompt),
            SystemMessage(content=topic_selections[0].description),
            HumanMessage(content=topic_selections[0].user_query),
        ]
        output = await self.chat_model.ainvoke(context_messages)
        return str(output.content)
