import tiktoken
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)

from src import ENV

from ...core.entities.context_manager import ContextManager
from .prompts import CHAT_SYSTEM_PROMPT


class ChromaContextManager(ContextManager):
    """A context manager that retrieves and trims context from a Chroma vector database.

    This class handles the retrieval of relevant context from a Chroma vector database
    based on user queries and manages the trimming of messages to fit within token limits.

    Attributes:
        vectorDB: The Chroma vector database instance for storing and retrieving embeddings.
    """

    def __init__(self, emb_model: Embeddings) -> None:
        """Initialize the ChromaContextManager with an embedding model.

        Args:
            emb_model: The embedding model to use for vectorization.
        """
        self.vectorDB = Chroma(
            persist_directory=ENV.chroma.persist_directory,
            embedding_function=emb_model,
        )

    async def retrieve_context(self, query, history):
        """Retrieve context from the vector database and build a system message.

        Args:
            query: The user's query string.
            history: The conversation history.

        Returns:
            The trimmed context messages including system message.
        """
        query_message = HumanMessage(content=query)
        messages = history.messages + [query_message]
        context = len(history.messages) and history.messages[-1].text() + query or query
        system_message = await self.build_system_message(context)
        return await self.trim_context([system_message] + messages)

    async def build_system_message(self, query: str):
        """Build a system message with contextual information from the vector database.

        Args:
            query: The user's query string to search for relevant documents.

        Returns:
            A SystemMessage containing the formatted context from the database.
        """
        retriver = self.vectorDB.as_retriever(search_kwargs={"k": 10})
        docs = await retriver.ainvoke(query)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        chat_system_prompt = CHAT_SYSTEM_PROMPT.format(context=context_text)
        return SystemMessage(content=chat_system_prompt)

    async def trim_context(self, context):
        """Trim messages to fit within token limits using OpenAI token counting.

        Args:
            context: List of message objects to trim.

        Returns:
            The trimmed list of messages that fit within the token limit.
        """
        encoding = tiktoken.encoding_for_model("gpt-4-nano")

        def count_tokens_openai(message_list: list[BaseMessage]):
            return sum(
                len(encoding.encode(str(msg.content)))
                for msg in message_list
                if hasattr(msg, "content")
            )

        return trim_messages(
            context,
            token_counter=count_tokens_openai,
            max_tokens=ENV.llm.max_tokens,
            strategy="last",
            start_on="human",
            end_on=("human", "tool"),
            include_system=True,
        )
