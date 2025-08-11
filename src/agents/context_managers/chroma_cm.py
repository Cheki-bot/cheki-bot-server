from datetime import UTC, datetime, timedelta, timezone
from typing import Sequence

import tiktoken
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)

from src import ENV

from ...core.entities.context_manager import ContextManager
from .prompts import (
    CHAT_SYSTEM_PROMPT,
    VERIFICATION_TEMPLATE,
    VERIFICATION_TEMPLATE_DEFAULT,
)


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
        messages = await self.trim_context([*history.messages, query_message])
        system_messages = await self.build_system_messages(query)

        return [*system_messages, *messages]

    async def build_system_messages(self, query: str) -> Sequence[SystemMessage]:
        """Build a system message with contextual information from the vector database.

        Args:
            query: The user's query string to search for relevant documents.

        Returns:
            A SystemMessage containing the formatted context from the database.
        """
        retriver = self.vectorDB.as_retriever(search_kwargs={"k": 10})
        documents = await retriver.ainvoke(query)

        current_date = datetime.now(UTC)
        date_str = current_date.astimezone(
            timezone(offset=timedelta(hours=-4), name="America/La_Paz")
        ).strftime("%d de %B del %Y")

        system_prompt = SystemMessage(content=CHAT_SYSTEM_PROMPT.format(date=date_str))

        def format_document(document: Document):
            data = VERIFICATION_TEMPLATE_DEFAULT.copy()
            data.update({**document.metadata, "body": document.page_content})
            return VERIFICATION_TEMPLATE.format(**data)

        system_documents = [
            SystemMessage(content=format_document(document))
            for document in documents
            if document.metadata.get("type") == "verifications"
        ]

        return [system_prompt, *system_documents]

    async def trim_context(self, context) -> list[BaseMessage]:
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

        # Separar mensajes de sistema y usuario/asistente
        system_messages = []
        user_messages = []
        for msg in context:
            if isinstance(msg, SystemMessage):
                system_messages.append(msg)
            else:
                user_messages.append(msg)

        max_tokens_system = ENV.llm.context_length * 2 // 3
        max_tokens_user = ENV.llm.context_length // 3

        # Recortar mensajes de sistema
        trimmed_system = trim_messages(
            system_messages,
            token_counter=count_tokens_openai,
            max_tokens=max_tokens_system,
            strategy="first",
            end_on=("system", "tool"),
        )

        # Recortar mensajes de usuario/asistente
        trimmed_user = trim_messages(
            user_messages,
            token_counter=count_tokens_openai,
            max_tokens=max_tokens_user,
            strategy="last",
            start_on="human",
            end_on=("human", "tool"),
            include_system=True,
        )

        # Combinar los mensajes recortados
        return [*trimmed_system, *trimmed_user]
