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
    CALENDAR_EVENT_TEMPLATE,
    CALENDAR_METADATA_TEMPLATE,
    CHAT_SYSTEM_PROMPT,
    GOV_PROGRAM_TEMPLATE,
    GOV_PROGRAM_TEMPLATE_DEFAULT,
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

    def __format_verification(self, document: Document):
        data = VERIFICATION_TEMPLATE_DEFAULT.copy()
        data.update({**document.metadata, "body": document.page_content})
        return VERIFICATION_TEMPLATE.format(**data)

    def __format_gov_program(self, document: Document):
        data = GOV_PROGRAM_TEMPLATE_DEFAULT.copy()
        data.update({**document.metadata, "content": document.page_content})
        return GOV_PROGRAM_TEMPLATE.format(**data)

    async def build_system_messages(
        self, queries: Sequence[BaseMessage]
    ) -> Sequence[SystemMessage]:
        """Build a system message with contextual information from the vector database.

        Args:
            query: The user's query string to search for relevant documents.

        Returns:
            A SystemMessage containing the formatted context from the database.
        """

        k = 20
        documents: list[Document] = []
        contents = []
        for query in queries[::-1]:
            k = k // 3 if k >= 3 else k
            retriver = self.vectorDB.as_retriever(search_kwargs={"k": k * 2})
            docs = await retriver.ainvoke(str(query.content))
            contents.append(query.content)
            documents.extend(docs)
        retriver = self.vectorDB.as_retriever(
            search_kwargs={"k": k},
        )
        extra_docs = await retriver.ainvoke(" ".join(contents))
        documents.extend(extra_docs)

        current_date = datetime.now(UTC)
        date_str = current_date.astimezone(
            timezone(offset=timedelta(hours=-4), name="America/La_Paz")
        ).strftime("%d de %B del %Y")

        contents = []

        for document in documents:
            match document.metadata.get("type"):
                case DocType.VERIFICATIONS.value:
                    content = self.__format_verification(document)

                    contents.append(content)
                case DocType.GOV_PROGRAMS.value:
                    content = self.__format_gov_program(document)
                    contents.append(content)

                case DocType.CALENDAR_META.value:
                    content = CALENDAR_METADATA_TEMPLATE.format(
                        content=document.page_content
                    )
                    contents.append(content)

                case DocType.CALENDAR.value:
                    content = CALENDAR_EVENT_TEMPLATE.format(
                        content=document.page_content
                    )
                    contents.append(content)

        total_content = "".join(contents)

        system_prompt = SystemMessage(
            content=CHAT_SYSTEM_PROMPT.format(
                date=date_str,
                content=total_content,
            )
        )

        return [system_prompt]

    async def trim_context(self, context) -> list[BaseMessage]:
        """Trim messages to fit within token limits using OpenAI token counting.

        Args:
            context: List of message objects to trim.

        Returns:
            The trimmed list of messages that fit within the token limit.
        """
        encoding = tiktoken.encoding_for_model("gpt-4.1-nano")

        def count_tokens_openai(message_list: list[BaseMessage]):
            return sum(
                len(encoding.encode(str(msg.content)))
                for msg in message_list
                if hasattr(msg, "content")
            )

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
