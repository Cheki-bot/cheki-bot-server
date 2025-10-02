from typing import Literal, Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage

from src.agent.commands import AsyncClassifyTopic, AsyncRAGRetrieve, AsyncSelectPrompt
from src.agent.schemas import AgentResponseChunk


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
        select_prompt: AsyncSelectPrompt,
    ):
        """Initialize the AsyncAgent with a chat model and context manager.

        Args:
            chat_model (BaseChatModel): The language model to use for responses.
            context_manager (ContextManager): The manager for handling context retrieval.
        """
        self.chat_model = chat_model
        self.classify_topic = classify_topic
        self.rag_retrieve = rag_retrieve
        self.select_prompt = select_prompt

    async def stream(self, messages: Sequence[BaseMessage]):
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
            topic_selection = await self.classify_topic(messages)
            yield AgentResponseChunk(content="Obteniendo información...")
            documents = await self.rag_retrieve(topic_selection)
            yield AgentResponseChunk(content="Procesando información...")
            prompt = await self.select_prompt(topic_selection)
            yield AgentResponseChunk(content="Generando respuesta...")
            data = ""
            for document in documents:
                data += f"{document.page_content}\n\n"

            system_prompt = prompt.format(data=data)
            messages = [SystemMessage(content=system_prompt), *messages]

            async for chunk in self.chat_model.astream(messages):
                yield AgentResponseChunk(content=str(chunk.content), type="text")

            yield AgentResponseChunk(content="", type="text", done=True)

        except Exception as e:
            yield AgentResponseChunk(content=f"Error: {str(e)}", type="error", done=True)

    async def invoke(
        self,
        messages: Sequence[BaseMessage],
        platform: Literal["telegram", "whatsapp", "web"] = "web",
    ) -> str:
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
            >>> agent = AsyncAgent()
            >>> response = await agent.invoke("What is AI?", [])
            >>> print(response)
            "AI stands for Artificial Intelligence..."
        """

        topic_selection = await self.classify_topic(messages)
        documents = await self.rag_retrieve(topic_selection)
        prompt = await self.select_prompt(topic_selection)
        data = ""
        for document in documents:
            data += f"{document.page_content}\n\n"

        system_prompt = prompt.format(data=data)
        messages = [SystemMessage(content=system_prompt), *messages]

        output = await self.chat_model.ainvoke(messages)
        return str(output.content)
