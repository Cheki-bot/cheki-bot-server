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
from src.consts import DocType

from ...core.entities.context_manager import ContextManager
from .prompts import (
    CALENDAR_EVENT_PROMPT,
    CALENDAR_METADATA_PROMPT,
    CANDIDATES_PROMPT,
    CHAT_SYSTEM_PROMPT,
    GOV_PROGRAM_PROMPT,
    NOT_FOUND_PROMPT,
    VERIFICATION_PROMPT,
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
        messages = await self.trim_context([*history, query_message])

        user_message = filter(lambda msg: isinstance(msg, HumanMessage), messages)

        system_messages = await self.build_system_messages(list(user_message)[-3:])

        return [*system_messages, *messages]

    def __format_verification(self, documents: list[Document]):
        content = []
        for document in documents:
            data = VERIFICATION_TEMPLATE_DEFAULT.copy()
            data.update({**document.metadata, "body": document.page_content})
            content.append(VERIFICATION_TEMPLATE.format(**data))
        return VERIFICATION_PROMPT.format(content="\n".join(content))

    def __format_content(self, documents: list[Document]):
        content = []
        for document in documents:
            content.append(document.page_content)
        return "\n\n".join(content)

    async def build_system_messages(self, queries: Sequence[BaseMessage]) -> Sequence[SystemMessage]:
        """Build a system message with contextual information from the vector database.

        Args:
            query: The user's query string to search for relevant documents.

        Returns:
            A SystemMessage containing the formatted context from the database.
        """

        score_retriever = self.vectorDB.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.1, "k": 10},
        )
        relevant_docs: list[Document] = []
        complete_context = ""
        for query in queries[::-1]:
            query_str = str(query.content).lower()
            relevant_docs += score_retriever.invoke(query_str)
            complete_context += f"{query_str} "
        relevant_docs += score_retriever.invoke(complete_context.strip())

        content_type = {}
        for doc in relevant_docs:
            _type = doc.metadata.get("type")
            if _type not in content_type:
                content_type[_type] = 0
            content_type[_type] += 1

        best_match = max(content_type, key=lambda key: content_type.get(key, 0))
        retriver = self.vectorDB.as_retriever(search_kwargs={"k": 20, "filter": {"type": best_match}})
        documents: list[Document] = await retriver.ainvoke(complete_context)

        current_date = datetime.now(UTC)
        date_str = current_date.astimezone(timezone(offset=timedelta(hours=-4), name="America/La_Paz")).strftime(
            "%d de %B del %Y"
        )

        system_prompts = [SystemMessage(content=CHAT_SYSTEM_PROMPT.format(date=date_str))]

        match best_match:
            case DocType.VERIFICATIONS.value:
                content = self.__format_verification(documents)
                system_prompts.append(SystemMessage(content))

            case DocType.GOV_PROGRAMS.value:
                content = self.__format_content(documents)
                content = GOV_PROGRAM_PROMPT.format(content=content)
                system_prompts.append(SystemMessage(content))

            case DocType.CALENDAR_META.value:
                content = self.__format_content(documents)
                content = CALENDAR_METADATA_PROMPT.format(content=content)
                system_prompts.append(SystemMessage(content))

            case DocType.CALENDAR.value:
                content = self.__format_content(documents)
                content = CALENDAR_EVENT_PROMPT.format(content=content)
                system_prompts.append(SystemMessage(content))

            case DocType.CANDIDATES.value:
                content = self.__format_content(documents)
                content = CANDIDATES_PROMPT.format(content=content)
                system_prompts.append(SystemMessage(content))

            case _:
                system_prompts.append(SystemMessage(NOT_FOUND_PROMPT))

        return system_prompts

    async def trim_context(self, context) -> list[BaseMessage]:
        """Trim messages to fit within token limits using OpenAI token counting.

        Args:
            context: List of message objects to trim.

        Returns:
            The trimmed list of messages that fit within the token limit.
        """
        encoding = tiktoken.encoding_for_model("text-embedding-3-small")

        def count_tokens_openai(message_list: list[BaseMessage]):
            return sum(len(encoding.encode(str(msg.content))) for msg in message_list if hasattr(msg, "content"))

        trimmed_user = trim_messages(
            context,
            token_counter=count_tokens_openai,
            max_tokens=ENV.llm.context_length,
            strategy="last",
            start_on="human",
            end_on=("human", "tool"),
            include_system=True,
        )

        return trimmed_user
